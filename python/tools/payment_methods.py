"""
JustiFi Payment Method Tools

Payment method operations for retrieving tokenized payment methods.
"""

from __future__ import annotations

from typing import Any

from ..core import JustiFiClient
from .base import ToolError, ValidationError


async def retrieve_payment_method(
    client: JustiFiClient, payment_method_token: str
) -> dict[str, Any]:
    """Retrieve detailed information about a specific payment method by token.

    Args:
        client: JustiFi API client
        payment_method_token: The unique token for the payment method (e.g., 'pm_ABC123XYZ')

    Returns:
        Payment method object with token, type, card/bank details, and metadata

    Raises:
        ValidationError: If payment_method_token is invalid
        ToolError: If payment method retrieval fails
    """
    if not payment_method_token or not isinstance(payment_method_token, str):
        raise ValidationError(
            "payment_method_token is required and must be a non-empty string",
            field="payment_method_token",
            value=payment_method_token,
        )

    if not payment_method_token.strip():
        raise ValidationError(
            "payment_method_token cannot be empty or whitespace",
            field="payment_method_token",
            value=payment_method_token,
        )

    try:
        # Call JustiFi API to retrieve payment method
        result = await client.request(
            "GET", f"/v1/payment_methods/{payment_method_token}"
        )
        return result

    except Exception as e:
        raise ToolError(
            f"Failed to retrieve payment method {payment_method_token}: {str(e)}",
            error_type="PaymentMethodRetrievalError",
        ) from e
