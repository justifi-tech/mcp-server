"""
JustiFi Dispute Tools - Framework-Agnostic Business Logic

Pure business logic for dispute operations, separated from any specific
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
async def list_disputes(
    client: JustiFiClient,
    limit: int = 25,
    after_cursor: str | None = None,
    before_cursor: str | None = None,
) -> dict[str, Any]:
    """List disputes with cursor-based pagination.

    Args:
        client: JustiFi client instance.
        limit: Number of disputes to return (default: 25, max: 100).
        after_cursor: Cursor for pagination (get disputes after this cursor).
        before_cursor: Cursor for pagination (get disputes before this cursor).

    Returns:
        JSON response with disputes list from the JustiFi API.

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

    return await client.request("GET", "/v1/disputes", params=params)


@traceable
@handle_tool_errors
async def retrieve_dispute(client: JustiFiClient, dispute_id: str) -> dict[str, Any]:
    """Retrieve a dispute by its ID.

    Args:
        client: JustiFi client instance.
        dispute_id: The ID of the dispute to retrieve (e.g., 'dp_ABC123XYZ').

    Returns:
        JSON response from the JustiFi API with dispute details.

    Raises:
        ValidationError: If dispute_id is empty or invalid.
        ToolError: For API errors (wrapped from httpx.HTTPStatusError).
    """
    if not dispute_id or not dispute_id.strip():
        raise ValidationError(
            "dispute_id cannot be empty", field="dispute_id", value=dispute_id
        )

    return await client.request("GET", f"/v1/disputes/{dispute_id}")
