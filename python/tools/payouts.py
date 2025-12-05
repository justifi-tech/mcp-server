"""
JustiFi Payout Tools - Framework-Agnostic Business Logic

Pure business logic for payout operations, separated from any specific
framework (MCP, LangChain, etc.). These functions return raw Python data
structures and can be used by any framework adapter.
"""

from __future__ import annotations

from typing import Any

from ..core import JustiFiClient
from .base import ValidationError, handle_tool_errors
from .response_formatter import standardize_response


@handle_tool_errors
async def retrieve_payout(
    client: JustiFiClient,
    payout_id: str,
    sub_account_id: str | None = None,
) -> dict[str, Any]:
    """Retrieve detailed information about a specific payout by ID.

    Use this to get complete details about funds transferred to a merchant's bank account,
    including the payout amount, status, timing, and the transactions (payments, refunds)
    that contributed to the payout balance. Essential for reconciliation and investigating
    payout discrepancies.

    Related tools:
    - Use `list_payouts` first to find payout IDs
    - Use `get_payout_status` for a quick status check without full details
    - Use `list_balance_transactions` with payout_id filter to see all transactions in this payout

    Args:
        client: JustiFi client instance.
        payout_id: The ID of the payout to retrieve (e.g., 'po_ABC123XYZ').
            Obtain this from `list_payouts` or webhook events.
        sub_account_id: Optional sub-account ID. Overrides the default
            platform_account_id if provided.

    Returns:
        Payout object containing:
        - id: Unique payout identifier
        - status: Payout state (scheduled, in_transit, paid, failed, forwarded, canceled)
        - amount: Net amount transferred in cents (after fees)
        - currency: Three-letter ISO currency code
        - bank_account: Destination bank account details (masked account number)
        - arrival_date: Expected or actual deposit date (ISO 8601)
        - created_at: When the payout was initiated

    Raises:
        ValidationError: If payout_id is empty or invalid.
        ToolError: For API errors (wrapped from httpx.HTTPStatusError).
    """
    if not payout_id or not payout_id.strip():
        raise ValidationError(
            "payout_id cannot be empty", field="payout_id", value=payout_id
        )

    result = await client.request(
        "GET", f"/v1/payouts/{payout_id}", sub_account_id=sub_account_id
    )
    return standardize_response(result, "retrieve_payout")


@handle_tool_errors
async def list_payouts(
    client: JustiFiClient,
    limit: int = 25,
    after_cursor: str | None = None,
    before_cursor: str | None = None,
    sub_account_id: str | None = None,
) -> dict[str, Any]:
    """List payouts with cursor-based pagination.

    Use this to view the history of fund transfers to merchant bank accounts. Payouts
    represent the movement of collected payment funds (minus fees and refunds) from
    JustiFi to the merchant's bank. Useful for financial reconciliation and tracking
    deposit history.

    Pagination: Use `page_info.end_cursor` as `after_cursor` to fetch subsequent pages.

    Related tools:
    - Use `retrieve_payout` with a payout ID for complete details
    - Use `get_recent_payouts` for a quick view of the latest payouts
    - Use `list_balance_transactions` to see the transactions that make up each payout

    Args:
        client: JustiFi client instance.
        limit: Number of payouts to return per page (1-100, default: 25).
        after_cursor: Pagination cursor for fetching the next page of results.
        before_cursor: Pagination cursor for fetching the previous page of results.
        sub_account_id: Optional sub-account ID. Overrides the default
            platform_account_id if provided.

    Returns:
        Object containing:
        - data: Array of payout objects with id, status, amount, arrival_date
        - page_info: Pagination metadata for navigating through results

    Raises:
        ValidationError: If limit is invalid or cursors are both provided.
        ToolError: For API errors (wrapped from httpx.HTTPStatusError).
    """
    # Validation
    if limit < 1 or limit > 100:
        raise ValidationError(
            "limit must be between 1 and 100", field="limit", value=limit
        )

    if after_cursor and before_cursor:
        raise ValidationError("Cannot specify both after_cursor and before_cursor")

    params: dict[str, Any] = {"limit": limit}
    if after_cursor:
        params["after_cursor"] = after_cursor
    if before_cursor:
        params["before_cursor"] = before_cursor

    result = await client.request(
        "GET", "/v1/payouts", params=params, sub_account_id=sub_account_id
    )
    return standardize_response(result, "list_payouts")


@handle_tool_errors
async def get_payout_status(
    client: JustiFiClient,
    payout_id: str,
    sub_account_id: str | None = None,
) -> str:
    """Get the current status of a specific payout.

    Use this for quick status checks when you only need to know the payout state,
    not full details. Ideal for monitoring payout progress or building status
    dashboards. For complete payout information, use `retrieve_payout` instead.

    Payout lifecycle: scheduled → in_transit → paid (or failed/canceled/forwarded)

    Related tools:
    - Use `retrieve_payout` when you need full payout details beyond status
    - Use `list_payouts` to find payout IDs

    Args:
        client: JustiFi client instance.
        payout_id: The ID of the payout to check (e.g., 'po_ABC123XYZ').
        sub_account_id: Optional sub-account ID. Overrides the default
            platform_account_id if provided.

    Returns:
        Status string: 'scheduled' (queued), 'in_transit' (sent to bank),
        'paid' (deposited), 'failed' (rejected), 'forwarded', or 'canceled'.

    Raises:
        ValidationError: If payout_id is empty or invalid.
        ToolError: For API errors or missing response fields.
    """
    payout_data = await retrieve_payout(
        client, payout_id, sub_account_id=sub_account_id
    )

    try:
        status: str = payout_data["data"]["status"]
        return status
    except KeyError as e:
        raise KeyError(f"Payout response missing expected field: {e}") from e


@handle_tool_errors
async def get_recent_payouts(
    client: JustiFiClient,
    limit: int = 10,
    sub_account_id: str | None = None,
) -> dict[str, Any]:
    """Get the most recent payouts for a quick overview.

    Use this for dashboards or quick checks on recent payout activity. Returns the
    latest payouts without requiring pagination. For browsing complete payout history,
    use `list_payouts` instead.

    Related tools:
    - Use `list_payouts` for paginated access to full payout history
    - Use `retrieve_payout` to get complete details on a specific payout

    Args:
        client: JustiFi client instance.
        limit: Number of recent payouts to return (1-25, default: 10).
            Keep this small for overview displays; use `list_payouts` for larger queries.
        sub_account_id: Optional sub-account ID. Overrides the default
            platform_account_id if provided.

    Returns:
        Object containing:
        - payouts: Array of recent payout objects with id, status, amount, arrival_date
        - count: Number of payouts returned
        - limit: The limit that was applied

    Raises:
        ValidationError: If limit is invalid.
        ToolError: For API errors or missing response fields.
    """
    if limit < 1 or limit > 25:
        raise ValidationError(
            "limit must be between 1 and 25 for recent payouts",
            field="limit",
            value=limit,
        )

    response = await list_payouts(client, limit=limit, sub_account_id=sub_account_id)

    try:
        payouts_data: list[dict[str, Any]] = response["data"]
        result = {"payouts": payouts_data, "count": len(payouts_data), "limit": limit}
        return standardize_response(result, "get_recent_payouts")
    except KeyError as e:
        raise KeyError(f"Payouts response missing expected field: {e}") from e
