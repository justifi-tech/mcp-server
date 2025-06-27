"""JustiFi MCP Integration - Payout Tools

Tools for managing payouts (fund transfers) in JustiFi.
Focus on payout operations for evaluation and testing.
"""

from __future__ import annotations

from typing import Any

from langsmith import traceable

from .core import JustiFiClient, _request


@traceable
async def retrieve_payout(
    payout_id: str, client: JustiFiClient | None = None
) -> dict[str, Any]:
    """Retrieve a payout by its ID.

    Args:
        payout_id: The ID of the payout to retrieve.
        client: Optional JustiFi client instance (uses default if not provided).

    Returns:
        JSON response from the JustiFi API with payout details.

    Raises:
        ValueError: If payout_id is empty or invalid.
        httpx.HTTPStatusError: For API errors.

    """
    if not payout_id or not payout_id.strip():
        raise ValueError("payout_id cannot be empty")

    if client:
        return await client.request("GET", f"/payouts/{payout_id}")
    # Use legacy function for backward compatibility
    return await _request("GET", f"/payouts/{payout_id}")


@traceable
async def list_payouts(
    limit: int = 25,
    after_cursor: str | None = None,
    before_cursor: str | None = None,
    client: JustiFiClient | None = None,
) -> dict[str, Any]:
    """List payouts with cursor-based pagination.

    Args:
        limit: Number of payouts to return (default: 25, max: 100).
        after_cursor: Cursor for pagination (get payouts after this cursor).
        before_cursor: Cursor for pagination (get payouts before this cursor).
        client: Optional JustiFi client instance (uses default if not provided).

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

    if client:
        return await client.request("GET", "/payouts", params=params)
    # Use legacy function for backward compatibility
    return await _request("GET", "/payouts", params=params)


@traceable
async def get_payout_status(payout_id: str, client: JustiFiClient | None = None) -> str:
    """Get the status of a specific payout.

    Args:
        payout_id: The ID of the payout to check.
        client: Optional JustiFi client instance.

    Returns:
        The status string of the payout (e.g., 'pending', 'completed', 'failed').

    Raises:
        ValueError: If payout_id is empty or invalid.
        httpx.HTTPStatusError: For API errors.
        KeyError: If the response doesn't contain expected status field.

    """
    payout_data = await retrieve_payout(payout_id, client)

    try:
        status: str = payout_data["data"]["status"]
        return status
    except KeyError as e:
        raise KeyError(f"Payout response missing expected field: {e}") from e


@traceable
async def get_recent_payouts(
    limit: int = 10, client: JustiFiClient | None = None
) -> list[dict[str, Any]]:
    """Get the most recent payouts.

    Args:
        limit: Number of recent payouts to return (default: 10, max: 25).
        client: Optional JustiFi client instance.

    Returns:
        List of payout data dictionaries.

    Raises:
        ValueError: If limit is invalid.
        httpx.HTTPStatusError: For API errors.

    """
    if limit < 1 or limit > 25:
        raise ValueError("limit must be between 1 and 25 for recent payouts")

    response = await list_payouts(limit=limit, client=client)

    try:
        payouts_data: list[dict[str, Any]] = response["data"]
        return payouts_data
    except KeyError as e:
        raise KeyError(f"Payouts response missing expected field: {e}") from e
