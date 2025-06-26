"""JustiFi MCP Integration - Payment Method Tools

Tools for managing payment methods (cards, bank accounts) in JustiFi.
"""

from __future__ import annotations

from typing import Any

from langsmith import traceable

from .core import _request


@traceable
async def create_payment_method(
    customer_id: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Create a new payment method for a customer.

    Args:
        customer_id: The customer ID to associate the payment method with.
        **kwargs: Payment method details (card info, bank account, etc.)
                 as accepted by the JustiFi CreatePaymentMethod schema.

    Returns:
        JSON response from the JustiFi API containing the payment method token.

    """
    payload = {"customer_id": customer_id, **kwargs}
    return await _request("POST", "/payment_methods", data=payload)


@traceable
async def retrieve_payment_method(payment_method_token: str) -> dict[str, Any]:
    """Retrieve a payment method by its token.

    Args:
        payment_method_token: The token of the payment method to retrieve.

    Returns:
        JSON response from the JustiFi API with payment method details.

    """
    return await _request("GET", f"/payment_methods/{payment_method_token}")
