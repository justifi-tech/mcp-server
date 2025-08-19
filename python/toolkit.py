"""JustiFi Agent Toolkit

Framework-agnostic toolkit for JustiFi payment operations.
Provides adapters for AI frameworks (LangChain) with direct usage support for OpenAI.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .adapters.langchain import LangChainAdapter

from .config import JustiFiConfig

# Simple tool registry for the toolkit
_TOOL_NAMES = [
    "list_balance_transactions",
    "retrieve_balance_transaction",
    "list_checkouts",
    "retrieve_checkout",
    "list_disputes",
    "retrieve_dispute",
    "retrieve_payment_method",
    "create_payment_method_group",
    "list_payment_method_groups",
    "retrieve_payment_method_group",
    "update_payment_method_group",
    "remove_payment_method_from_group",
    "list_payments",
    "retrieve_payment",
    "get_payout_status",
    "get_recent_payouts",
    "list_payouts",
    "retrieve_payout",
    "list_payment_refunds",
    "list_proceeds",
    "retrieve_proceed",
    "list_refunds",
    "retrieve_refund",
    "get_sub_account",
    "get_sub_account_payout_account",
    "get_sub_account_settings",
    "list_sub_accounts",
]


class JustiFiToolkit:
    """Multi-framework toolkit for JustiFi payment operations.

    Provides a unified interface to JustiFi tools that can be used across
    AI frameworks (LangChain) with configuration-driven tool selection
    and context management. OpenAI integration uses direct tool access.

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
        langchain_tools = toolkit.get_langchain_tools()
    """

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        enabled_tools: str | list[str] = "all",
        context: dict[str, Any] | None = None,
        config: JustiFiConfig | None = None,
        **kwargs: Any,
    ):
        """Initialize JustiFi toolkit with configuration.

        Args:
            client_id: JustiFi API client ID
            client_secret: JustiFi API client secret
            enabled_tools: Tools to enable ("all" or list of tool names)
            context: Additional context configuration
            config: Pre-configured JustiFiConfig instance
            **kwargs: Additional configuration parameters
        """
        if config:
            self.config = config
        else:
            self.config = JustiFiConfig(
                client_id=client_id,
                client_secret=client_secret,
                enabled_tools=enabled_tools,
                context=context,
                **kwargs,
            )

        # Initialize adapters as None for lazy loading
        self._langchain_adapter: LangChainAdapter | None = None

    def get_enabled_tools(self) -> dict[str, Any]:
        """Get currently enabled tools based on configuration.

        Returns:
            Dictionary mapping tool names to tool functions
        """
        enabled_tools = {}
        enabled_tool_names = self.config.get_enabled_tools()

        # Import tools dynamically to avoid circular imports
        from . import tools

        for tool_name in enabled_tool_names:
            if tool_name in _TOOL_NAMES:
                tool_func = getattr(tools, tool_name, None)
                if tool_func:
                    enabled_tools[tool_name] = tool_func

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
            "available_tools": _TOOL_NAMES,
        }

    # Framework-specific methods

    def get_langchain_tools(self) -> list[Any]:
        """Get LangChain-compatible tools.

        Returns:
            List of LangChain StructuredTool instances

        Raises:
            ImportError: If LangChain is not installed
        """
        if not self._langchain_adapter:
            from .adapters.langchain import LangChainAdapter

            self._langchain_adapter = LangChainAdapter(self.config)

        return self._langchain_adapter.get_langchain_tools()

    def get_langchain_schemas(self) -> list[dict[str, Any]]:
        """Get tool schemas for LangChain integration.

        Returns:
            List of tool schema dictionaries
        """
        if not self._langchain_adapter:
            from .adapters.langchain import LangChainAdapter

            self._langchain_adapter = LangChainAdapter(self.config)

        return self._langchain_adapter.get_tool_schemas()

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
