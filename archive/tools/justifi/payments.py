"""JustiFi MCP Integration - Payment Tools

Payment processing tools for creating, retrieving, listing, and refunding payments.
"""

from __future__ import annotations

from typing import Any

from langsmith import traceable

from .core import _request


@traceable
async def create_payment(
    amount_cents: int,
    currency: str,
    idempotency_key: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Create a new payment in JustiFi.

    Args:
        amount_cents: Amount in the smallest currency unit (e.g. 1000 = $10.00).
        currency: ISO currency code, e.g. 'usd'.
        idempotency_key: Unique key to guarantee single processing.
        **kwargs: Any additional fields accepted by the CreatePayment schema.

    Returns:
        JSON response from the JustiFi API.

    """
    payload = {"amount": amount_cents, "currency": currency, **kwargs}
    return await _request(
        "POST",
        "/payments",
        data=payload,
        idempotency_key=idempotency_key,
    )


@traceable
async def retrieve_payment(payment_id: str) -> dict[str, Any]:
    """Retrieve a payment by its ID."""
    return await _request("GET", f"/payments/{payment_id}")


@traceable
async def list_payments(
    limit: int = 25,
    after_cursor: str | None = None,
    before_cursor: str | None = None,
) -> dict[str, Any]:
    """List payments with cursor-based pagination."""
    params: dict[str, Any] = {"limit": limit}
    if after_cursor:
        params["after_cursor"] = after_cursor
    if before_cursor:
        params["before_cursor"] = before_cursor
    return await _request("GET", "/payments", params=params)


@traceable
async def refund_payment(
    payment_id: str,
    amount_cents: int | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Issue a refund for a specific payment.

    Args:
        payment_id: ID of the payment to refund.
        amount_cents: Optional partial-refund amount; defaults to full amount.
        idempotency_key: Optional key to make the request idempotent.

    """
    payload: dict[str, Any] = {}
    if amount_cents is not None:
        payload["amount"] = amount_cents
    return await _request(
        "POST",
        f"/payments/{payment_id}/refunds",
        data=payload,
        idempotency_key=idempotency_key,
    )
