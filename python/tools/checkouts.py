"""
JustiFi Checkout Tools - Framework-Agnostic Business Logic

Pure business logic for checkout operations, separated from any specific
framework (MCP, LangChain, etc.). These functions return raw Python data
structures and can be used by any framework adapter.
"""

from __future__ import annotations

from typing import Any

from ..core import JustiFiClient
from .base import ValidationError, handle_tool_errors


@handle_tool_errors
async def list_checkouts(
    client: JustiFiClient,
    limit: int = 25,
    after_cursor: str | None = None,
    before_cursor: str | None = None,
    payment_mode: str | None = None,
    status: str | None = None,
    payment_status: str | None = None,
    sub_account_id: str | None = None,
) -> dict[str, Any]:
    """List checkout sessions with filtering and cursor-based pagination.

    Use this to view checkout sessions created for customers. Checkouts are hosted
    payment pages that securely collect payment information. Filter by status to
    find abandoned checkouts (created/attempted) or successful ones (completed).

    Checkout lifecycle: created → attempted (customer started) → completed/expired

    Pagination: Use `page_info.end_cursor` as `after_cursor` to fetch subsequent pages.

    Related tools:
    - Use `retrieve_checkout` with a checkout ID for complete details
    - Use `retrieve_payment` to see the payment created by a completed checkout
    - Use `generate_unified_checkout_integration` for integration code examples

    Args:
        client: JustiFi client instance.
        limit: Number of checkouts to return per page (1-100, default: 25).
        after_cursor: Pagination cursor for fetching the next page of results.
        before_cursor: Pagination cursor for fetching the previous page of results.
        payment_mode: Filter by payment type:
            - 'ecom': Standard e-commerce card/bank payments
            - 'bnpl': Buy Now Pay Later financing options
        status: Filter by checkout session state:
            - 'created': Session created, customer hasn't started
            - 'attempted': Customer began but didn't complete
            - 'completed': Payment successfully collected
            - 'expired': Session timed out (typically 24 hours)
        payment_status: Filter by the resulting payment's status.
        sub_account_id: Optional sub-account ID. Overrides the default
            platform_account_id if provided.

    Returns:
        Object containing:
        - data: Array of checkout objects with id, status, amount, payment_mode, created_at
        - page_info: Pagination metadata for navigating through results

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

    # Validate payment_mode if provided
    if payment_mode and payment_mode not in ["bnpl", "ecom"]:
        raise ValidationError(
            "payment_mode must be 'bnpl' or 'ecom'",
            field="payment_mode",
            value=payment_mode,
        )

    # Validate status if provided
    if status and status not in ["created", "completed", "attempted", "expired"]:
        raise ValidationError(
            "status must be one of: created, completed, attempted, expired",
            field="status",
            value=status,
        )

    params: dict[str, Any] = {"limit": limit}
    if after_cursor:
        params["after_cursor"] = after_cursor
    if before_cursor:
        params["before_cursor"] = before_cursor
    if payment_mode:
        params["payment_mode"] = payment_mode
    if status:
        params["status"] = status
    if payment_status:
        params["payment_status"] = payment_status

    return await client.request(
        "GET", "/v1/checkouts", params=params, sub_account_id=sub_account_id
    )


@handle_tool_errors
async def retrieve_checkout(
    client: JustiFiClient,
    checkout_id: str,
    sub_account_id: str | None = None,
) -> dict[str, Any]:
    """Retrieve detailed information about a specific checkout session.

    Use this to get complete details about a checkout session including its status,
    configuration, and resulting payment (if completed). Essential for debugging
    checkout issues, tracking customer progress, or retrieving payment details
    after completion.

    Related tools:
    - Use `list_checkouts` first to find checkout IDs
    - Use `retrieve_payment` if the checkout is completed to see payment details
    - Use `generate_unified_checkout_integration` for integration examples

    Args:
        client: JustiFi client instance.
        checkout_id: The unique identifier for the checkout (e.g., 'co_ABC123XYZ').
            Obtain from `list_checkouts`, your checkout creation response, or webhooks.
        sub_account_id: Optional sub-account ID. Overrides the default
            platform_account_id if provided.

    Returns:
        Checkout object containing:
        - id: Unique checkout identifier
        - status: Session state (created, attempted, completed, expired)
        - amount: Payment amount in cents
        - currency: Three-letter ISO currency code
        - payment_mode: 'ecom' or 'bnpl'
        - payment_id: ID of resulting payment (if completed)
        - checkout_url: URL to redirect customers to for payment
        - success_url: Where customers go after successful payment
        - cancel_url: Where customers go if they cancel
        - created_at: ISO 8601 timestamp

    Raises:
        ValidationError: If checkout_id is empty or invalid.
        ToolError: For API errors (wrapped from httpx.HTTPStatusError).
    """
    if not checkout_id or not checkout_id.strip():
        raise ValidationError(
            "checkout_id cannot be empty", field="checkout_id", value=checkout_id
        )

    return await client.request(
        "GET", f"/v1/checkouts/{checkout_id}", sub_account_id=sub_account_id
    )
