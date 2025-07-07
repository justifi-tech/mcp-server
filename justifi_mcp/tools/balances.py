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
    """List balance transactions with pagination support.

    Args:
        client: JustiFi API client
        limit: Number of balance transactions to return (1-100, default: 25)
        after_cursor: Cursor for pagination - returns results after this cursor
        before_cursor: Cursor for pagination - returns results before this cursor
        payout_id: Optional payout ID to filter transactions

    Returns:
        Dict containing balance transactions list and pagination info

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
    """Retrieve a specific balance transaction by ID.

    Args:
        client: JustiFi API client
        balance_transaction_id: The ID of the balance transaction to retrieve

    Returns:
        Dict containing balance transaction details

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
