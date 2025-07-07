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
) -> dict[str, Any]:
    """List refunds with pagination support.

    Args:
        client: JustiFi API client
        limit: Number of refunds to return (1-100, default: 25)
        after_cursor: Cursor for pagination - returns results after this cursor
        before_cursor: Cursor for pagination - returns results before this cursor

    Returns:
        Dict containing refunds list and pagination info

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

    response = await client.request("GET", "/v1/refunds", params=params)
    return response


@handle_tool_errors
async def retrieve_refund(
    client: JustiFiClient,
    refund_id: str,
) -> dict[str, Any]:
    """Retrieve a specific refund by ID.

    Args:
        client: JustiFi API client
        refund_id: The ID of the refund to retrieve

    Returns:
        Dict containing refund details

    Raises:
        ValidationError: If refund_id is invalid
        ToolError: For API errors
    """
    # Validation
    if not refund_id:
        raise ValidationError("refund_id must be a non-empty string")

    if isinstance(refund_id, str) and not refund_id.strip():
        raise ValidationError("refund_id cannot be empty or contain only whitespace")

    response = await client.request("GET", f"/v1/refunds/{refund_id}")
    return response


@handle_tool_errors
async def list_payment_refunds(
    client: JustiFiClient,
    payment_id: str,
) -> dict[str, Any]:
    """List all refunds for a specific payment.

    Args:
        client: JustiFi API client
        payment_id: The ID of the payment to get refunds for

    Returns:
        Dict containing refunds list (extracted from payment data)

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
    payment_response = await client.request("GET", f"/v1/payments/{payment_id}")

    # Extract refunds from payment response
    refunds = payment_response.get("data", {}).get("refunds", [])

    # Return in standard list format
    return {
        "type": "array",
        "data": refunds,
        "page_info": None,  # Payment refunds don't use pagination
    }
