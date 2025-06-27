"""JustiFi MCP Integration - Core Authentication & HTTP

Shared OAuth2 token management and HTTP request functionality
for JustiFi MCP tools, with a focus on payout operations.
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx
from pydantic import BaseModel


class _TokenCache(BaseModel):
    """Simple in-memory OAuth token cache."""

    token: str | None = None
    expires_at: float = 0.0  # epoch seconds


_TOKEN_CACHE = _TokenCache()


class JustiFiClient:
    """JustiFi API client focused on payout operations."""

    def __init__(self, client_id: str | None = None, client_secret: str | None = None):
        """Initialize JustiFi client.

        Args:
            client_id: JustiFi client ID (or from JUSTIFI_CLIENT_ID env var)
            client_secret: JustiFi client secret (or from JUSTIFI_CLIENT_SECRET env var)

        """
        self.client_id = client_id or os.getenv("JUSTIFI_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("JUSTIFI_CLIENT_SECRET")

        if not self.client_id or not self.client_secret:
            raise RuntimeError(
                "JUSTIFI_CLIENT_ID/SECRET must be provided or set in environment"
            )

    def clear_token_cache(self) -> None:
        """Clear the token cache (useful for testing)."""
        global _TOKEN_CACHE
        _TOKEN_CACHE = _TokenCache()

    async def get_access_token(self) -> str:
        """Fetch and cache a JustiFi access token (OAuth client-credentials)."""
        if _TOKEN_CACHE.token and time.time() < _TOKEN_CACHE.expires_at - 60:
            return _TOKEN_CACHE.token

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://api.justifi.ai/oauth/token",
                json={"client_id": self.client_id, "client_secret": self.client_secret},
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()
            _TOKEN_CACHE.token = data["access_token"]
            _TOKEN_CACHE.expires_at = time.time() + int(data.get("expires_in", 86400))
            return _TOKEN_CACHE.token

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Call JustiFi API with automatic token refresh on 401.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path (e.g., "/payouts")
            params: Query parameters
            data: JSON body data
            idempotency_key: Optional idempotency key header

        Returns:
            JSON response from JustiFi API

        Raises:
            httpx.HTTPStatusError: For HTTP errors
            RuntimeError: For missing credentials

        """
        base_url = os.getenv("JUSTIFI_BASE_URL", "https://api.justifi.ai/v1")
        url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"

        # First attempt
        try:
            return await self._make_request(method, url, params, data, idempotency_key)
        except httpx.HTTPStatusError as e:
            # Retry once on 401 (token expired)
            if e.response.status_code == 401:
                self.clear_token_cache()  # Force token refresh
                return await self._make_request(
                    method, url, params, data, idempotency_key
                )
            raise

    async def _make_request(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None,
        data: dict[str, Any] | None,
        idempotency_key: str | None,
    ) -> dict[str, Any]:
        """Make the actual HTTP request with current token."""
        token = await self.get_access_token()
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


# Legacy functions for backward compatibility
def _clear_token_cache() -> None:
    """Clear the token cache (useful for testing)."""
    global _TOKEN_CACHE
    _TOKEN_CACHE = _TokenCache()


async def _get_access_token() -> str:
    """Legacy function - use JustiFiClient.get_access_token() instead."""
    client = JustiFiClient()
    return await client.get_access_token()


async def _request(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Legacy function - use JustiFiClient.request() instead."""
    client = JustiFiClient()
    return await client.request(
        method, path, params=params, data=data, idempotency_key=idempotency_key
    )
