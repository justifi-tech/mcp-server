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

    Use this to get complete payment details including status, amount, payment method,
    and transaction metadata. Common use cases include checking payment status after
    creation, retrieving details for customer service inquiries, and auditing transactions.

    Related tools:
    - Use `list_payments` first to find payment IDs
    - Use `list_payment_refunds` to see refunds associated with this payment
    - Use `retrieve_payment_method` to get details about the payment method used

    Args:
        client: JustiFi API client
        payment_id: The unique identifier for the payment (e.g., 'py_ABC123XYZ').
            Obtain this from `list_payments`, checkout completion, or webhook events.

    Returns:
        Payment object containing:
        - id: Unique payment identifier
        - status: Payment state (pending, authorized, succeeded, failed, disputed, refunded)
        - amount: Amount in cents (e.g., 1000 = $10.00)
        - currency: Three-letter ISO currency code (e.g., 'usd')
        - payment_method: Nested object with card/bank account details
        - refunds: Array of associated refund objects
        - metadata: Custom key-value data attached to the payment
        - created_at: ISO 8601 timestamp of payment creation

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
    """List payments with cursor-based pagination.

    Use this to browse payment history, find specific transactions, or build payment
    reports. Returns payments in reverse chronological order (newest first). For
    details on a specific payment, use `retrieve_payment` with the payment ID.

    Pagination: Use `page_info.end_cursor` from the response as `after_cursor` in
    the next request to fetch the next page. Continue until `page_info.has_next_page`
    is false.

    Related tools:
    - Use `retrieve_payment` with a payment ID from results to get full details
    - Use `list_refunds` for a global view of all refunds across payments

    Args:
        client: JustiFi API client
        limit: Number of payments to return per page (1-100, default: 25).
            Use smaller values for quick lookups, larger for batch processing.
        after_cursor: Pagination cursor from previous response's `page_info.end_cursor`.
            Returns payments created before the cursor position.
        before_cursor: Pagination cursor from previous response's `page_info.start_cursor`.
            Returns payments created after the cursor position (for reverse pagination).

    Returns:
        Object containing:
        - data: Array of payment objects with id, status, amount, currency, created_at
        - page_info: Pagination metadata with has_next_page, has_previous_page,
          start_cursor, end_cursor for navigating through results

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
