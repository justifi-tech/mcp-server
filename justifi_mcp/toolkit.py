"""JustiFi Agent Toolkit

Main toolkit class providing Stripe-like configuration-driven tool management.
Supports multiple AI frameworks with consistent tool interfaces.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from mcp.server import Server
from mcp.types import TextContent, Tool

from .config import JustiFiConfig
from .core import JustiFiClient
from .payouts import (
    get_payout_status,
    get_recent_payouts,
    list_payouts,
    retrieve_payout,
)


class JustiFiToolkit:
    """JustiFi Agent Toolkit - Configuration-driven payment integration.

    Provides Stripe-like configuration for tool selection and context management.
    Supports multiple AI frameworks with consistent interfaces.

    Example:
        ```python
        from justifi_mcp import JustiFiToolkit

        # Basic usage with environment variables
        toolkit = JustiFiToolkit()

        # Advanced configuration
        toolkit = JustiFiToolkit(
            client_id="your_client_id",
            client_secret="your_client_secret",
            configuration={
                "tools": {
                    "payouts": {
                        "retrieve": {"enabled": True},
                        "list": {"enabled": True},
                        "status": {"enabled": True},
                        "recent": {"enabled": False}  # Disable for this environment
                    }
                },
                "context": {
                    "environment": "production",
                    "timeout": 15,
                    "rate_limit": "premium"
                }
            }
        )

        # Get MCP server with only enabled tools
        mcp_server = toolkit.get_mcp_server()
        ```

    """

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        configuration: dict[str, Any] | None = None,
        config: JustiFiConfig | None = None,
    ):
        """Initialize JustiFi toolkit.

        Args:
            client_id: JustiFi client ID (or from JUSTIFI_CLIENT_ID env var)
            client_secret: JustiFi client secret (or from JUSTIFI_CLIENT_SECRET env var)
            configuration: Dictionary configuration (Stripe-like format)
            config: Pre-built JustiFiConfig instance (takes precedence)

        """
        if config:
            self.config = config
        else:
            # Build config from parameters
            config_data = {}
            if client_id:
                config_data["client_id"] = client_id
            if client_secret:
                config_data["client_secret"] = client_secret
            if configuration:
                config_data.update(configuration)

            self.config = JustiFiConfig(**config_data)

        # Initialize client with configuration
        self.client = JustiFiClient(
            client_id=self.config.client_id, client_secret=self.config.client_secret
        )

        # Tool function mapping
        self._tool_functions: dict[str, Callable] = {
            "retrieve_payout": retrieve_payout,
            "list_payouts": list_payouts,
            "get_payout_status": get_payout_status,
            "get_recent_payouts": get_recent_payouts,
        }

    def get_enabled_tools(self) -> dict[str, Any]:
        """Get dictionary of enabled tools and their functions."""
        enabled_tools = {}
        enabled_configs = self.config.get_enabled_tools()

        for tool_name in enabled_configs:
            if tool_name in self._tool_functions:
                enabled_tools[tool_name] = self._tool_functions[tool_name]

        return enabled_tools

    def get_tool_schemas(self) -> list[Tool]:
        """Get MCP tool schemas for enabled tools."""
        enabled_tools = self.config.get_enabled_tools()
        schemas = []

        # Tool schema definitions
        tool_schemas = {
            "retrieve_payout": Tool(
                name="retrieve_payout",
                description="Retrieve details of a specific payout by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "payout_id": {
                            "type": "string",
                            "description": (
                                "The ID of the payout to retrieve "
                                "(e.g., 'po_ABC123XYZ')"
                            ),
                        }
                    },
                    "required": ["payout_id"],
                },
            ),
            "list_payouts": Tool(
                name="list_payouts",
                description="List payouts with cursor-based pagination",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of payouts to return (default: 25, max: 100)",
                            "default": 25,
                            "minimum": 1,
                            "maximum": 100,
                        },
                        "after_cursor": {
                            "type": "string",
                            "description": "Cursor for pagination (get payouts after this cursor)",
                            "optional": True,
                        },
                        "before_cursor": {
                            "type": "string",
                            "description": "Cursor for pagination (get payouts before this cursor)",
                            "optional": True,
                        },
                    },
                    "required": [],
                },
            ),
            "get_payout_status": Tool(
                name="get_payout_status",
                description="Get the status of a specific payout (returns just the status string)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "payout_id": {
                            "type": "string",
                            "description": "The ID of the payout to check status for (e.g., 'po_ABC123XYZ')",
                        }
                    },
                    "required": ["payout_id"],
                },
            ),
            "get_recent_payouts": Tool(
                name="get_recent_payouts",
                description="Get the most recent payouts (optimized for recency)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of recent payouts to return (default: 10, max: 25)",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 25,
                        }
                    },
                    "required": [],
                },
            ),
        }

        # Return only enabled tool schemas
        for tool_name in enabled_tools:
            if tool_name in tool_schemas:
                schemas.append(tool_schemas[tool_name])

        return schemas

    async def call_tool(
        self, name: str, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """Call a tool with the given arguments.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            List of TextContent responses

        Raises:
            ValueError: If tool is not enabled or doesn't exist

        """
        # Check if tool is enabled
        if not self.config.is_tool_enabled(name):
            available_tools = list(self.config.get_enabled_tools().keys())
            return [
                TextContent(
                    type="text",
                    text=f"Tool '{name}' is not enabled. Available tools: {available_tools}",
                )
            ]

        # Get tool function
        if name not in self._tool_functions:
            return [
                TextContent(
                    type="text",
                    text=f"Unknown tool: {name}",
                )
            ]

        try:
            # Call the tool function with client and arguments
            tool_func = self._tool_functions[name]
            result = await tool_func(client=self.client, **arguments)

            # Format the response
            response_text = json.dumps(result, indent=2)
            return [TextContent(type="text", text=response_text)]

        except Exception as e:
            error_msg = f"Error calling {name}: {type(e).__name__}: {str(e)}"
            return [TextContent(type="text", text=error_msg)]

    def get_mcp_server(self, server_name: str = "justifi-toolkit-mcp-server") -> Server:
        """Get an MCP server configured with enabled tools.

        Args:
            server_name: Name for the MCP server

        Returns:
            Configured MCP Server instance

        """
        server: Server = Server(server_name)

        # Register list_tools handler
        @server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            return self.get_tool_schemas()

        # Register call_tool handler
        @server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
            return await self.call_tool(name, arguments)

        # Register empty handlers for resources and prompts
        @server.list_resources()
        async def handle_list_resources():
            return []

        @server.list_prompts()
        async def handle_list_prompts():
            return []

        return server

    def get_configuration_summary(self) -> dict[str, Any]:
        """Get a summary of the current configuration.

        Returns:
            Dictionary with configuration details

        """
        enabled_tools = self.config.get_enabled_tools()

        return {
            "environment": self.config.context.environment,
            "base_url": self.config.get_effective_base_url(),
            "timeout": self.config.context.timeout,
            "rate_limit": self.config.context.rate_limit,
            "enabled_tools": list(enabled_tools.keys()),
            "total_tools": len(enabled_tools),
            "account_id": self.config.context.account_id,
        }

    # Future: Framework-specific methods for Phase 3

    def get_langchain_tools(self) -> list[Any]:
        """Get LangChain-compatible tools.

        Returns:
            List of LangChain BaseTool instances

        """
        try:
            from langchain_core.tools import StructuredTool
            from pydantic import BaseModel, Field
        except ImportError as err:
            raise ImportError(
                "LangChain is required for this functionality. "
                "Install it with: pip install langchain-core"
            ) from err

        enabled_tools = self.get_enabled_tools()
        langchain_tools = []

        for tool_name, _tool_config in enabled_tools.items():
            # Get the tool function and create LangChain tool
            tool_func = self._tool_functions[tool_name]

            if tool_name == "retrieve_payout":

                class RetrievePayoutInput(BaseModel):
                    payout_id: str = Field(
                        description="The ID of the payout to retrieve (e.g., 'po_ABC123XYZ')"
                    )

                # Create wrapper with proper closure capture
                def make_retrieve_wrapper(func):
                    async def retrieve_payout_wrapper(**kwargs):
                        return await func(client=self.client, **kwargs)

                    return retrieve_payout_wrapper

                retrieve_wrapper = make_retrieve_wrapper(tool_func)

                langchain_tool = StructuredTool.from_function(
                    func=None,
                    coroutine=retrieve_wrapper,
                    name="retrieve_payout",
                    description="Retrieve details of a specific payout by ID",
                    args_schema=RetrievePayoutInput,
                )

            elif tool_name == "list_payouts":

                class ListPayoutsInput(BaseModel):
                    limit: int = Field(
                        default=25,
                        description="Number of payouts to return (default: 25, max: 100)",
                        ge=1,
                        le=100,
                    )
                    after_cursor: str | None = Field(
                        default=None,
                        description="Cursor for pagination (get payouts after this cursor)",
                    )
                    before_cursor: str | None = Field(
                        default=None,
                        description="Cursor for pagination (get payouts before this cursor)",
                    )

                # Create wrapper with proper closure capture
                def make_list_wrapper(func):
                    async def list_payouts_wrapper(**kwargs):
                        return await func(client=self.client, **kwargs)

                    return list_payouts_wrapper

                list_wrapper = make_list_wrapper(tool_func)

                langchain_tool = StructuredTool.from_function(
                    func=None,
                    coroutine=list_wrapper,
                    name="list_payouts",
                    description="List payouts with cursor-based pagination",
                    args_schema=ListPayoutsInput,
                )

            elif tool_name == "get_payout_status":

                class GetPayoutStatusInput(BaseModel):
                    payout_id: str = Field(
                        description="The ID of the payout to check status for (e.g., 'po_ABC123XYZ')"
                    )

                # Create wrapper with proper closure capture
                def make_status_wrapper(func):
                    async def get_payout_status_wrapper(**kwargs):
                        return await func(client=self.client, **kwargs)

                    return get_payout_status_wrapper

                status_wrapper = make_status_wrapper(tool_func)

                langchain_tool = StructuredTool.from_function(
                    func=None,
                    coroutine=status_wrapper,
                    name="get_payout_status",
                    description="Get the status of a specific payout (returns just the status string)",
                    args_schema=GetPayoutStatusInput,
                )

            elif tool_name == "get_recent_payouts":

                class GetRecentPayoutsInput(BaseModel):
                    limit: int = Field(
                        default=10,
                        description="Number of recent payouts to return (default: 10, max: 25)",
                        ge=1,
                        le=25,
                    )

                # Create wrapper with proper closure capture
                def make_recent_wrapper(func):
                    async def get_recent_payouts_wrapper(**kwargs):
                        return await func(client=self.client, **kwargs)

                    return get_recent_payouts_wrapper

                recent_wrapper = make_recent_wrapper(tool_func)

                langchain_tool = StructuredTool.from_function(
                    func=None,
                    coroutine=recent_wrapper,
                    name="get_recent_payouts",
                    description="Get the most recent payouts (optimized for recency)",
                    args_schema=GetRecentPayoutsInput,
                )

            else:
                continue  # Skip unknown tools

            langchain_tools.append(langchain_tool)

        return langchain_tools

    def get_openai_functions(self) -> list[dict[str, Any]]:
        """Get OpenAI function definitions (Phase 3).

        Returns:
            List of OpenAI function definitions

        """
        # TODO: Implement in Phase 3
        raise NotImplementedError("OpenAI integration coming in Phase 3")

    def get_direct_api(self) -> dict[str, Any]:
        """Get direct API interface (Phase 3).

        Returns:
            Dictionary of callable functions

        """
        # TODO: Implement in Phase 3
        raise NotImplementedError("Direct API coming in Phase 3")
