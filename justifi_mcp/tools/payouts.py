"""
JustiFi Payout Tools - Framework-Agnostic Business Logic

Pure business logic for payout operations, separated from any specific
framework (MCP, LangChain, etc.). These functions return raw Python data
structures and can be used by any framework adapter.
"""

from __future__ import annotations

from typing import Any

from langsmith import traceable

from ..core import JustiFiClient
from .base import ValidationError, handle_tool_errors


@traceable
@handle_tool_errors
async def retrieve_payout(client: JustiFiClient, payout_id: str) -> dict[str, Any]:
    """Retrieve a payout by its ID.

    Args:
        client: JustiFi client instance.
        payout_id: The ID of the payout to retrieve (e.g., 'po_ABC123XYZ').

    Returns:
        JSON response from the JustiFi API with payout details.

    Raises:
        ValidationError: If payout_id is empty or invalid.
        ToolError: For API errors (wrapped from httpx.HTTPStatusError).
    """
    if not payout_id or not payout_id.strip():
        raise ValidationError(
            "payout_id cannot be empty", field="payout_id", value=payout_id
        )

    return await client.request("GET", f"/payouts/{payout_id}")


@traceable
@handle_tool_errors
async def list_payouts(
    client: JustiFiClient,
    limit: int = 25,
    after_cursor: str | None = None,
    before_cursor: str | None = None,
) -> dict[str, Any]:
    """List payouts with cursor-based pagination.

    Args:
        client: JustiFi client instance.
        limit: Number of payouts to return (default: 25, max: 100).
        after_cursor: Cursor for pagination (get payouts after this cursor).
        before_cursor: Cursor for pagination (get payouts before this cursor).

    Returns:
        JSON response with payouts list from the JustiFi API.

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

    return await client.request("GET", "/payouts", params=params)


@traceable
@handle_tool_errors
async def get_payout_status(client: JustiFiClient, payout_id: str) -> str:
    """Get the status of a specific payout.

    Args:
        client: JustiFi client instance.
        payout_id: The ID of the payout to check status for (e.g., 'po_ABC123XYZ').

    Returns:
        The status string of the payout (e.g., 'pending', 'completed', 'failed').

    Raises:
        ValidationError: If payout_id is empty or invalid.
        ToolError: For API errors or missing response fields.
    """
    payout_data = await retrieve_payout(client, payout_id)

    try:
        status: str = payout_data["data"]["status"]
        return status
    except KeyError as e:
        raise KeyError(f"Payout response missing expected field: {e}") from e


@traceable
@handle_tool_errors
async def get_recent_payouts(
    client: JustiFiClient, limit: int = 10
) -> list[dict[str, Any]]:
    """Get the most recent payouts.

    Args:
        client: JustiFi client instance.
        limit: Number of recent payouts to return (default: 10, max: 25).

    Returns:
        List of payout data dictionaries.

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

    response = await list_payouts(client, limit=limit)

    try:
        payouts_data: list[dict[str, Any]] = response["data"]
        return payouts_data
    except KeyError as e:
        raise KeyError(f"Payouts response missing expected field: {e}") from e
