"""
JustiFi Proceed Tools - Framework-Agnostic Business Logic

Pure business logic for proceed operations, separated from any specific
framework (MCP, LangChain, etc.). These functions return raw Python data
structures and can be used by any framework adapter.
"""

from __future__ import annotations

from typing import Any

from ..core import JustiFiClient
from .base import ValidationError, handle_tool_errors
from .response_formatter import standardize_response


@handle_tool_errors
async def retrieve_proceed(client: JustiFiClient, proceed_id: str) -> dict[str, Any]:
    """Retrieve detailed information about a specific proceed (platform revenue record).

    Use this to get complete details about platform fee revenue. Proceeds represent
    the platform's share of payment processing—the fees you collect on transactions
    processed through your sub accounts. Essential for platform revenue reporting
    and reconciliation.

    Related tools:
    - Use `list_proceeds` first to find proceed IDs
    - Use `retrieve_payment` to see the original payment this proceed came from
    - Use `retrieve_payout` to see when this proceed was paid out to your platform

    Args:
        client: JustiFi client instance.
        proceed_id: The ID of the proceed to retrieve (e.g., 'prc_ABC123XYZ').
            Obtain from `list_proceeds` or webhook events.

    Returns:
        Proceed object containing:
        - id: Unique proceed identifier
        - amount: Platform fee amount in cents
        - currency: Three-letter ISO currency code
        - payment_id: The payment this proceed originated from
        - sub_account_id: The merchant who processed the payment
        - status: Proceed state (pending, available, paid_out)
        - payout_id: ID of the payout this proceed was included in (if paid out)
        - created_at: ISO 8601 timestamp

    Raises:
        ValidationError: If proceed_id is empty or invalid.
        ToolError: For API errors (wrapped from httpx.HTTPStatusError).
    """
    if not proceed_id or not proceed_id.strip():
        raise ValidationError(
            "proceed_id cannot be empty", field="proceed_id", value=proceed_id
        )

    result = await client.request("GET", f"/v1/proceeds/{proceed_id}")
    return standardize_response(result, "retrieve_proceed")


@handle_tool_errors
async def list_proceeds(
    client: JustiFiClient,
    limit: int = 25,
    after_cursor: str | None = None,
    before_cursor: str | None = None,
) -> dict[str, Any]:
    """List platform fee proceeds with cursor-based pagination.

    Use this to view your platform's revenue from payment processing fees. Proceeds
    are created automatically when payments are processed through your sub accounts—
    they represent your platform's cut of each transaction. Essential for revenue
    tracking, financial reporting, and reconciling platform earnings.

    Pagination: Use `page_info.end_cursor` as `after_cursor` to fetch subsequent pages.

    Related tools:
    - Use `retrieve_proceed` with a proceed ID for complete details
    - Use `list_payments` to see the payments that generated these proceeds
    - Use `list_payouts` to see when proceeds were paid out to your platform account

    Args:
        client: JustiFi client instance.
        limit: Number of proceeds to return per page (1-100, default: 25).
        after_cursor: Pagination cursor for fetching the next page of results.
        before_cursor: Pagination cursor for fetching the previous page of results.

    Returns:
        Object containing:
        - data: Array of proceed objects with id, amount, payment_id, sub_account_id, status
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

    result = await client.request("GET", "/v1/proceeds", params=params)
    return standardize_response(result, "list_proceeds")
