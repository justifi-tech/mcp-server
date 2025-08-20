"""
LangChain Adapter for JustiFi Tools

This adapter wraps framework-agnostic JustiFi tools with LangChain-specific
handling, converting raw tool results to LangChain StructuredTool format.

All tools are async-only and designed for modern LangChain patterns.
Use with `await tool.arun(args)` or LangChain agents that support async execution.
"""

from __future__ import annotations

import json
from typing import Any

from ..config import JustiFiConfig
from ..core import JustiFiClient
from ..tools.base import ToolError, ValidationError
from .schema_generator import generate_langchain_schema


class LangChainAdapter:
    """Adapter for integrating JustiFi tools with LangChain framework."""

    def __init__(self, config: JustiFiConfig):
        self.config = config
        # Config validation ensures these are not None
        assert config.client_id is not None, "client_id is required"
        assert config.client_secret is not None, "client_secret is required"
        self.client = JustiFiClient(config.client_id, config.client_secret)

    def get_langchain_tools(self) -> list[Any]:
        """Get LangChain-compatible tools.

        Returns:
            List of LangChain StructuredTool instances

        Raises:
            ImportError: If LangChain is not installed
        """
        try:
            # Import check only - actual imports happen in _create_langchain_tool
            import langchain_core.tools  # noqa: F401
            import pydantic  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "LangChain is required for LangChainAdapter. "
                "Install with: pip install langchain-core"
            ) from e

        enabled_tools = self.config.get_enabled_tools()
        langchain_tools = []

        for tool_name in enabled_tools:
            # Create LangChain tool based on tool type
            langchain_tool = self._create_langchain_tool(tool_name)
            if langchain_tool:
                langchain_tools.append(langchain_tool)

        return langchain_tools

    def _create_langchain_tool(self, tool_name: str) -> Any:
        """Create a LangChain StructuredTool for a specific tool."""
        try:
            from langchain_core.tools import StructuredTool
            from pydantic import Field, create_model
        except ImportError as e:
            raise ImportError(
                "LangChain is required for LangChainAdapter. "
                "Install with: pip install langchain-core"
            ) from e

        # Import tools for introspection
        from .. import tools

        # Get tool function
        if not hasattr(tools, tool_name):
            return None

        tool_func = getattr(tools, tool_name)

        # Generate schema using auto-generation
        schema = generate_langchain_schema(tool_name, tool_func)

        # Convert schema to Pydantic model
        model_fields = {}
        for param_name, param_schema in schema["parameters"]["properties"].items():
            param_type = str  # Default to string
            field_kwargs = {"description": param_schema["description"]}

            # Convert JSON Schema type to Python type
            if param_schema["type"] == "integer":
                param_type = int
            elif param_schema["type"] == "number":
                param_type = float
            elif param_schema["type"] == "boolean":
                param_type = bool
            elif param_schema["type"] == "array":
                param_type = list[str]  # Simplified - could be more specific
            elif param_schema["type"] == "object":
                param_type = dict

            # Check if parameter is required
            if param_name in schema["parameters"]["required"]:
                field_kwargs["default"] = ...  # Required field marker
            else:
                # For optional parameters, make them Union with None
                param_type = param_type | None
                field_kwargs["default"] = None

            model_fields[param_name] = (param_type, Field(**field_kwargs))

        # Create input model
        model_name = f"{tool_name.title().replace('_', '')}Input"
        input_model = create_model(model_name, **model_fields)

        config = {
            "description": schema["description"],
            "input_model": input_model,
        }

        # Create async tool execution function
        async def execute_tool_async(**kwargs: Any) -> str:
            """Async LangChain tool execution."""
            try:
                result = await self.execute_tool(tool_name, **kwargs)
                return json.dumps(result, indent=2, default=str)
            except Exception as e:
                return f"Error: {e}"

        return StructuredTool(
            name=tool_name,
            description=config["description"],
            args_schema=config["input_model"],
            coroutine=execute_tool_async,
        )

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        """Get auto-generated tool schemas in LangChain format.

        Returns:
            List of auto-generated tool schema dictionaries
        """
        enabled_tools = self.config.get_enabled_tools()
        schemas = []

        # Import tools for introspection
        from .. import tools

        for tool_name in enabled_tools:
            tool_func = getattr(tools, tool_name, None)
            if tool_func:
                schema = generate_langchain_schema(tool_name, tool_func)
                # Add framework metadata
                schema["framework"] = "langchain"
                schemas.append(schema)

        return schemas

    async def execute_tool(self, tool_name: str, **kwargs: Any) -> Any:
        """Execute a tool directly with LangChain-style error handling.

        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool arguments

        Returns:
            Tool result

        Raises:
            ValidationError: For input validation errors
            ToolError: For execution errors
        """
        # Import tools dynamically
        from .. import tools

        # Check if tool exists
        if not hasattr(tools, tool_name):
            raise ValidationError(
                f"Unknown tool '{tool_name}'", field="tool_name", value=tool_name
            )

        # Check if tool is enabled
        if not self.config.is_tool_enabled(tool_name):
            available_tools = list(self.config.get_enabled_tools())
            raise ValidationError(
                f"Tool '{tool_name}' is not enabled. Available tools: {available_tools}",
                field="tool_name",
                value=tool_name,
            )

        tool_func = getattr(tools, tool_name)

        try:
            return await tool_func(self.client, **kwargs)
        except (ValidationError, ToolError):
            # Re-raise framework errors as-is
            raise
        except Exception as e:
            # Wrap unexpected errors
            raise ToolError(str(e), error_type=type(e).__name__) from e
