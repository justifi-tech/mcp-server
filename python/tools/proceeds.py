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
    """Retrieve a proceed by its ID.

    Args:
        client: JustiFi client instance.
        proceed_id: The ID of the proceed to retrieve (e.g., 'pr_ABC123XYZ').

    Returns:
        JSON response from the JustiFi API with proceed details.

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
    """List proceeds with cursor-based pagination.

    Args:
        client: JustiFi client instance.
        limit: Number of proceeds to return (default: 25, max: 100).
        after_cursor: Cursor for pagination (get proceeds after this cursor).
        before_cursor: Cursor for pagination (get proceeds before this cursor).

    Returns:
        JSON response with proceeds list from the JustiFi API.

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
