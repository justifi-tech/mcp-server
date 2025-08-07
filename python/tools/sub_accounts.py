"""
JustiFi Sub Account Tools

Core sub account operations for retrieving and listing sub accounts,
their payout accounts, and settings.
"""

from __future__ import annotations

from typing import Any

from ..core import JustiFiClient
from .base import ToolError, ValidationError


async def list_sub_accounts(
    client: JustiFiClient,
    status: str | None = None,
    limit: int = 25,
    after_cursor: str | None = None,
    before_cursor: str | None = None,
) -> dict[str, Any]:
    """List sub accounts with optional status filtering and pagination.

    Args:
        client: JustiFi API client
        status: Optional status filter - one of: created, submitted, information_needed,
               rejected, approved, enabled, disabled, archived
        limit: Number of sub accounts to return (1-100, default: 25)
        after_cursor: Cursor for pagination - returns results after this cursor
        before_cursor: Cursor for pagination - returns results before this cursor

    Returns:
        Paginated list of sub accounts with page_info for navigation

    Raises:
        ValidationError: If parameters are invalid
        ToolError: If sub account listing fails
    """
    # Validate limit
    if not isinstance(limit, int) or limit < 1 or limit > 100:
        raise ValidationError(
            "limit must be an integer between 1 and 100", field="limit", value=limit
        )

    # Validate status if provided
    valid_statuses = {
        "created", "submitted", "information_needed", "rejected",
        "approved", "enabled", "disabled", "archived"
    }
    if status is not None:
        if not isinstance(status, str):
            raise ValidationError(
                "status must be a string if provided", field="status", value=status
            )
        if status not in valid_statuses:
            raise ValidationError(
                f"status must be one of: {', '.join(sorted(valid_statuses))}",
                field="status",
                value=status,
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

    try:
        # Build query parameters
        params: dict[str, Any] = {"limit": limit}

        if status:
            params["status"] = status
        if after_cursor:
            params["after_cursor"] = after_cursor
        if before_cursor:
            params["before_cursor"] = before_cursor

        # Call JustiFi API to list sub accounts
        result = await client.request("GET", "/v1/sub_accounts", params=params)
        return result

    except Exception as e:
        raise ToolError(
            f"Failed to list sub accounts: {str(e)}", error_type="SubAccountListError"
        ) from e


async def get_sub_account(client: JustiFiClient, sub_account_id: str) -> dict[str, Any]:
    """Get detailed information about a specific sub account by ID.

    Args:
        client: JustiFi API client
        sub_account_id: The unique identifier for the sub account (e.g., 'acc_ABC123XYZ')

    Returns:
        Sub account object with ID, name, status, and other details

    Raises:
        ValidationError: If sub_account_id is invalid
        ToolError: If sub account retrieval fails
    """
    if sub_account_id is None or not isinstance(sub_account_id, str):
        raise ValidationError(
            "sub_account_id is required and must be a non-empty string",
            field="sub_account_id",
            value=sub_account_id,
        )

    if not sub_account_id.strip():
        raise ValidationError(
            "sub_account_id cannot be empty or whitespace",
            field="sub_account_id",
            value=sub_account_id,
        )

    try:
        # Call JustiFi API to retrieve sub account
        result = await client.request("GET", f"/v1/sub_accounts/{sub_account_id}")
        return result

    except Exception as e:
        raise ToolError(
            f"Failed to retrieve sub account {sub_account_id}: {str(e)}",
            error_type="SubAccountRetrievalError",
        ) from e


async def get_sub_account_payout_account(
    client: JustiFiClient, sub_account_id: str
) -> dict[str, Any]:
    """Get information about the currently active payout bank account of a sub account.

    Args:
        client: JustiFi API client
        sub_account_id: The unique identifier for the sub account (e.g., 'acc_ABC123XYZ')

    Returns:
        Payout bank account object with account details

    Raises:
        ValidationError: If sub_account_id is invalid
        ToolError: If payout account retrieval fails
    """
    if sub_account_id is None or not isinstance(sub_account_id, str):
        raise ValidationError(
            "sub_account_id is required and must be a non-empty string",
            field="sub_account_id",
            value=sub_account_id,
        )

    if not sub_account_id.strip():
        raise ValidationError(
            "sub_account_id cannot be empty or whitespace",
            field="sub_account_id",
            value=sub_account_id,
        )

    try:
        # Call JustiFi API to retrieve sub account payout account
        result = await client.request(
            "GET", f"/v1/sub_accounts/{sub_account_id}/payout_account"
        )
        return result

    except Exception as e:
        raise ToolError(
            f"Failed to retrieve payout account for sub account {sub_account_id}: {str(e)}",
            error_type="SubAccountPayoutAccountRetrievalError",
        ) from e


async def get_sub_account_settings(
    client: JustiFiClient, sub_account_id: str
) -> dict[str, Any]:
    """Get information about sub account settings.

    Args:
        client: JustiFi API client
        sub_account_id: The unique identifier for the sub account (e.g., 'acc_ABC123XYZ')

    Returns:
        Sub account settings object

    Raises:
        ValidationError: If sub_account_id is invalid
        ToolError: If sub account settings retrieval fails
    """
    if sub_account_id is None or not isinstance(sub_account_id, str):
        raise ValidationError(
            "sub_account_id is required and must be a non-empty string",
            field="sub_account_id",
            value=sub_account_id,
        )

    if not sub_account_id.strip():
        raise ValidationError(
            "sub_account_id cannot be empty or whitespace",
            field="sub_account_id",
            value=sub_account_id,
        )

    try:
        # Call JustiFi API to retrieve sub account settings
        result = await client.request(
            "GET", f"/v1/sub_accounts/{sub_account_id}/settings"
        )
        return result

    except Exception as e:
        raise ToolError(
            f"Failed to retrieve settings for sub account {sub_account_id}: {str(e)}",
            error_type="SubAccountSettingsRetrievalError",
        ) from e
