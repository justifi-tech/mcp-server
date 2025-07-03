"""
LangChain Adapter for JustiFi Tools

This adapter wraps framework-agnostic JustiFi tools with LangChain-specific
handling, converting raw tool results to LangChain StructuredTool format.
"""

from __future__ import annotations

import json
from typing import Any

from ..config import JustiFiConfig
from ..core import JustiFiClient
from ..tools import AVAILABLE_TOOLS, TOOL_SCHEMAS
from ..tools.base import ToolError, ValidationError


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
            if tool_name in AVAILABLE_TOOLS:
                tool_func = AVAILABLE_TOOLS[tool_name]

                # Create LangChain tool based on tool type
                langchain_tool = self._create_langchain_tool(tool_name, tool_func)
                if langchain_tool:
                    langchain_tools.append(langchain_tool)

        return langchain_tools

    def _create_langchain_tool(self, tool_name: str, tool_func: Any) -> Any:
        """Create a LangChain StructuredTool for a specific tool."""
        try:
            from langchain_core.tools import StructuredTool
            from pydantic import BaseModel, Field
        except ImportError as e:
            raise ImportError(
                "LangChain is required for LangChainAdapter. "
                "Install with: pip install langchain-core"
            ) from e

        # Get tool schema and metadata
        schema = TOOL_SCHEMAS[tool_name]

        # Convert description to string if it's a list
        description = schema.get("description", "")
        if isinstance(description, list | tuple):
            description = " ".join(str(d) for d in description)

        # Ensure description is a string
        description = str(description)

        # Create input models for each specific tool
        InputModel: type[BaseModel]

        if tool_name == "retrieve_payout":

            class RetrievePayoutInput(BaseModel):
                payout_id: str = Field(description="The ID of the payout to retrieve")

            InputModel = RetrievePayoutInput

        elif tool_name == "list_payouts":

            class ListPayoutsInput(BaseModel):
                limit: int = Field(
                    default=25, description="Number of payouts to return"
                )
                after_cursor: str | None = Field(
                    default=None, description="Pagination cursor"
                )
                before_cursor: str | None = Field(
                    default=None, description="Pagination cursor"
                )

            InputModel = ListPayoutsInput

        elif tool_name == "get_payout_status":

            class GetPayoutStatusInput(BaseModel):
                payout_id: str = Field(description="The ID of the payout to check")

            InputModel = GetPayoutStatusInput

        elif tool_name == "get_recent_payouts":

            class GetRecentPayoutsInput(BaseModel):
                limit: int = Field(default=10, description="Number of recent payouts")

            InputModel = GetRecentPayoutsInput

        else:
            # Fallback for unknown tools
            class GenericInput(BaseModel):
                pass

            InputModel = GenericInput

        # Create wrapper function
        def wrapper(**kwargs: Any) -> str:
            """LangChain tool wrapper."""
            import asyncio

            try:
                # Try to get the current event loop
                try:
                    loop = asyncio.get_running_loop()
                    # If we have a running loop, use it directly
                    import concurrent.futures

                    def run_async():
                        return asyncio.run(self.execute_tool(tool_name, **kwargs))

                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(run_async)
                        result = future.result()
                except RuntimeError:
                    # No running loop, safe to use asyncio.run
                    result = asyncio.run(self.execute_tool(tool_name, **kwargs))

                return json.dumps(result, indent=2, default=str)
            except Exception as e:
                return f"Error: {e}"

        # Create async wrapper function for arun support
        async def async_wrapper(**kwargs: Any) -> str:
            """Async LangChain tool wrapper."""
            try:
                result = await self.execute_tool(tool_name, **kwargs)
                return json.dumps(result, indent=2, default=str)
            except Exception as e:
                return f"Error: {e}"

        return StructuredTool(
            name=tool_name,
            description=description,
            args_schema=InputModel,
            func=wrapper,
            coroutine=async_wrapper,
        )

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        """Get tool schemas in LangChain format.

        Returns:
            List of tool schema dictionaries
        """
        enabled_tools = self.config.get_enabled_tools()
        schemas = []

        for tool_name in enabled_tools:
            if tool_name in TOOL_SCHEMAS:
                schema = TOOL_SCHEMAS[tool_name].copy()
                # Add LangChain-specific metadata
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
        # First check if tool exists
        if tool_name not in AVAILABLE_TOOLS:
            raise ValidationError(
                f"Unknown tool '{tool_name}'", field="tool_name", value=tool_name
            )

        # Then check if tool is enabled
        if not self.config.is_tool_enabled(tool_name):
            available_tools = list(self.config.get_enabled_tools())
            raise ValidationError(
                f"Tool '{tool_name}' is not enabled. Available tools: {available_tools}",
                field="tool_name",
                value=tool_name,
            )

        tool_func = AVAILABLE_TOOLS[tool_name]

        try:
            return await tool_func(self.client, **kwargs)
        except (ValidationError, ToolError):
            # Re-raise framework errors as-is
            raise
        except Exception as e:
            # Wrap unexpected errors
            raise ToolError(str(e), error_type=type(e).__name__) from e
