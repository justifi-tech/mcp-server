"""
MCP (Model Context Protocol) Adapter for JustiFi Tools

This adapter wraps framework-agnostic JustiFi tools with MCP protocol
handling, converting raw tool results to MCP TextContent format.
"""

import json
from typing import Any, cast

from mcp.server import Server
from mcp.types import TextContent, Tool

from ..config import JustiFiConfig
from ..core import JustiFiClient
from ..tools import AVAILABLE_TOOLS, TOOL_SCHEMAS
from ..tools.base import ToolError, ValidationError


class MCPAdapter:
    """Adapter for integrating JustiFi tools with MCP protocol."""

    def __init__(self, config: JustiFiConfig):
        self.config = config
        # Config validation ensures these are not None
        assert config.client_id is not None, "client_id is required"
        assert config.client_secret is not None, "client_secret is required"
        self.client = JustiFiClient(config.client_id, config.client_secret)

    def get_enabled_tool_schemas(self) -> list[Tool]:
        """Get MCP Tool schemas for enabled tools."""
        enabled_tools = self.config.get_enabled_tools()
        schemas: list[Tool] = []

        for tool_name in enabled_tools:
            if tool_name in TOOL_SCHEMAS:
                schema_data = TOOL_SCHEMAS[tool_name]
                tool = Tool(
                    name=str(schema_data["name"]),
                    description=str(schema_data["description"]),
                    inputSchema=cast(dict[str, Any], schema_data["parameters"]),
                )
                schemas.append(tool)

        return schemas

    async def call_tool(
        self, name: str, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """Call a tool and return MCP-formatted results."""
        # Check if tool is enabled
        if not self.config.is_tool_enabled(name):
            available_tools = list(self.config.get_enabled_tools())
            return [
                TextContent(
                    type="text",
                    text=f"❌ Tool '{name}' is not enabled in the current configuration.\n\n"
                    f"Available tools: {', '.join(available_tools) if available_tools else 'None'}\n\n"
                    f"To enable tools, set the JUSTIFI_ENABLED_TOOLS environment variable.",
                )
            ]

        # Check if tool exists
        if name not in AVAILABLE_TOOLS:
            return [
                TextContent(
                    type="text",
                    text=f"❌ Tool '{name}' is not enabled in the current configuration.\n\n"
                    f"Available tools: {', '.join(self.config.get_enabled_tools())}",
                )
            ]

        try:
            # Get the tool function
            tool_func = AVAILABLE_TOOLS[name]

            # Call the tool with client and arguments
            result = await tool_func(self.client, **arguments)

            # Format success response
            return [
                TextContent(
                    type="text",
                    text=f"✅ Success: {name}\n\n{json.dumps(result, indent=2)}",
                )
            ]

        except ValidationError as e:
            # Handle validation errors with helpful messages
            error_msg = f"❌ Input Error: {e.message}"
            if e.field:
                error_msg += f"\nField: {e.field}"
            if e.value is not None:
                error_msg += f"\nProvided value: {e.value}"
            error_msg += "\nError Type: ValidationError"

            return [TextContent(type="text", text=error_msg)]

        except ToolError as e:
            # Handle wrapped tool errors
            return [TextContent(type="text", text=f"❌ {e.error_type}: {e.message}")]

        except Exception as e:
            # Handle unexpected errors
            return [
                TextContent(
                    type="text",
                    text=f"❌ Unexpected Error: {type(e).__name__}: {str(e)}",
                )
            ]

    def create_mcp_server(self, server_name: str = "justifi-mcp-server") -> Server:
        """Create and configure an MCP server with JustiFi tools."""
        server: Server = Server(server_name)

        @server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available JustiFi tools based on configuration."""
            return self.get_enabled_tool_schemas()

        @server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict[str, Any]
        ) -> list[TextContent]:
            """Handle tool execution requests."""
            return await self.call_tool(name, arguments)

        return server
