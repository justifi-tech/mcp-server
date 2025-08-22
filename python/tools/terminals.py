"""
JustiFi Terminal Management Tools

Core terminal operations for listing, retrieving, updating, checking status, and identifying terminals.
"""

from __future__ import annotations

from typing import Any

from ..core import JustiFiClient
from .base import ToolError, ValidationError
from .response_formatter import standardize_response


async def list_terminals(
    client: JustiFiClient,
    limit: int = 25,
    after_cursor: str | None = None,
    before_cursor: str | None = None,
    status: str | None = None,
    terminal_id: str | None = None,
    provider_id: str | None = None,
    terminal_order_id: str | None = None,
    sub_account: str | None = None,
) -> dict[str, Any]:
    """List terminals with optional filtering and pagination.

    Args:
        client: JustiFi API client
        limit: Number of terminals to return (1-100, default: 25)
        after_cursor: Cursor for pagination - returns results after this cursor
        before_cursor: Cursor for pagination - returns results before this cursor
        status: Filter by terminal status (connected, disconnected, unknown, pending_configuration)
        terminal_id: Filter by specific terminal ID
        provider_id: Filter by provider/device ID
        terminal_order_id: Filter by terminal order ID
        sub_account: Sub account ID for filtering

    Returns:
        Paginated list of terminals with page_info for navigation

    Raises:
        ValidationError: If parameters are invalid
        ToolError: If terminal listing fails
    """
    # Validate limit
    if not isinstance(limit, int) or limit < 1 or limit > 100:
        raise ValidationError(
            "limit must be an integer between 1 and 100", field="limit", value=limit
        )

    # Validate cursors (if provided)
    if after_cursor is not None and not isinstance(after_cursor, str):
        raise ValidationError(
            "after_cursor must be a string if provided",
            field="after_cursor",
            value=after_cursor,
        )

    if before_cursor is not None and not isinstance(before_cursor, str):
        raise ValidationError(
            "before_cursor must be a string if provided",
            field="before_cursor",
            value=before_cursor,
        )

    # Cannot use both cursors at the same time
    if after_cursor and before_cursor:
        raise ValidationError(
            "Cannot specify both after_cursor and before_cursor",
            field="cursors",
            value={"after_cursor": after_cursor, "before_cursor": before_cursor},
        )

    # Validate status filter (if provided)
    if status is not None:
        valid_statuses = [
            "connected",
            "disconnected",
            "unknown",
            "pending_configuration",
        ]
        if status not in valid_statuses:
            raise ValidationError(
                f"status must be one of {valid_statuses}",
                field="status",
                value=status,
            )

    # Validate string parameters (if provided)
    for param_name, param_value in [
        ("terminal_id", terminal_id),
        ("provider_id", provider_id),
        ("terminal_order_id", terminal_order_id),
        ("sub_account", sub_account),
    ]:
        if param_value is not None and not isinstance(param_value, str):
            raise ValidationError(
                f"{param_name} must be a string if provided",
                field=param_name,
                value=param_value,
            )

    try:
        # Build query parameters
        params: dict[str, Any] = {"limit": limit}

        if after_cursor:
            params["after_cursor"] = after_cursor
        if before_cursor:
            params["before_cursor"] = before_cursor
        if status:
            params["status"] = status
        if terminal_id:
            params["terminal_id"] = terminal_id
        if provider_id:
            params["provider_id"] = provider_id
        if terminal_order_id:
            params["terminal_order_id"] = terminal_order_id
        if sub_account:
            params["sub_account"] = sub_account

        # Call JustiFi API to list terminals
        result = await client.request("GET", "/v1/terminals", params=params)
        return standardize_response(result, "list_terminals")

    except Exception as e:
        raise ToolError(
            f"Failed to list terminals: {str(e)}", error_type="TerminalListError"
        ) from e


async def retrieve_terminal(client: JustiFiClient, terminal_id: str) -> dict[str, Any]:
    """Retrieve detailed information about a specific terminal by ID.

    Args:
        client: JustiFi API client
        terminal_id: The unique identifier for the terminal (e.g., 'trm_abc123')

    Returns:
        Terminal object with ID, status, provider info, and details

    Raises:
        ValidationError: If terminal_id is invalid
        ToolError: If terminal retrieval fails
    """
    if not terminal_id or not isinstance(terminal_id, str):
        raise ValidationError(
            "terminal_id is required and must be a non-empty string",
            field="terminal_id",
            value=terminal_id,
        )

    if not terminal_id.strip():
        raise ValidationError(
            "terminal_id cannot be empty or whitespace",
            field="terminal_id",
            value=terminal_id,
        )

    try:
        # Call JustiFi API to retrieve terminal
        result = await client.request("GET", f"/v1/terminals/{terminal_id}")
        return standardize_response(result, "retrieve_terminal")

    except Exception as e:
        raise ToolError(
            f"Failed to retrieve terminal {terminal_id}: {str(e)}",
            error_type="TerminalRetrievalError",
        ) from e


async def update_terminal(
    client: JustiFiClient,
    terminal_id: str,
    nickname: str | None = None,
) -> dict[str, Any]:
    """Update terminal properties (primarily nickname).

    Args:
        client: JustiFi API client
        terminal_id: The unique identifier for the terminal (e.g., 'trm_abc123')
        nickname: Custom terminal nickname

    Returns:
        Updated terminal object

    Raises:
        ValidationError: If parameters are invalid
        ToolError: If terminal update fails
    """
    if not terminal_id or not isinstance(terminal_id, str):
        raise ValidationError(
            "terminal_id is required and must be a non-empty string",
            field="terminal_id",
            value=terminal_id,
        )

    if not terminal_id.strip():
        raise ValidationError(
            "terminal_id cannot be empty or whitespace",
            field="terminal_id",
            value=terminal_id,
        )

    if nickname is not None and not isinstance(nickname, str):
        raise ValidationError(
            "nickname must be a string if provided",
            field="nickname",
            value=nickname,
        )

    # Ensure we have at least one field to update
    if nickname is None:
        raise ValidationError(
            "At least one field must be provided to update",
            field="update_fields",
            value={"nickname": nickname},
        )

    try:
        # Build update payload
        payload: dict[str, Any] = {}
        if nickname is not None:
            payload["nickname"] = nickname

        # Call JustiFi API to update terminal
        result = await client.request(
            "PATCH", f"/v1/terminals/{terminal_id}", data=payload
        )
        return standardize_response(result, "update_terminal")

    except Exception as e:
        raise ToolError(
            f"Failed to update terminal {terminal_id}: {str(e)}",
            error_type="TerminalUpdateError",
        ) from e


async def get_terminal_status(
    client: JustiFiClient, terminal_id: str
) -> dict[str, Any]:
    """Get real-time terminal status.

    Args:
        client: JustiFi API client
        terminal_id: The unique identifier for the terminal (e.g., 'trm_abc123')

    Returns:
        Terminal status object with current status information

    Raises:
        ValidationError: If terminal_id is invalid
        ToolError: If status retrieval fails
    """
    if not terminal_id or not isinstance(terminal_id, str):
        raise ValidationError(
            "terminal_id is required and must be a non-empty string",
            field="terminal_id",
            value=terminal_id,
        )

    if not terminal_id.strip():
        raise ValidationError(
            "terminal_id cannot be empty or whitespace",
            field="terminal_id",
            value=terminal_id,
        )

    try:
        # Call JustiFi API to get terminal status
        result = await client.request("GET", f"/v1/terminals/{terminal_id}/status")
        return standardize_response(result, "get_terminal_status")

    except Exception as e:
        raise ToolError(
            f"Failed to get status for terminal {terminal_id}: {str(e)}",
            error_type="TerminalStatusError",
        ) from e


async def identify_terminal(client: JustiFiClient, terminal_id: str) -> dict[str, Any]:
    """Display identification information on terminal screen for 20 seconds.

    Args:
        client: JustiFi API client
        terminal_id: The unique identifier for the terminal (e.g., 'trm_abc123')

    Returns:
        Confirmation that the identify request was sent to the terminal

    Raises:
        ValidationError: If terminal_id is invalid
        ToolError: If identify request fails
    """
    if not terminal_id or not isinstance(terminal_id, str):
        raise ValidationError(
            "terminal_id is required and must be a non-empty string",
            field="terminal_id",
            value=terminal_id,
        )

    if not terminal_id.strip():
        raise ValidationError(
            "terminal_id cannot be empty or whitespace",
            field="terminal_id",
            value=terminal_id,
        )

    try:
        # Call JustiFi API to identify terminal
        result = await client.request("POST", f"/v1/terminals/{terminal_id}/identify")
        return standardize_response(result, "identify_terminal")

    except Exception as e:
        raise ToolError(
            f"Failed to identify terminal {terminal_id}: {str(e)}",
            error_type="TerminalIdentifyError",
        ) from e
