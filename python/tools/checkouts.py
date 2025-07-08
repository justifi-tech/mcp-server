"""
JustiFi Checkout Tools - Framework-Agnostic Business Logic

Pure business logic for checkout operations, separated from any specific
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
async def list_checkouts(
    client: JustiFiClient,
    limit: int = 25,
    after_cursor: str | None = None,
    before_cursor: str | None = None,
    payment_mode: str | None = None,
    status: str | None = None,
    payment_status: str | None = None,
) -> dict[str, Any]:
    """List checkouts with cursor-based pagination and filtering.

    Args:
        client: JustiFi client instance.
        limit: Number of checkouts to return (default: 25, max: 100).
        after_cursor: Cursor for pagination (get checkouts after this cursor).
        before_cursor: Cursor for pagination (get checkouts before this cursor).
        payment_mode: Filter by payment mode ('bnpl', 'ecom').
        status: Filter by checkout status ('created', 'completed', 'attempted', 'expired').
        payment_status: Filter by payment status.

    Returns:
        JSON response with checkouts list from the JustiFi API.

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

    return await client.request("GET", "/v1/checkouts", params=params)


@traceable
@handle_tool_errors
async def retrieve_checkout(client: JustiFiClient, checkout_id: str) -> dict[str, Any]:
    """Retrieve a checkout by its ID.

    Args:
        client: JustiFi client instance.
        checkout_id: The ID of the checkout to retrieve (e.g., 'co_ABC123XYZ').

    Returns:
        JSON response from the JustiFi API with checkout details.

    Raises:
        ValidationError: If checkout_id is empty or invalid.
        ToolError: For API errors (wrapped from httpx.HTTPStatusError).
    """
    if not checkout_id or not checkout_id.strip():
        raise ValidationError(
            "checkout_id cannot be empty", field="checkout_id", value=checkout_id
        )

    return await client.request("GET", f"/v1/checkouts/{checkout_id}")
