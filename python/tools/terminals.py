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
    """List physical payment terminals (card readers) with optional filtering.

    Use this to view and manage physical point-of-sale terminals deployed to merchant
    locations. Terminals are hardware devices that accept card-present payments (tap,
    dip, swipe). Filter by status to find terminals needing attention or by sub_account
    to see terminals for a specific merchant.

    Pagination: Use `page_info.end_cursor` as `after_cursor` to fetch subsequent pages.

    Related tools:
    - Use `retrieve_terminal` with a terminal ID for complete details
    - Use `get_terminal_status` for real-time connectivity status
    - Use `identify_terminal` to make a terminal display its ID (for physical location)
    - Use `update_terminal` to change a terminal's nickname

    Args:
        client: JustiFi API client
        limit: Number of terminals to return per page (1-100, default: 25).
        after_cursor: Pagination cursor for fetching the next page of results.
        before_cursor: Pagination cursor for fetching the previous page of results.
        status: Filter by terminal connectivity state:
            - 'connected': Online and ready for transactions
            - 'disconnected': Offline, cannot process payments
            - 'unknown': Status cannot be determined
            - 'pending_configuration': Newly added, not yet set up
        terminal_id: Filter by specific terminal ID (e.g., 'trm_ABC123').
        provider_id: Filter by hardware provider/device serial number.
        terminal_order_id: Filter by the order ID from terminal purchase.
        sub_account: Filter to show only terminals assigned to a specific merchant.

    Returns:
        Object containing:
        - data: Array of terminal objects with id, status, nickname, provider_id, sub_account_id
        - page_info: Pagination metadata for navigating through results

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
    """Retrieve detailed information about a specific physical payment terminal.

    Use this to get complete details about a terminal including its configuration,
    connectivity status, location assignment, and hardware information. Essential
    for troubleshooting terminal issues or verifying terminal setup.

    Related tools:
    - Use `list_terminals` first to find terminal IDs
    - Use `get_terminal_status` for real-time connectivity check
    - Use `identify_terminal` to make the physical device display its ID
    - Use `update_terminal` to change the terminal's nickname

    Args:
        client: JustiFi API client
        terminal_id: The unique identifier for the terminal (e.g., 'trm_ABC123').
            Obtain from `list_terminals` or your terminal provisioning records.

    Returns:
        Terminal object containing:
        - id: Unique terminal identifier
        - status: Connectivity state (connected, disconnected, unknown, pending_configuration)
        - nickname: Custom display name for easier identification
        - provider_id: Hardware serial number or device ID
        - sub_account_id: Merchant this terminal is assigned to
        - terminal_order_id: Order reference from terminal purchase
        - last_seen_at: Timestamp of last communication with the terminal
        - created_at: When the terminal was registered

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
    """Update a terminal's display nickname for easier identification.

    Use this to set a friendly name for a terminal that helps identify its physical
    location or purpose. For example: 'Front Counter', 'Register 2', or 'Drive-Thru'.
    Nicknames make it easier to manage multiple terminals at the same location.

    Related tools:
    - Use `list_terminals` to see all terminals and their current nicknames
    - Use `retrieve_terminal` to see current terminal properties
    - Use `identify_terminal` to make the physical terminal display its ID

    Args:
        client: JustiFi API client
        terminal_id: The unique identifier for the terminal (e.g., 'trm_ABC123').
        nickname: Custom display name for the terminal (e.g., 'Front Counter', 'Register 2').
            Required for update; use descriptive names indicating location or purpose.

    Returns:
        Updated terminal object containing:
        - id: Unique terminal identifier
        - nickname: The newly set display name
        - status: Current connectivity state
        - updated_at: Timestamp of this update

    Raises:
        ValidationError: If parameters are invalid or nickname not provided
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
    """Get the real-time connectivity status of a physical payment terminal.

    Use this for live status checks to verify a terminal is online and ready to
    accept payments before directing a customer to use it. More current than the
    status in `retrieve_terminal` which may be cached.

    Related tools:
    - Use `retrieve_terminal` for full terminal details (status may be slightly delayed)
    - Use `list_terminals` to find terminal IDs
    - Use `identify_terminal` to physically locate a terminal that's showing as connected

    Args:
        client: JustiFi API client
        terminal_id: The unique identifier for the terminal (e.g., 'trm_ABC123').

    Returns:
        Terminal status object containing:
        - id: Terminal identifier
        - status: Real-time connectivity state (connected, disconnected, unknown)
        - last_seen_at: Timestamp of most recent communication
        - is_ready: Boolean indicating if terminal can accept payments now

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
    """Make a physical terminal display its identification info for 20 seconds.

    Use this to physically locate a specific terminal in a store or warehouse. When
    triggered, the terminal screen displays identifying information (like its ID or
    nickname), making it easy to find among multiple terminals. Essential for
    installation, inventory, or troubleshooting when you need to identify which
    physical device corresponds to a terminal ID in your system.

    Note: The terminal must be connected (online) for this command to work.
    The display automatically returns to normal after 20 seconds.

    Related tools:
    - Use `get_terminal_status` first to verify the terminal is connected
    - Use `list_terminals` to find terminal IDs
    - Use `update_terminal` to set a memorable nickname for easier future identification

    Args:
        client: JustiFi API client
        terminal_id: The unique identifier for the terminal (e.g., 'trm_ABC123').
            The terminal must be online (status: connected) to respond.

    Returns:
        Confirmation object containing:
        - success: Boolean indicating the identify command was sent
        - terminal_id: The terminal that was triggered
        - message: Description of what was displayed

    Raises:
        ValidationError: If terminal_id is invalid
        ToolError: If identify request fails (e.g., terminal is offline)
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
