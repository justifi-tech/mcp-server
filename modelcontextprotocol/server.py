"""FastMCP Server Implementation for JustiFi."""

from typing import Any

from fastmcp import FastMCP

from python.config import JustiFiConfig

# Import JustiFi tools from python directory
from python.core import JustiFiClient


def create_mcp_server() -> FastMCP:
    """Create and configure the FastMCP server with all JustiFi tools."""
    # Initialize FastMCP server
    mcp: FastMCP = FastMCP("JustiFi Payment Server")

    # Load configuration
    config = JustiFiConfig()

    # Ensure we have valid credentials
    client_id = config.client_id
    client_secret = config.client_secret
    if not client_id or not client_secret:
        raise ValueError("JustiFi client_id and client_secret must be configured")

    client = JustiFiClient(
        client_id=client_id,
        client_secret=client_secret,
    )

    # Register all JustiFi tools
    register_tools(mcp, client)

    return mcp


def register_tools(mcp: FastMCP, client: JustiFiClient) -> None:
    """Register all JustiFi tools with FastMCP server."""

    # Payout tools
    @mcp.tool
    async def retrieve_payout(payout_id: str) -> dict[str, Any]:
        """Retrieve detailed information about a specific payout by ID.

        Args:
            payout_id: The unique identifier for the payout (e.g., 'po_ABC123XYZ')

        Returns:
            Payout object with ID, status, amount, and details
        """
        from python.tools.payouts import retrieve_payout as _retrieve_payout

        return await _retrieve_payout(client, payout_id)

    @mcp.tool
    async def list_payouts(
        limit: int = 25,
        after_cursor: str | None = None,
        before_cursor: str | None = None,
    ) -> dict[str, Any]:
        """List payouts with optional pagination using cursor-based pagination.

        Args:
            limit: Number of payouts to return (1-100, default: 25)
            after_cursor: Cursor for pagination - returns results after this cursor
            before_cursor: Cursor for pagination - returns results before this cursor

        Returns:
            Paginated list of payouts with page_info for navigation
        """
        from python.tools.payouts import list_payouts as _list_payouts

        return await _list_payouts(client, limit, after_cursor, before_cursor)

    @mcp.tool
    async def get_payout_status(payout_id: str) -> str:
        """Get the current status of a payout (quick status check).

        Args:
            payout_id: The unique identifier for the payout

        Returns:
            The status string of the payout (e.g., 'pending', 'completed', 'failed')
        """
        from python.tools.payouts import get_payout_status as _get_payout_status

        return await _get_payout_status(client, payout_id)

    @mcp.tool
    async def get_recent_payouts(limit: int = 10) -> dict[str, Any]:
        """Get the most recent payouts (optimized for recency).

        Args:
            limit: Number of recent payouts to return (1-50, default: 10)

        Returns:
            List of recent payouts
        """
        from python.tools.payouts import get_recent_payouts as _get_recent_payouts

        return await _get_recent_payouts(client, limit)

    # Payment tools
    @mcp.tool
    async def retrieve_payment(payment_id: str) -> dict[str, Any]:
        """Retrieve detailed information about a specific payment by ID.

        Args:
            payment_id: The unique identifier for the payment (e.g., 'py_ABC123XYZ')

        Returns:
            Payment object with ID, status, amount, and details
        """
        from python.tools.payments import retrieve_payment as _retrieve_payment

        return await _retrieve_payment(client, payment_id)

    @mcp.tool
    async def list_payments(
        limit: int = 25, after_cursor: str = None, before_cursor: str = None
    ) -> dict[str, Any]:
        """List payments with optional pagination using cursor-based pagination.

        Args:
            limit: Number of payments to return (1-100, default: 25)
            after_cursor: Cursor for pagination - returns results after this cursor
            before_cursor: Cursor for pagination - returns results before this cursor

        Returns:
            Paginated list of payments with page_info for navigation
        """
        from python.tools.payments import list_payments as _list_payments

        return await _list_payments(client, limit, after_cursor, before_cursor)

    # Payment method tools
    @mcp.tool
    async def retrieve_payment_method(payment_method_token: str) -> dict[str, Any]:
        """Retrieve detailed information about a specific payment method by token.

        Args:
            payment_method_token: The unique token for the payment method (e.g., 'pm_ABC123XYZ')

        Returns:
            Payment method object with token, type, card/bank details, and metadata
        """
        from python.tools.payment_methods import (
            retrieve_payment_method as _retrieve_payment_method,
        )

        return await _retrieve_payment_method(client, payment_method_token)

    # Refund tools
    @mcp.tool
    async def list_refunds(
        limit: int = 25, after_cursor: str = None, before_cursor: str = None
    ) -> dict[str, Any]:
        """List all refunds with optional pagination using cursor-based pagination.

        Args:
            limit: Number of refunds to return (1-100, default: 25)
            after_cursor: Cursor for pagination - returns results after this cursor
            before_cursor: Cursor for pagination - returns results before this cursor

        Returns:
            Paginated list of refunds with page_info for navigation
        """
        from python.tools.refunds import list_refunds as _list_refunds

        return await _list_refunds(client, limit, after_cursor, before_cursor)

    @mcp.tool
    async def retrieve_refund(refund_id: str) -> dict[str, Any]:
        """Retrieve detailed information about a specific refund by ID.

        Args:
            refund_id: The unique identifier for the refund (e.g., 're_ABC123XYZ')

        Returns:
            Refund object with ID, status, amount, and details
        """
        from python.tools.refunds import retrieve_refund as _retrieve_refund

        return await _retrieve_refund(client, refund_id)

    @mcp.tool
    async def list_payment_refunds(payment_id: str) -> dict[str, Any]:
        """List refunds for a specific payment by extracting them from the payment data.

        Args:
            payment_id: The unique identifier for the payment (e.g., 'py_ABC123XYZ')

        Returns:
            List of refunds for the specified payment
        """
        from python.tools.refunds import list_payment_refunds as _list_payment_refunds

        return await _list_payment_refunds(client, payment_id)

    # Balance transaction tools
    @mcp.tool
    async def list_balance_transactions(
        limit: int = 25,
        after_cursor: str = None,
        before_cursor: str = None,
        payout_id: str = None,
    ) -> dict[str, Any]:
        """List balance transactions with optional pagination and filtering by payout.

        Args:
            limit: Number of balance transactions to return (1-100, default: 25)
            after_cursor: Cursor for pagination - returns results after this cursor
            before_cursor: Cursor for pagination - returns results before this cursor
            payout_id: Filter records which are part of the payout with the specified id (e.g., 'po_ABC123XYZ')

        Returns:
            Paginated list of balance transactions with page_info for navigation
        """
        from python.tools.balances import (
            list_balance_transactions as _list_balance_transactions,
        )

        return await _list_balance_transactions(
            client, limit, after_cursor, before_cursor, payout_id
        )

    @mcp.tool
    async def retrieve_balance_transaction(
        balance_transaction_id: str,
    ) -> dict[str, Any]:
        """Retrieve detailed information about a specific balance transaction by ID.

        Args:
            balance_transaction_id: The unique identifier for the balance transaction (e.g., 'bt_ABC123XYZ')

        Returns:
            Balance transaction object with ID, amount, type, and details
        """
        from python.tools.balances import (
            retrieve_balance_transaction as _retrieve_balance_transaction,
        )

        return await _retrieve_balance_transaction(client, balance_transaction_id)

    # Dispute tools
    @mcp.tool
    async def list_disputes(
        limit: int = 25, after_cursor: str = None, before_cursor: str = None
    ) -> dict[str, Any]:
        """List disputes with optional pagination using cursor-based pagination.

        Args:
            limit: Number of disputes to return (1-100, default: 25)
            after_cursor: Cursor for pagination - returns results after this cursor
            before_cursor: Cursor for pagination - returns results before this cursor

        Returns:
            Paginated list of disputes with page_info for navigation
        """
        from python.tools.disputes import list_disputes as _list_disputes

        return await _list_disputes(client, limit, after_cursor, before_cursor)

    @mcp.tool
    async def retrieve_dispute(dispute_id: str) -> dict[str, Any]:
        """Retrieve detailed information about a specific dispute by ID.

        Args:
            dispute_id: The unique identifier for the dispute (e.g., 'dp_ABC123XYZ')

        Returns:
            Dispute object with ID, status, amount, and details
        """
        from python.tools.disputes import retrieve_dispute as _retrieve_dispute

        return await _retrieve_dispute(client, dispute_id)

    # Checkout tools
    @mcp.tool
    async def list_checkouts(
        limit: int = 25,
        after_cursor: str = None,
        before_cursor: str = None,
        payment_mode: str = None,
        status: str = None,
        payment_status: str = None,
    ) -> dict[str, Any]:
        """List checkouts with optional pagination and filtering by payment mode, status, and payment status.

        Args:
            limit: Number of checkouts to return (1-100, default: 25)
            after_cursor: Cursor for pagination - returns results after this cursor
            before_cursor: Cursor for pagination - returns results before this cursor
            payment_mode: Filter by payment mode ('bnpl', 'ecom')
            status: Filter by checkout status ('created', 'completed', 'attempted', 'expired')
            payment_status: Filter by payment status

        Returns:
            Paginated list of checkouts with page_info for navigation
        """
        from python.tools.checkouts import list_checkouts as _list_checkouts

        return await _list_checkouts(
            client,
            limit,
            after_cursor,
            before_cursor,
            payment_mode,
            status,
            payment_status,
        )

    @mcp.tool
    async def retrieve_checkout(checkout_id: str) -> dict[str, Any]:
        """Retrieve detailed information about a specific checkout by ID.

        Args:
            checkout_id: The unique identifier for the checkout (e.g., 'co_ABC123XYZ')

        Returns:
            Checkout object with ID, status, amount, and details
        """
        from python.tools.checkouts import retrieve_checkout as _retrieve_checkout

        return await _retrieve_checkout(client, checkout_id)

    # Sub Account tools
    @mcp.tool
    async def list_sub_accounts(
        status: str = None,
        limit: int = 25,
        after_cursor: str = None,
        before_cursor: str = None,
    ) -> dict[str, Any]:
        """List sub accounts with optional status filtering and pagination.

        Args:
            status: Optional status filter - one of: created, submitted, information_needed, rejected, approved, enabled, disabled, archived
            limit: Number of sub accounts to return (1-100, default: 25)
            after_cursor: Cursor for pagination - returns results after this cursor
            before_cursor: Cursor for pagination - returns results before this cursor

        Returns:
            Paginated list of sub accounts with page_info for navigation
        """
        from python.tools.sub_accounts import list_sub_accounts as _list_sub_accounts

        return await _list_sub_accounts(client, status, limit, after_cursor, before_cursor)

    @mcp.tool
    async def get_sub_account(sub_account_id: str) -> dict[str, Any]:
        """Get detailed information about a specific sub account by ID.

        Args:
            sub_account_id: The unique identifier for the sub account (e.g., 'acc_ABC123XYZ')

        Returns:
            Sub account object with ID, name, status, and other details
        """
        from python.tools.sub_accounts import get_sub_account as _get_sub_account

        return await _get_sub_account(client, sub_account_id)

    @mcp.tool
    async def get_sub_account_payout_account(sub_account_id: str) -> dict[str, Any]:
        """Get information about the currently active payout bank account of a sub account.

        Args:
            sub_account_id: The unique identifier for the sub account (e.g., 'acc_ABC123XYZ')

        Returns:
            Payout bank account object with account details
        """
        from python.tools.sub_accounts import (
            get_sub_account_payout_account as _get_sub_account_payout_account,
        )

        return await _get_sub_account_payout_account(client, sub_account_id)

    @mcp.tool
    async def get_sub_account_settings(sub_account_id: str) -> dict[str, Any]:
        """Get information about sub account settings.

        Args:
            sub_account_id: The unique identifier for the sub account (e.g., 'acc_ABC123XYZ')

        Returns:
            Sub account settings object
        """
        from python.tools.sub_accounts import (
            get_sub_account_settings as _get_sub_account_settings,
        )

        return await _get_sub_account_settings(client, sub_account_id)
