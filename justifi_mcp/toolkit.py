"""JustiFi Agent Toolkit

Framework-agnostic toolkit for JustiFi payment operations.
Provides adapters for different AI frameworks (MCP, LangChain, OpenAI, etc.).
"""

from __future__ import annotations

from typing import Any, cast

from .adapters.mcp import MCPAdapter
from .config import JustiFiConfig
from .core import JustiFiClient
from .tools import AVAILABLE_TOOLS


class JustiFiToolkit:
    """Framework-agnostic JustiFi Agent Toolkit.

    Provides consistent interfaces for JustiFi payment operations across
    multiple AI frameworks (MCP, LangChain, OpenAI Agent SDK, etc.).

    Example:
        ```python
        from justifi_mcp import JustiFiToolkit

        # Basic usage with environment variables
        toolkit = JustiFiToolkit()

        # With explicit configuration
        toolkit = JustiFiToolkit(
            client_id="your_client_id",
            client_secret="your_client_secret",
            enabled_tools=["retrieve_payout", "list_payouts"]
        )

        # Framework-specific usage
        mcp_server = toolkit.get_mcp_server()
        langchain_tools = toolkit.get_langchain_tools()
        ```
    """

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        configuration: dict[str, Any] | None = None,
        config: JustiFiConfig | None = None,
        **kwargs: Any,
    ):
        """Initialize JustiFi toolkit.

        Args:
            client_id: JustiFi client ID (or from JUSTIFI_CLIENT_ID env var)
            client_secret: JustiFi client secret (or from JUSTIFI_CLIENT_SECRET env var)
            configuration: Dictionary configuration (legacy support)
            config: Pre-built JustiFiConfig instance (takes precedence)
            **kwargs: Additional configuration parameters

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

            # Add any additional kwargs
            config_data.update(kwargs)

            self.config = JustiFiConfig(**config_data)

        # Validate credentials
        if not self.config.client_id or not self.config.client_secret:
            raise ValueError("JustiFi credentials are required")

        # Initialize client
        self.client = JustiFiClient(
            client_id=self.config.client_id, client_secret=self.config.client_secret
        )

        # Initialize adapters (lazy-loaded)
        self._mcp_adapter: MCPAdapter | None = None

    def get_enabled_tools(self) -> dict[str, Any]:
        """Get dictionary of enabled tools and their functions."""
        enabled_tools = {}
        enabled_tool_names = self.config.get_enabled_tools()

        for tool_name in enabled_tool_names:
            if tool_name in AVAILABLE_TOOLS:
                enabled_tools[tool_name] = AVAILABLE_TOOLS[tool_name]

        return enabled_tools

    def get_configuration_summary(self) -> dict[str, Any]:
        """Get a summary of the current configuration."""
        enabled_tools = self.get_enabled_tools()

        return {
            "environment": self.config.context.environment,
            "base_url": self.config.get_effective_base_url(),
            "timeout": self.config.context.timeout,
            "rate_limit": self.config.context.rate_limit,
            "enabled_tools": list(enabled_tools.keys()),
            "total_tools": len(enabled_tools),
            "available_tools": list(AVAILABLE_TOOLS.keys()),
        }

    # Framework-specific methods

    def get_mcp_server(self, server_name: str = "justifi-toolkit-mcp-server") -> Any:
        """Get an MCP server with JustiFi tools.

        Args:
            server_name: Name for the MCP server

        Returns:
            Configured MCP server instance
        """
        if not self._mcp_adapter:
            self._mcp_adapter = MCPAdapter(self.config)

        return self._mcp_adapter.create_mcp_server(server_name)

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool directly (framework-agnostic).

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result (format depends on framework)
        """
        if not self._mcp_adapter:
            self._mcp_adapter = MCPAdapter(self.config)

        return await self._mcp_adapter.call_tool(name, arguments)

    def get_tool_schemas(self) -> Any:
        """Get tool schemas for the current framework.

        Returns:
            List of tool schemas (format depends on framework)
        """
        if not self._mcp_adapter:
            self._mcp_adapter = MCPAdapter(self.config)

        return self._mcp_adapter.get_enabled_tool_schemas()

    def get_langchain_tools(self) -> list[Any]:
        """Get LangChain-compatible tools.

        Returns:
            List of LangChain Tool instances

        Raises:
            ImportError: If LangChain is not installed
        """
        try:
            from langchain_core.tools import StructuredTool
            from pydantic import BaseModel, Field
        except ImportError as e:
            raise ImportError(
                "LangChain is required for get_langchain_tools(). "
                "Install with: pip install langchain-core"
            ) from e

        enabled_tools = self.get_enabled_tools()
        langchain_tools = []

        for tool_name, tool_func in enabled_tools.items():
            # Create tool-specific input models and wrappers
            if tool_name == "retrieve_payout":

                class RetrievePayoutInput(BaseModel):
                    payout_id: str = Field(
                        description="The ID of the payout to retrieve (e.g., 'po_ABC123XYZ')"
                    )

                def create_retrieve_wrapper(func):
                    async def retrieve_payout_wrapper(**kwargs: Any) -> dict[str, Any]:
                        return cast(dict[str, Any], await func(self.client, **kwargs))

                    return retrieve_payout_wrapper

                tool = StructuredTool(
                    name="retrieve_payout",
                    description="Retrieve details of a specific payout by ID",
                    args_schema=RetrievePayoutInput,
                    coroutine=create_retrieve_wrapper(tool_func),
                )
                langchain_tools.append(tool)

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

                def create_list_wrapper(func):
                    async def list_payouts_wrapper(**kwargs: Any) -> dict[str, Any]:
                        return cast(dict[str, Any], await func(self.client, **kwargs))

                    return list_payouts_wrapper

                tool = StructuredTool(
                    name="list_payouts",
                    description="List payouts with cursor-based pagination",
                    args_schema=ListPayoutsInput,
                    coroutine=create_list_wrapper(tool_func),
                )
                langchain_tools.append(tool)

            elif tool_name == "get_payout_status":

                class GetPayoutStatusInput(BaseModel):
                    payout_id: str = Field(
                        description="The ID of the payout to check status for (e.g., 'po_ABC123XYZ')"
                    )

                def create_status_wrapper(func):
                    async def get_payout_status_wrapper(**kwargs: Any) -> str:
                        return cast(str, await func(self.client, **kwargs))

                    return get_payout_status_wrapper

                tool = StructuredTool(
                    name="get_payout_status",
                    description="Get the status of a specific payout",
                    args_schema=GetPayoutStatusInput,
                    coroutine=create_status_wrapper(tool_func),
                )
                langchain_tools.append(tool)

            elif tool_name == "get_recent_payouts":

                class GetRecentPayoutsInput(BaseModel):
                    limit: int = Field(
                        default=10,
                        description="Number of recent payouts to return (default: 10, max: 25)",
                        ge=1,
                        le=25,
                    )

                def create_recent_wrapper(func):
                    async def get_recent_payouts_wrapper(
                        **kwargs: Any,
                    ) -> list[dict[str, Any]]:
                        return cast(
                            list[dict[str, Any]], await func(self.client, **kwargs)
                        )

                    return get_recent_payouts_wrapper

                tool = StructuredTool(
                    name="get_recent_payouts",
                    description="Get the most recent payouts",
                    args_schema=GetRecentPayoutsInput,
                    coroutine=create_recent_wrapper(tool_func),
                )
                langchain_tools.append(tool)

        return langchain_tools

    def get_openai_functions(self) -> list[dict[str, Any]]:
        """Get OpenAI function definitions.

        Returns:
            List of OpenAI function definitions

        Raises:
            NotImplementedError: OpenAI integration coming in Phase 3
        """
        raise NotImplementedError("OpenAI integration coming in Phase 3")

    def get_direct_api(self) -> dict[str, Any]:
        """Get direct API access for custom integrations.

        Returns:
            Dictionary with client and tool functions

        Raises:
            NotImplementedError: Direct API coming in Phase 3
        """
        raise NotImplementedError("Direct API coming in Phase 3")
