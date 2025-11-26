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
    """List sub accounts (merchants) on your platform with optional filtering.

    Use this to view and manage merchants onboarded to your platform. Sub accounts
    represent individual businesses that process payments through your JustiFi platform
    account. Filter by status to find accounts needing attention (information_needed)
    or ready to process (enabled).

    Sub account lifecycle: created → submitted → enabled/rejected/information_needed

    Pagination: Use `page_info.end_cursor` as `after_cursor` to fetch subsequent pages.

    Related tools:
    - Use `get_sub_account` with an account ID for complete details
    - Use `get_sub_account_payout_account` to see their bank account for payouts
    - Use `get_sub_account_settings` to view their configuration

    Args:
        client: JustiFi API client
        status: Filter by onboarding/account state:
            - 'created': Account created, application not started
            - 'submitted': Application submitted, under review
            - 'information_needed': Additional information required
            - 'rejected': Application denied
            - 'enabled': Active and can process payments
            - 'disabled': Temporarily unable to process
            - 'archived': Account closed
        limit: Number of sub accounts to return per page (1-100, default: 25).
        after_cursor: Pagination cursor for fetching the next page of results.
        before_cursor: Pagination cursor for fetching the previous page of results.

    Returns:
        Object containing:
        - data: Array of sub account objects with id, name, status, created_at
        - page_info: Pagination metadata for navigating through results

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
        "created",
        "submitted",
        "information_needed",
        "rejected",
        "approved",
        "enabled",
        "disabled",
        "archived",
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
    """Retrieve detailed information about a specific sub account (merchant).

    Use this to get complete details about a merchant on your platform, including
    their business information, onboarding status, and processing capabilities.
    Essential for customer support, compliance checks, and monitoring merchant health.

    Related tools:
    - Use `list_sub_accounts` first to find sub account IDs
    - Use `get_sub_account_payout_account` to see their linked bank account
    - Use `get_sub_account_settings` to view their configuration
    - Use `list_payments` filtered by sub_account to see their transactions

    Args:
        client: JustiFi API client
        sub_account_id: The unique identifier for the sub account (e.g., 'acc_ABC123XYZ').
            Obtain from `list_sub_accounts` or your onboarding records.

    Returns:
        Sub account object containing:
        - id: Unique sub account identifier
        - name: Business name
        - status: Account state (created, submitted, enabled, disabled, etc.)
        - platform_account_id: Your platform's account ID
        - business_details: Legal name, address, tax ID (masked)
        - processing_capabilities: What payment types they can accept
        - created_at: ISO 8601 timestamp

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
    """Get the linked bank account where a sub account receives payouts.

    Use this to view the bank account configured for a merchant's payouts. Shows
    masked account details for security. Essential for verifying payout destination
    or troubleshooting payout delivery issues.

    Related tools:
    - Use `get_sub_account` for general merchant information
    - Use `list_payouts` to see actual payouts sent to this account
    - Use `get_sub_account_settings` for other configuration details

    Args:
        client: JustiFi API client
        sub_account_id: The unique identifier for the sub account (e.g., 'acc_ABC123XYZ').
            Obtain from `list_sub_accounts`.

    Returns:
        Payout bank account object containing:
        - id: Bank account identifier
        - bank_name: Name of the financial institution
        - account_type: 'checking' or 'savings'
        - account_number_last4: Last 4 digits of account number
        - routing_number: Bank routing number (may be partially masked)
        - account_owner_name: Name on the bank account
        - is_active: Whether this is the current payout destination

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
    """Get configuration settings for a specific sub account.

    Use this to view a merchant's processing settings including payout schedule,
    statement descriptor, and enabled features. Helpful for understanding how
    a merchant's account is configured or troubleshooting processing issues.

    Related tools:
    - Use `get_sub_account` for general merchant information and status
    - Use `get_sub_account_payout_account` to see their bank account

    Args:
        client: JustiFi API client
        sub_account_id: The unique identifier for the sub account (e.g., 'acc_ABC123XYZ').
            Obtain from `list_sub_accounts`.

    Returns:
        Sub account settings object containing:
        - payout_schedule: How often payouts are sent (daily, weekly, monthly)
        - statement_descriptor: Text that appears on customer card statements
        - card_payments_enabled: Whether card processing is active
        - ach_payments_enabled: Whether bank transfer processing is active
        - additional configuration specific to the account

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
