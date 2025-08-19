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

        # Define tool schemas for LangChain integration
        tool_configs = {
            "retrieve_payout": {
                "description": "Retrieve detailed information about a specific payout by ID.",
                "input_model": create_model(
                    "RetrievePayoutInput",
                    payout_id=(
                        str,
                        Field(..., description="The ID of the payout to retrieve"),
                    ),
                ),
            },
            "list_payouts": {
                "description": "List payouts with optional pagination using cursor-based pagination.",
                "input_model": create_model(
                    "ListPayoutsInput",
                    limit=(
                        int,
                        Field(default=25, description="Number of payouts to return"),
                    ),
                    after_cursor=(
                        str | None,
                        Field(default=None, description="Pagination cursor"),
                    ),
                    before_cursor=(
                        str | None,
                        Field(default=None, description="Pagination cursor"),
                    ),
                ),
            },
            "get_payout_status": {
                "description": "Get the current status of a payout (quick status check).",
                "input_model": create_model(
                    "GetPayoutStatusInput",
                    payout_id=(
                        str,
                        Field(..., description="The ID of the payout to check"),
                    ),
                ),
            },
            "get_recent_payouts": {
                "description": "Get the most recent payouts (optimized for recency).",
                "input_model": create_model(
                    "GetRecentPayoutsInput",
                    limit=(
                        int,
                        Field(default=10, description="Number of recent payouts"),
                    ),
                ),
            },
            "retrieve_payment": {
                "description": "Retrieve detailed information about a specific payment by ID.",
                "input_model": create_model(
                    "RetrievePaymentInput",
                    payment_id=(
                        str,
                        Field(..., description="The ID of the payment to retrieve"),
                    ),
                ),
            },
            "list_payments": {
                "description": "List payments with optional pagination using cursor-based pagination.",
                "input_model": create_model(
                    "ListPaymentsInput",
                    limit=(
                        int,
                        Field(default=25, description="Number of payments to return"),
                    ),
                    after_cursor=(
                        str | None,
                        Field(default=None, description="Pagination cursor"),
                    ),
                    before_cursor=(
                        str | None,
                        Field(default=None, description="Pagination cursor"),
                    ),
                ),
            },
            "retrieve_payment_method": {
                "description": "Retrieve detailed information about a specific payment method by token.",
                "input_model": create_model(
                    "RetrievePaymentMethodInput",
                    payment_method_token=(
                        str,
                        Field(..., description="The payment method token"),
                    ),
                ),
            },
            "create_payment_method_group": {
                "description": "Create a new payment method group to organize tokenized payment methods.",
                "input_model": create_model(
                    "CreatePaymentMethodGroupInput",
                    name=(
                        str,
                        Field(..., description="Name of the payment method group"),
                    ),
                    description=(
                        str | None,
                        Field(
                            default=None,
                            description="Optional description of the group",
                        ),
                    ),
                    payment_method_ids=(
                        list[str] | None,
                        Field(
                            default=None,
                            description="Optional list of payment method IDs to add to the group",
                        ),
                    ),
                ),
            },
            "list_payment_method_groups": {
                "description": "List payment method groups with optional pagination.",
                "input_model": create_model(
                    "ListPaymentMethodGroupsInput",
                    limit=(
                        int,
                        Field(
                            default=25, description="Number of groups to return (1-100)"
                        ),
                    ),
                    after_cursor=(
                        str | None,
                        Field(
                            default=None,
                            description="Pagination cursor for results after this cursor",
                        ),
                    ),
                    before_cursor=(
                        str | None,
                        Field(
                            default=None,
                            description="Pagination cursor for results before this cursor",
                        ),
                    ),
                ),
            },
            "retrieve_payment_method_group": {
                "description": "Retrieve detailed information about a specific payment method group.",
                "input_model": create_model(
                    "RetrievePaymentMethodGroupInput",
                    group_id=(
                        str,
                        Field(
                            ...,
                            description="The unique identifier for the payment method group",
                        ),
                    ),
                ),
            },
            "update_payment_method_group": {
                "description": "Update an existing payment method group.",
                "input_model": create_model(
                    "UpdatePaymentMethodGroupInput",
                    group_id=(
                        str,
                        Field(
                            ...,
                            description="The unique identifier for the payment method group",
                        ),
                    ),
                    name=(
                        str | None,
                        Field(default=None, description="New name for the group"),
                    ),
                    description=(
                        str | None,
                        Field(
                            default=None, description="New description for the group"
                        ),
                    ),
                    payment_method_ids=(
                        list[str] | None,
                        Field(
                            default=None,
                            description="New list of payment method IDs to set in the group",
                        ),
                    ),
                ),
            },
            "remove_payment_method_from_group": {
                "description": "Remove a payment method from a payment method group.",
                "input_model": create_model(
                    "RemovePaymentMethodFromGroupInput",
                    group_id=(
                        str,
                        Field(
                            ...,
                            description="The unique identifier for the payment method group",
                        ),
                    ),
                    payment_method_id=(
                        str,
                        Field(
                            ...,
                            description="The payment method ID to remove from the group",
                        ),
                    ),
                ),
            },
            "list_refunds": {
                "description": "List all refunds with optional pagination using cursor-based pagination.",
                "input_model": create_model(
                    "ListRefundsInput",
                    limit=(
                        int,
                        Field(default=25, description="Number of refunds to return"),
                    ),
                    after_cursor=(
                        str | None,
                        Field(default=None, description="Pagination cursor"),
                    ),
                    before_cursor=(
                        str | None,
                        Field(default=None, description="Pagination cursor"),
                    ),
                ),
            },
            "retrieve_refund": {
                "description": "Retrieve detailed information about a specific refund by ID.",
                "input_model": create_model(
                    "RetrieveRefundInput",
                    refund_id=(
                        str,
                        Field(..., description="The ID of the refund to retrieve"),
                    ),
                ),
            },
            "list_payment_refunds": {
                "description": "List refunds for a specific payment by extracting them from the payment data.",
                "input_model": create_model(
                    "ListPaymentRefundsInput",
                    payment_id=(str, Field(..., description="The ID of the payment")),
                ),
            },
            "list_balance_transactions": {
                "description": "List balance transactions with optional pagination and filtering by payout.",
                "input_model": create_model(
                    "ListBalanceTransactionsInput",
                    limit=(
                        int,
                        Field(
                            default=25,
                            description="Number of balance transactions to return",
                        ),
                    ),
                    after_cursor=(
                        str | None,
                        Field(default=None, description="Pagination cursor"),
                    ),
                    before_cursor=(
                        str | None,
                        Field(default=None, description="Pagination cursor"),
                    ),
                    payout_id=(
                        str | None,
                        Field(default=None, description="Filter by payout ID"),
                    ),
                ),
            },
            "retrieve_balance_transaction": {
                "description": "Retrieve detailed information about a specific balance transaction by ID.",
                "input_model": create_model(
                    "RetrieveBalanceTransactionInput",
                    balance_transaction_id=(
                        str,
                        Field(..., description="The ID of the balance transaction"),
                    ),
                ),
            },
            "list_disputes": {
                "description": "List disputes with optional pagination using cursor-based pagination.",
                "input_model": create_model(
                    "ListDisputesInput",
                    limit=(
                        int,
                        Field(default=25, description="Number of disputes to return"),
                    ),
                    after_cursor=(
                        str | None,
                        Field(default=None, description="Pagination cursor"),
                    ),
                    before_cursor=(
                        str | None,
                        Field(default=None, description="Pagination cursor"),
                    ),
                ),
            },
            "retrieve_dispute": {
                "description": "Retrieve detailed information about a specific dispute by ID.",
                "input_model": create_model(
                    "RetrieveDisputeInput",
                    dispute_id=(
                        str,
                        Field(..., description="The ID of the dispute to retrieve"),
                    ),
                ),
            },
            "list_checkouts": {
                "description": "List checkouts with optional pagination and filtering by payment mode, status, and payment status.",
                "input_model": create_model(
                    "ListCheckoutsInput",
                    limit=(
                        int,
                        Field(default=25, description="Number of checkouts to return"),
                    ),
                    after_cursor=(
                        str | None,
                        Field(default=None, description="Pagination cursor"),
                    ),
                    before_cursor=(
                        str | None,
                        Field(default=None, description="Pagination cursor"),
                    ),
                    payment_mode=(
                        str | None,
                        Field(default=None, description="Filter by payment mode"),
                    ),
                    status=(
                        str | None,
                        Field(default=None, description="Filter by checkout status"),
                    ),
                    payment_status=(
                        str | None,
                        Field(default=None, description="Filter by payment status"),
                    ),
                ),
            },
            "retrieve_checkout": {
                "description": "Retrieve detailed information about a specific checkout by ID.",
                "input_model": create_model(
                    "RetrieveCheckoutInput",
                    checkout_id=(
                        str,
                        Field(..., description="The ID of the checkout to retrieve"),
                    ),
                ),
            },
            "list_proceeds": {
                "description": "List proceeds with optional pagination using cursor-based pagination.",
                "input_model": create_model(
                    "ListProceedsInput",
                    limit=(
                        int,
                        Field(default=25, description="Number of proceeds to return"),
                    ),
                    after_cursor=(
                        str | None,
                        Field(default=None, description="Pagination cursor"),
                    ),
                    before_cursor=(
                        str | None,
                        Field(default=None, description="Pagination cursor"),
                    ),
                ),
            },
            "retrieve_proceed": {
                "description": "Retrieve detailed information about a specific proceed by ID.",
                "input_model": create_model(
                    "RetrieveProceedInput",
                    proceed_id=(
                        str,
                        Field(..., description="The ID of the proceed to retrieve"),
                    ),
                ),
            },
            "list_sub_accounts": {
                "description": "List sub accounts with optional status filtering and pagination.",
                "input_model": create_model(
                    "ListSubAccountsInput",
                    status=(
                        str | None,
                        Field(
                            default=None,
                            description="Filter by status (created, submitted, information_needed, rejected, approved, enabled, disabled, archived)",
                        ),
                    ),
                    limit=(
                        int,
                        Field(
                            default=25,
                            description="Number of sub accounts to return (1-100)",
                        ),
                    ),
                    after_cursor=(
                        str | None,
                        Field(default=None, description="Pagination cursor"),
                    ),
                    before_cursor=(
                        str | None,
                        Field(default=None, description="Pagination cursor"),
                    ),
                ),
            },
            "get_sub_account": {
                "description": "Get detailed information about a specific sub account by ID.",
                "input_model": create_model(
                    "GetSubAccountInput",
                    sub_account_id=(
                        str,
                        Field(..., description="The ID of the sub account to retrieve"),
                    ),
                ),
            },
            "get_sub_account_payout_account": {
                "description": "Get information about the currently active payout bank account of a sub account.",
                "input_model": create_model(
                    "GetSubAccountPayoutAccountInput",
                    sub_account_id=(
                        str,
                        Field(..., description="The ID of the sub account"),
                    ),
                ),
            },
            "get_sub_account_settings": {
                "description": "Get information about sub account settings.",
                "input_model": create_model(
                    "GetSubAccountSettingsInput",
                    sub_account_id=(
                        str,
                        Field(..., description="The ID of the sub account"),
                    ),
                ),
            },
        }

        if tool_name not in tool_configs:
            return None

        config = tool_configs[tool_name]

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
        """Get tool schemas in LangChain format.

        Returns:
            List of tool schema dictionaries
        """
        enabled_tools = self.config.get_enabled_tools()
        schemas = []

        # Simple schema definitions
        for tool_name in enabled_tools:
            schema = {
                "name": tool_name,
                "description": f"JustiFi tool: {tool_name}",
                "framework": "langchain",
            }
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
