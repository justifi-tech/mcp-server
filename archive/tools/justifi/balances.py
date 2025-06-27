"""JustiFi MCP Integration - Balance Tools

Tools for retrieving account balance information from JustiFi.
"""

from __future__ import annotations

from typing import Any

from langsmith import traceable

from .core import _request


@traceable
async def list_balance_transactions(
    limit: int = 25,
    after_cursor: str | None = None,
    before_cursor: str | None = None,
) -> dict[str, Any]:
    """List balance transactions for the account.

    Args:
        limit: Number of balance transactions to return (default: 25).
        after_cursor: Cursor for pagination (get transactions after this cursor).
        before_cursor: Cursor for pagination (get transactions before this cursor).

    Returns:
        JSON response from the JustiFi API with balance transactions list.

    """
    params: dict[str, Any] = {"limit": limit}
    if after_cursor:
        params["after_cursor"] = after_cursor
    if before_cursor:
        params["before_cursor"] = before_cursor
    return await _request("GET", "/balance_transactions", params=params)
