"""
JustiFi Dispute Tools - Framework-Agnostic Business Logic

Pure business logic for dispute operations, separated from any specific
framework (MCP, LangChain, etc.). These functions return raw Python data
structures and can be used by any framework adapter.
"""

from __future__ import annotations

from typing import Any

from ..core import JustiFiClient
from .base import ValidationError, handle_tool_errors


@handle_tool_errors
async def list_disputes(
    client: JustiFiClient,
    limit: int = 25,
    after_cursor: str | None = None,
    before_cursor: str | None = None,
    sub_account_id: str | None = None,
) -> dict[str, Any]:
    """List payment disputes (chargebacks) with cursor-based pagination.

    Use this to monitor and manage disputes filed by cardholders against payments.
    Disputes occur when a customer contests a charge with their bank. Timely response
    is critical—disputes have strict deadlines for submitting evidence.

    Dispute lifecycle: needs_response → under_review → won/lost

    Pagination: Use `page_info.end_cursor` as `after_cursor` to fetch subsequent pages.

    Related tools:
    - Use `retrieve_dispute` with a dispute ID for complete details and evidence requirements
    - Use `retrieve_payment` to see the original disputed payment

    Args:
        client: JustiFi client instance.
        limit: Number of disputes to return per page (1-100, default: 25).
        after_cursor: Pagination cursor for fetching the next page of results.
        before_cursor: Pagination cursor for fetching the previous page of results.
        sub_account_id: Optional sub-account ID. Overrides the default
            platform_account_id if provided.

    Returns:
        Object containing:
        - data: Array of dispute objects with id, status, amount, reason, payment_id,
          due_date (deadline), created_at
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

    params: dict[str, Any] = {"limit": limit}
    if after_cursor:
        params["after_cursor"] = after_cursor
    if before_cursor:
        params["before_cursor"] = before_cursor

    return await client.request(
        "GET", "/v1/disputes", params=params, sub_account_id=sub_account_id
    )


@handle_tool_errors
async def retrieve_dispute(
    client: JustiFiClient,
    dispute_id: str,
    sub_account_id: str | None = None,
) -> dict[str, Any]:
    """Retrieve detailed information about a specific dispute (chargeback).

    Use this to get complete dispute details including the reason, evidence requirements,
    deadline for response, and current status. Essential for preparing dispute responses
    and understanding why a customer contested a charge.

    Related tools:
    - Use `list_disputes` first to find dispute IDs
    - Use `retrieve_payment` to see the original payment that was disputed

    Args:
        client: JustiFi client instance.
        dispute_id: The unique identifier for the dispute (e.g., 'dp_ABC123XYZ').
            Obtain from `list_disputes` or webhook events.
        sub_account_id: Optional sub-account ID. Overrides the default
            platform_account_id if provided.

    Returns:
        Dispute object containing:
        - id: Unique dispute identifier
        - status: Dispute state (needs_response, under_review, won, lost)
        - amount: Disputed amount in cents
        - currency: Three-letter ISO currency code
        - reason: Why the cardholder disputed (fraudulent, duplicate, product_not_received, etc.)
        - payment_id: ID of the original disputed payment
        - due_date: Deadline for evidence submission (date format)
        - evidence: Object with evidence requirements and submitted documents
        - created_at: When the dispute was filed

    Raises:
        ValidationError: If dispute_id is empty or invalid.
        ToolError: For API errors (wrapped from httpx.HTTPStatusError).
    """
    if not dispute_id or not dispute_id.strip():
        raise ValidationError(
            "dispute_id cannot be empty", field="dispute_id", value=dispute_id
        )

    return await client.request(
        "GET", f"/v1/disputes/{dispute_id}", sub_account_id=sub_account_id
    )
