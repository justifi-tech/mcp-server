"""
JustiFi Balance Transaction Tools

Tools for retrieving balance transaction information.
"""

from typing import Any

from ..core import JustiFiClient
from .base import ValidationError, handle_tool_errors


@handle_tool_errors
async def list_balance_transactions(
    client: JustiFiClient,
    limit: int = 25,
    after_cursor: str | None = None,
    before_cursor: str | None = None,
    payout_id: str | None = None,
) -> dict[str, Any]:
    """List balance transactions showing money movement affecting the account balance.

    Use this to understand how funds flow through the account. Each balance transaction
    represents an event that changed the available balance: payments add funds, refunds
    and fees subtract funds. Essential for financial reconciliation and understanding
    what transactions are included in each payout.

    Filter by payout_id to see exactly which transactions were bundled into a specific
    payout—critical for reconciling bank deposits.

    Pagination: Use `page_info.end_cursor` as `after_cursor` to fetch subsequent pages.

    Related tools:
    - Use `retrieve_balance_transaction` for complete details on a specific transaction
    - Use `retrieve_payout` to see the payout these transactions contribute to
    - Use `retrieve_payment` or `retrieve_refund` to see the original transaction

    Args:
        client: JustiFi API client
        limit: Number of transactions to return per page (1-100, default: 25).
        after_cursor: Pagination cursor for fetching the next page of results.
        before_cursor: Pagination cursor for fetching the previous page of results.
        payout_id: Filter to show only transactions included in a specific payout.
            Use this for payout reconciliation.

    Returns:
        Object containing:
        - data: Array of balance transaction objects with id, amount, fee, net,
          source_type (payment, refund, dispute, payout), source_id, created_at
        - page_info: Pagination metadata for navigating through results

    Raises:
        ValidationError: If parameters are invalid
        ToolError: For API errors
    """
    # Validation
    if limit < 1 or limit > 100:
        raise ValidationError(
            "limit must be an integer between 1 and 100", field="limit", value=limit
        )

    if after_cursor and before_cursor:
        raise ValidationError("Cannot specify both after_cursor and before_cursor")

    params: dict[str, Any] = {"limit": limit}
    if after_cursor:
        params["after_cursor"] = after_cursor
    if before_cursor:
        params["before_cursor"] = before_cursor
    if payout_id:
        params["payout_id"] = payout_id

    response = await client.request("GET", "/v1/balance_transactions", params=params)
    return response


@handle_tool_errors
async def retrieve_balance_transaction(
    client: JustiFiClient,
    balance_transaction_id: str,
) -> dict[str, Any]:
    """Retrieve detailed information about a specific balance transaction.

    Use this to get complete details about a single balance-affecting event,
    including the gross amount, fees, net amount, and the source transaction
    (payment, refund, etc.) that caused this balance change. Essential for
    investigating specific line items during reconciliation.

    Related tools:
    - Use `list_balance_transactions` first to find transaction IDs
    - Use `retrieve_payment` if source_type is 'payment' to see payment details
    - Use `retrieve_refund` if source_type is 'refund' to see refund details
    - Use `retrieve_payout` to see the payout this transaction belongs to

    Args:
        client: JustiFi API client
        balance_transaction_id: The unique identifier for the balance transaction
            (e.g., 'bt_ABC123XYZ'). Obtain from `list_balance_transactions`.

    Returns:
        Balance transaction object containing:
        - id: Unique balance transaction identifier
        - amount: Gross amount in cents (before fees)
        - fee: Processing fees in cents
        - net: Net amount in cents (amount - fee, added to balance)
        - source_type: What caused this transaction (payment, refund, dispute, payout)
        - source_id: ID of the source object (payment_id, refund_id, etc.)
        - payout_id: ID of the payout this transaction was included in (if paid out)
        - available_on: When funds became/become available
        - created_at: ISO 8601 timestamp

    Raises:
        ValidationError: If balance_transaction_id is invalid
        ToolError: For API errors
    """
    # Validation
    if not balance_transaction_id:
        raise ValidationError("balance_transaction_id must be a non-empty string")

    if isinstance(balance_transaction_id, str) and not balance_transaction_id.strip():
        raise ValidationError(
            "balance_transaction_id cannot be empty or contain only whitespace"
        )

    response = await client.request(
        "GET", f"/v1/balance_transactions/{balance_transaction_id}"
    )
    return response
