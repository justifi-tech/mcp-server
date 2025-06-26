"""JustiFi MCP Integration - Payout Tools

Tools for managing payouts (fund transfers) in JustiFi.
"""

from __future__ import annotations

from typing import Any

from langsmith import traceable

from .core import _request


@traceable
async def retrieve_payout(payout_id: str) -> dict[str, Any]:
    """Retrieve a payout by its ID.

    Args:
        payout_id: The ID of the payout to retrieve.

    Returns:
        JSON response from the JustiFi API with payout details.

    """
    return await _request("GET", f"/payouts/{payout_id}")


@traceable
async def list_payouts(
    limit: int = 25,
    after_cursor: str | None = None,
    before_cursor: str | None = None,
) -> dict[str, Any]:
    """List payouts with cursor-based pagination.

    Args:
        limit: Number of payouts to return (default: 25).
        after_cursor: Cursor for pagination (get payouts after this cursor).
        before_cursor: Cursor for pagination (get payouts before this cursor).

    Returns:
        JSON response with payouts list from the JustiFi API.

    """
    params: dict[str, Any] = {"limit": limit}
    if after_cursor:
        params["after_cursor"] = after_cursor
    if before_cursor:
        params["before_cursor"] = before_cursor
    return await _request("GET", "/payouts", params=params)
