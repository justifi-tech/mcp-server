"""
JustiFi Payment Method Tools

Payment method operations for retrieving tokenized payment methods.
"""

from __future__ import annotations

from typing import Any

from ..core import JustiFiClient
from .base import ToolError, ValidationError


async def retrieve_payment_method(
    client: JustiFiClient,
    payment_method_token: str,
    sub_account_id: str | None = None,
) -> dict[str, Any]:
    """Retrieve detailed information about a tokenized payment method.

    Use this to get details about a saved card or bank account, such as card brand,
    last 4 digits, expiration, or bank account type. Payment methods are created when
    customers save payment information during checkout or through the payment method
    tokenization flow.

    Note: For security, full card numbers and CVVs are never returned. Only masked/partial
    information is available.

    Related tools:
    - Use `retrieve_payment` to see a payment method in context of a transaction
    - Use `list_payment_method_groups` to see how payment methods are organized
    - Use `retrieve_payment_method_group` to see payment methods within a group

    Args:
        client: JustiFi API client
        payment_method_token: The unique token for the payment method (e.g., 'pm_ABC123XYZ').
            Obtain from payment responses, checkout completion, or tokenization flows.
        sub_account_id: Optional sub-account ID. Overrides the default
            platform_account_id if provided.

    Returns:
        Payment method object containing:
        - token: Unique payment method identifier
        - type: 'card' or 'bank_account'
        - card (if type='card'): brand, last4, exp_month, exp_year, fingerprint
        - bank_account (if type='bank_account'): bank_name, account_type, last4
        - billing_address: Associated billing address if provided
        - metadata: Custom key-value data attached to the payment method
        - created_at: ISO 8601 timestamp

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
            "GET",
            f"/v1/payment_methods/{payment_method_token}",
            sub_account_id=sub_account_id,
        )
        return result

    except Exception as e:
        raise ToolError(
            f"Failed to retrieve payment method {payment_method_token}: {str(e)}",
            error_type="PaymentMethodRetrievalError",
        ) from e
