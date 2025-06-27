"""JustiFi MCP Integration - Payout Tools

Tools for managing payouts (fund transfers) in JustiFi.
Focus on payout operations for evaluation and testing.
"""

from __future__ import annotations

from typing import Any

from langsmith import traceable

from .core import JustiFiClient


@traceable
async def retrieve_payout(client: JustiFiClient, payout_id: str) -> dict[str, Any]:
    """Retrieve a payout by its ID.

    Args:
        client: JustiFi client instance.
        payout_id: The ID of the payout to retrieve.

    Returns:
        JSON response from the JustiFi API with payout details.

    Raises:
        ValueError: If payout_id is empty or invalid.
        httpx.HTTPStatusError: For API errors.

    """
    if not payout_id or not payout_id.strip():
        raise ValueError("payout_id cannot be empty")

    return await client.request("GET", f"/payouts/{payout_id}")


@traceable
async def list_payouts(
    client: JustiFiClient,
    limit: int = 25,
    after_cursor: str | None = None,
    before_cursor: str | None = None,
) -> dict[str, Any]:
    """List payouts with cursor-based pagination.

    Args:
        limit: Number of payouts to return (default: 25, max: 100).
        after_cursor: Cursor for pagination (get payouts after this cursor).
        before_cursor: Cursor for pagination (get payouts before this cursor).
        client: JustiFi client instance.

    Returns:
        JSON response with payouts list from the JustiFi API.

    Raises:
        ValueError: If limit is invalid or cursors are both provided.
        httpx.HTTPStatusError: For API errors.

    """
    # Validation
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")

    if after_cursor and before_cursor:
        raise ValueError("Cannot specify both after_cursor and before_cursor")

    params: dict[str, Any] = {"limit": limit}
    if after_cursor:
        params["after_cursor"] = after_cursor
    if before_cursor:
        params["before_cursor"] = before_cursor

    return await client.request("GET", "/payouts", params=params)


@traceable
async def get_payout_status(client: JustiFiClient, payout_id: str) -> str:
    """Get the status of a specific payout.

    Args:
        client: JustiFi client instance.
        payout_id: The ID of the payout to check.

    Returns:
        The status string of the payout (e.g., 'pending', 'completed', 'failed').

    Raises:
        ValueError: If payout_id is empty or invalid.
        httpx.HTTPStatusError: For API errors.
        KeyError: If the response doesn't contain expected status field.

    """
    payout_data = await retrieve_payout(client, payout_id)

    try:
        status: str = payout_data["data"]["status"]
        return status
    except KeyError as e:
        raise KeyError(f"Payout response missing expected field: {e}") from e


@traceable
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
        ValueError: If limit is invalid.
        httpx.HTTPStatusError: For API errors.

    """
    if limit < 1 or limit > 25:
        raise ValueError("limit must be between 1 and 25 for recent payouts")

    response = await list_payouts(client, limit=limit)

    try:
        payouts_data: list[dict[str, Any]] = response["data"]
        return payouts_data
    except KeyError as e:
        raise KeyError(f"Payouts response missing expected field: {e}") from e
