"""JustiFi Agent Toolkit

Framework-agnostic toolkit for JustiFi payment operations.
Provides adapters for different AI frameworks (MCP, LangChain, OpenAI, etc.).
"""

from __future__ import annotations

from typing import Any

from .adapters.mcp import MCPAdapter
from .config import JustiFiConfig
from .tools import AVAILABLE_TOOLS


class JustiFiToolkit:
    """Multi-framework toolkit for JustiFi payment operations.

    Provides a unified interface to JustiFi tools that can be used across
    different AI frameworks (MCP, LangChain, OpenAI, etc.) with configuration-driven
    tool selection and context management.

    Examples:
        # Basic usage with all tools enabled
        toolkit = JustiFiToolkit(
            client_id="your_client_id",
            client_secret="your_client_secret",
            enabled_tools="all"
        )

        # Selective tool enabling
        toolkit = JustiFiToolkit(
            client_id="your_client_id",
            client_secret="your_client_secret",
            enabled_tools=["retrieve_payout", "list_payouts"]
        )

        # Framework-specific usage
        mcp_server = toolkit.get_mcp_server()
        langchain_tools = toolkit.get_langchain_tools()
    """

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        enabled_tools: str | list[str] = "all",
        context: dict[str, Any] | None = None,
        configuration: dict[str, Any] | None = None,
        config: JustiFiConfig | None = None,
        **kwargs: Any,
    ):
        """Initialize JustiFi toolkit with configuration.

        Args:
            client_id: JustiFi API client ID
            client_secret: JustiFi API client secret
            enabled_tools: Tools to enable ("all" or list of tool names)
            context: Additional context configuration
            configuration: Legacy configuration dict support
            config: Pre-configured JustiFiConfig instance
            **kwargs: Additional configuration parameters
        """
        if config:
            # Use provided configuration object
            self.config = config
        elif configuration:
            # Legacy configuration dict support
            self.config = JustiFiConfig(**configuration, **kwargs)
        else:
            # Create new configuration from parameters
            self.config = JustiFiConfig(
                client_id=client_id,
                client_secret=client_secret,
                enabled_tools=enabled_tools,
                context=context,
                **kwargs,
            )

        # Initialize adapters as None for lazy loading
        self._mcp_adapter: MCPAdapter | None = None
        self._langchain_adapter = None

    def get_enabled_tools(self) -> dict[str, Any]:
        """Get currently enabled tools based on configuration.

        Returns:
            Dictionary mapping tool names to tool functions
        """
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
            List of LangChain StructuredTool instances

        Raises:
            ImportError: If LangChain is not installed
        """
        if not hasattr(self, "_langchain_adapter"):
            from .adapters.langchain import LangChainAdapter

            self._langchain_adapter = LangChainAdapter(self.config)

        return self._langchain_adapter.get_langchain_tools()  # type: ignore[no-any-return]

    def get_langchain_schemas(self) -> list[dict[str, Any]]:
        """Get tool schemas for LangChain integration.

        Returns:
            List of tool schema dictionaries
        """
        if not hasattr(self, "_langchain_adapter"):
            from .adapters.langchain import LangChainAdapter

            self._langchain_adapter = LangChainAdapter(self.config)

        return self._langchain_adapter.get_tool_schemas()  # type: ignore[no-any-return]

    async def execute_langchain_tool(self, tool_name: str, **kwargs: Any) -> Any:
        """Execute a tool directly with LangChain-style error handling.

        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool arguments

        Returns:
            Tool result
        """
        if not self._langchain_adapter:
            from .adapters.langchain import LangChainAdapter

            self._langchain_adapter = LangChainAdapter(self.config)

        return await self._langchain_adapter.execute_tool(tool_name, **kwargs)

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
