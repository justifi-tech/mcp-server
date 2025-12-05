"""
JustiFi Refund Tools

Tools for retrieving and listing refunds.
"""

from typing import Any

from ..core import JustiFiClient
from .base import ValidationError, handle_tool_errors


@handle_tool_errors
async def list_refunds(
    client: JustiFiClient,
    limit: int = 25,
    after_cursor: str | None = None,
    before_cursor: str | None = None,
    sub_account_id: str | None = None,
) -> dict[str, Any]:
    """List all refunds across your account with cursor-based pagination.

    Use this for a global view of refund activity across all payments. Useful for
    refund reporting, reconciliation, and monitoring refund trends. For refunds
    associated with a specific payment, use `list_payment_refunds` instead.

    Pagination: Use `page_info.end_cursor` as `after_cursor` to fetch subsequent pages.

    Related tools:
    - Use `retrieve_refund` with a refund ID for complete details
    - Use `list_payment_refunds` to see refunds for a specific payment
    - Use `retrieve_payment` to see the original payment that was refunded

    Args:
        client: JustiFi API client
        limit: Number of refunds to return per page (1-100, default: 25).
        after_cursor: Pagination cursor for fetching the next page of results.
        before_cursor: Pagination cursor for fetching the previous page of results.
        sub_account_id: Optional sub-account ID. Overrides the default
            platform_account_id if provided.

    Returns:
        Object containing:
        - data: Array of refund objects with id, amount, status, payment_id, reason
        - page_info: Pagination metadata for navigating through results

    Raises:
        ValidationError: If parameters are invalid
        ToolError: For API errors
    """
    # Validation
    if limit < 1 or limit > 100:
        raise ValidationError(
            "limit must be an integer between 1 and 100", field="limit", value=limit
        )

    if after_cursor and before_cursor:
        raise ValidationError("Cannot specify both after_cursor and before_cursor")

    params: dict[str, Any] = {"limit": limit}
    if after_cursor:
        params["after_cursor"] = after_cursor
    if before_cursor:
        params["before_cursor"] = before_cursor

    response = await client.request(
        "GET", "/v1/refunds", params=params, sub_account_id=sub_account_id
    )
    return response


@handle_tool_errors
async def retrieve_refund(
    client: JustiFiClient,
    refund_id: str,
    sub_account_id: str | None = None,
) -> dict[str, Any]:
    """Retrieve detailed information about a specific refund by ID.

    Use this to get complete refund details including the amount, status, reason,
    and associated payment information. Essential for customer service inquiries
    about refund status or investigating refund processing issues.

    Related tools:
    - Use `list_refunds` first to find refund IDs
    - Use `retrieve_payment` to get details about the original payment
    - Use `list_payment_refunds` to see all refunds for the associated payment

    Args:
        client: JustiFi API client
        refund_id: The unique identifier for the refund (e.g., 're_ABC123XYZ').
            Obtain this from `list_refunds`, `list_payment_refunds`, or webhook events.
        sub_account_id: Optional sub-account ID. Overrides the default
            platform_account_id if provided.

    Returns:
        Refund object containing:
        - id: Unique refund identifier
        - amount: Refund amount in cents
        - status: Refund state (pending, succeeded, failed)
        - reason: Reason for the refund (duplicate, fraudulent, customer_request)
        - payment_id: ID of the original payment that was refunded
        - created_at: ISO 8601 timestamp of refund creation

    Raises:
        ValidationError: If refund_id is invalid
        ToolError: For API errors
    """
    # Validation
    if not refund_id:
        raise ValidationError("refund_id must be a non-empty string")

    if isinstance(refund_id, str) and not refund_id.strip():
        raise ValidationError("refund_id cannot be empty or contain only whitespace")

    response = await client.request(
        "GET", f"/v1/refunds/{refund_id}", sub_account_id=sub_account_id
    )
    return response


@handle_tool_errors
async def list_payment_refunds(
    client: JustiFiClient,
    payment_id: str,
    sub_account_id: str | None = None,
) -> dict[str, Any]:
    """List all refunds associated with a specific payment.

    Use this to see the complete refund history for a single payment. A payment can
    have multiple partial refunds, and this tool shows all of them. Useful for
    customer service inquiries or verifying refund totals against the original
    payment amount.

    Note: This fetches refunds embedded in the payment object, not a separate refunds
    endpoint. No pagination is needed as refunds are returned with the payment.

    Related tools:
    - Use `list_refunds` for a global view of all refunds across payments
    - Use `retrieve_payment` to see the full payment details including refund total
    - Use `retrieve_refund` to get detailed info on a specific refund

    Args:
        client: JustiFi API client
        payment_id: The unique identifier for the payment (e.g., 'py_ABC123XYZ').
            Obtain this from `list_payments` or webhook events.
        sub_account_id: Optional sub-account ID. Overrides the default
            platform_account_id if provided.

    Returns:
        Object containing:
        - data: Array of refund objects with id, amount, status, reason, created_at
        - type: 'array' indicating this is a list response
        - page_info: null (refunds from payment data don't use pagination)

    Raises:
        ValidationError: If payment_id is invalid
        ToolError: For API errors
    """
    # Validation
    if not payment_id:
        raise ValidationError("payment_id must be a non-empty string")

    if isinstance(payment_id, str) and not payment_id.strip():
        raise ValidationError("payment_id cannot be empty or contain only whitespace")

    # Get payment data which includes refunds array
    payment_response = await client.request(
        "GET", f"/v1/payments/{payment_id}", sub_account_id=sub_account_id
    )

    # Extract refunds from payment response
    refunds = payment_response.get("data", {}).get("refunds", [])

    # Return in standard list format
    return {
        "type": "array",
        "data": refunds,
        "page_info": None,  # Payment refunds don't use pagination
    }
