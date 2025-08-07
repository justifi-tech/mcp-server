"""
JustiFi Payment Tools

Core payment operations for retrieving and listing payments.
"""

from __future__ import annotations

from typing import Any

from ..core import JustiFiClient
from .base import ToolError, ValidationError
from .response_formatter import standardize_response


async def retrieve_payment(client: JustiFiClient, payment_id: str) -> dict[str, Any]:
    """Retrieve detailed information about a specific payment by ID.

    Args:
        client: JustiFi API client
        payment_id: The unique identifier for the payment (e.g., 'py_ABC123XYZ')

    Returns:
        Payment object with ID, status, amount, and details

    Raises:
        ValidationError: If payment_id is invalid
        ToolError: If payment retrieval fails
    """
    if not payment_id or not isinstance(payment_id, str):
        raise ValidationError(
            "payment_id is required and must be a non-empty string",
            field="payment_id",
            value=payment_id,
        )

    if not payment_id.strip():
        raise ValidationError(
            "payment_id cannot be empty or whitespace",
            field="payment_id",
            value=payment_id,
        )

    try:
        # Call JustiFi API to retrieve payment
        result = await client.request("GET", f"/v1/payments/{payment_id}")
        return standardize_response(result, "retrieve_payment")

    except Exception as e:
        raise ToolError(
            f"Failed to retrieve payment {payment_id}: {str(e)}",
            error_type="PaymentRetrievalError",
        ) from e


async def list_payments(
    client: JustiFiClient,
    limit: int = 25,
    after_cursor: str | None = None,
    before_cursor: str | None = None,
) -> dict[str, Any]:
    """List payments with optional pagination using cursor-based pagination.

    Args:
        client: JustiFi API client
        limit: Number of payments to return (1-100, default: 25)
        after_cursor: Cursor for pagination - returns results after this cursor
        before_cursor: Cursor for pagination - returns results before this cursor

    Returns:
        Paginated list of payments with page_info for navigation

    Raises:
        ValidationError: If parameters are invalid
        ToolError: If payment listing fails
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

    try:
        # Build query parameters
        params: dict[str, Any] = {"limit": limit}

        if after_cursor:
            params["after_cursor"] = after_cursor
        if before_cursor:
            params["before_cursor"] = before_cursor

        # Call JustiFi API to list payments
        result = await client.request("GET", "/v1/payments", params=params)
        return standardize_response(result, "list_payments")

    except Exception as e:
        raise ToolError(
            f"Failed to list payments: {str(e)}", error_type="PaymentListError"
        ) from e
