"""
JustiFi MCP Integration - Payment Processing Tools

This module provides MCP tools for interacting with the JustiFi payments API.
Supports OAuth2 Client-Credentials auth with token caching.
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx
from langsmith import traceable
from pydantic import BaseModel


class _TokenCache(BaseModel):
    """Simple in-memory OAuth token cache."""

    token: str | None = None
    expires_at: float = 0.0  # epoch seconds


_TOKEN_CACHE = _TokenCache()


def _clear_token_cache() -> None:
    """Clear the token cache (useful for testing)."""
    global _TOKEN_CACHE
    _TOKEN_CACHE = _TokenCache()


async def _get_access_token() -> str:
    """Fetch and cache a JustiFi access token (OAuth client-credentials)."""
    if _TOKEN_CACHE.token and time.time() < _TOKEN_CACHE.expires_at - 60:
        return _TOKEN_CACHE.token

    client_id = os.getenv("JUSTIFI_CLIENT_ID")
    client_secret = os.getenv("JUSTIFI_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError("JUSTIFI_CLIENT_ID/SECRET must be set in the environment")

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            "https://api.justifi.ai/oauth/token",
            json={"client_id": client_id, "client_secret": client_secret},
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
        _TOKEN_CACHE.token = data["access_token"]
        _TOKEN_CACHE.expires_at = time.time() + int(data.get("expires_in", 86400))
        return _TOKEN_CACHE.token


async def _request(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Internal helper to call JustiFi API."""
    token = await _get_access_token()
    base_url = os.getenv("JUSTIFI_BASE_URL", "https://api.justifi.ai/v1")
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.request(
            method.upper(), url, headers=headers, params=params, json=data
        )
        resp.raise_for_status()
        result: dict[str, Any] = resp.json()
        return result


# ---------------- Public MCP Tools ----------------


@traceable
async def create_payment(
    amount_cents: int,
    currency: str,
    idempotency_key: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Create a new payment in JustiFi.

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
    """
    Issue a refund for a specific payment.

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
