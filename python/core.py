"""JustiFi MCP Integration - Core Authentication & HTTP

Shared OAuth2 token management and HTTP request functionality
for JustiFi MCP tools, with a focus on payout operations.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any

import httpx
from pydantic import BaseModel

# Create logger for this module
logger = logging.getLogger(__name__)


class JustiFiError(Exception):
    """Base exception for JustiFi-related errors."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class AuthenticationError(JustiFiError):
    """Authentication-related errors."""

    pass


class ValidationError(JustiFiError):
    """Input validation errors."""

    pass


class APIError(JustiFiError):
    """JustiFi API errors."""

    def __init__(
        self,
        message: str,
        status_code: int,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, error_code, details)
        self.status_code = status_code


class RateLimitError(APIError):
    """Rate limiting errors."""

    pass


class _TokenCache(BaseModel):
    """Simple in-memory OAuth token cache."""

    token: str | None = None
    expires_at: float = 0.0  # epoch seconds

    def is_expired(self) -> bool:
        """Check if the cached token is expired."""
        return time.time() >= self.expires_at


class JustiFiClient:
    """JustiFi API client with OAuth2 authentication and error handling."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str | None = None,
        bearer_token: str | None = None,
        platform_account_id: str | None = None,
    ):
        """Initialize the JustiFi client.

        Args:
            client_id: JustiFi client ID
            client_secret: JustiFi client secret
            base_url: Optional base URL (overrides JUSTIFI_BASE_URL env var)
            bearer_token: Optional pre-authenticated bearer token (for OAuth flow)
            platform_account_id: Optional default sub-account ID for API requests.
                Used as the Sub-Account header when no sub_account_id is provided
                to individual requests.

        Raises:
            AuthenticationError: If credentials are invalid
        """
        if not bearer_token and (not client_id or not client_secret):
            raise AuthenticationError(
                "JustiFi credentials are required. Please set JUSTIFI_CLIENT_ID and JUSTIFI_CLIENT_SECRET environment variables, or provide a bearer_token."
            )

        self.client_id = client_id
        self.client_secret = client_secret
        self.bearer_token = bearer_token
        self.platform_account_id = platform_account_id

        # Priority: explicit parameter > env var > default
        self.base_url = base_url or os.getenv(
            "JUSTIFI_BASE_URL", "https://api.justifi.ai"
        )

        # Normalize URL - remove trailing slashes and warn about /v1 suffix
        self.base_url = self.base_url.rstrip("/")
        if self.base_url.endswith("/v1"):
            logger.warning(f"Base URL should not include /v1 suffix: {self.base_url}")
            self.base_url = self.base_url[:-3]

        self._token_cache = _TokenCache()

        logger.debug(f"JustiFi client initialized with base URL: {self.base_url}")
        if platform_account_id:
            logger.debug(f"Default platform account ID: {platform_account_id}")

    async def get_access_token(self) -> str:
        """Get a valid access token, refreshing if necessary.

        Returns:
            Valid access token

        Raises:
            AuthenticationError: If unable to authenticate
        """
        if self.bearer_token:
            logger.debug("Using pre-authenticated bearer token")
            return self.bearer_token

        if not self._token_cache.is_expired() and self._token_cache.token:
            logger.debug("Using cached access token")
            return self._token_cache.token

        logger.debug("Requesting new access token from JustiFi OAuth endpoint")

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                oauth_url = f"{self.base_url}/oauth/token"
                logger.debug(f"Making OAuth request to: {oauth_url}")

                response = await client.post(
                    oauth_url,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if response.status_code == 401:
                    logger.error("OAuth authentication failed - invalid credentials")
                    raise AuthenticationError(
                        "Invalid JustiFi credentials. Please check your JUSTIFI_CLIENT_ID and JUSTIFI_CLIENT_SECRET.",
                        error_code="invalid_credentials",
                    )

                response.raise_for_status()
                token_data = response.json()

            # Cache the token with expiration
            expires_in = token_data.get("expires_in", 3600)  # Default 1 hour
            access_token: str = token_data["access_token"]
            self._token_cache = _TokenCache(
                token=access_token,
                expires_at=time.time() + expires_in - 60,  # Refresh 1 minute early
            )

            logger.debug(
                f"Successfully obtained access token (expires in {expires_in}s)"
            )
            return access_token

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during OAuth: {e.response.status_code}")
            if e.response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed. Please verify your JustiFi credentials.",
                    error_code="auth_failed",
                ) from e
            else:
                raise AuthenticationError(
                    f"Authentication error: {e.response.status_code}",
                    error_code="auth_error",
                ) from e
        except httpx.RequestError as e:
            logger.error(f"Network error during OAuth: {e}")
            raise AuthenticationError(
                "Unable to connect to JustiFi API. Please check your network connection.",
                error_code="connection_error",
            ) from e

    async def request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
        extra_headers: dict[str, str] | None = None,
        retries: int = 3,
        sub_account_id: str | None = None,
    ) -> dict[str, Any]:
        """Make an authenticated request to the JustiFi API with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., '/payouts')
            params: Query parameters
            data: Request body data
            idempotency_key: Optional idempotency key
            extra_headers: Additional headers to include in the request
            retries: Number of retry attempts for transient errors
            sub_account_id: Optional sub-account ID for this request. If provided,
                sets the Sub-Account header. Falls back to platform_account_id if
                not provided.

        Returns:
            API response data

        Raises:
            ValidationError: For invalid input
            APIError: For API-related errors
            RateLimitError: For rate limiting
        """
        effective_sub_account = sub_account_id or self.platform_account_id
        if effective_sub_account:
            if extra_headers is None:
                extra_headers = {}
            if "Sub-Account" not in extra_headers:
                extra_headers["Sub-Account"] = effective_sub_account
                if sub_account_id:
                    logger.debug(
                        f"Using request-specific sub-account: {sub_account_id}"
                    )
                elif self.platform_account_id:
                    logger.debug(
                        f"Using platform default sub-account: {self.platform_account_id}"
                    )

        url = f"{self.base_url}{endpoint}"
        logger.debug(f"Making {method} request to: {url}")

        if params:
            logger.debug(f"Query parameters: {params}")
        if data:
            logger.debug(f"Request body keys: {list(data.keys()) if data else 'None'}")

        for attempt in range(retries + 1):
            try:
                return await self._make_request(
                    method, url, params, data, idempotency_key, extra_headers
                )

            except httpx.HTTPStatusError as e:
                logger.warning(
                    f"HTTP error on attempt {attempt + 1}: {e.response.status_code}"
                )

                # Don't retry client errors (4xx) except 429
                if (
                    400 <= e.response.status_code < 500
                    and e.response.status_code != 429
                ):
                    await self._handle_client_error(e)
                    return {}  # This line won't be reached due to exception, but satisfies linter

                # Retry on server errors (5xx) and rate limits (429)
                if attempt < retries and (
                    e.response.status_code >= 500 or e.response.status_code == 429
                ):
                    wait_time = min(2**attempt, 10)  # Exponential backoff, max 10s
                    logger.info(
                        f"Retrying in {wait_time}s (attempt {attempt + 1}/{retries})"
                    )
                    await asyncio.sleep(wait_time)
                    continue

                # Final attempt failed
                await self._handle_server_error(e)
                return {}  # This line won't be reached due to exception, but satisfies linter

            except httpx.RequestError as e:
                logger.warning(f"Network error on attempt {attempt + 1}: {e}")

                # Retry on network errors
                if attempt < retries:
                    wait_time = min(2**attempt, 10)
                    logger.info(
                        f"Retrying in {wait_time}s (attempt {attempt + 1}/{retries})"
                    )
                    await asyncio.sleep(wait_time)
                    continue

                logger.error("Max retry attempts exceeded for network error")
                raise APIError(
                    "Unable to connect to JustiFi API. Please check your network connection and try again.",
                    status_code=0,
                    error_code="connection_error",
                ) from e

        # This should never be reached, but satisfies linter
        raise APIError(
            "Maximum retry attempts exceeded",
            status_code=0,
            error_code="max_retries_exceeded",
        )

    async def _handle_client_error(self, error: httpx.HTTPStatusError) -> None:
        """Handle 4xx client errors - pass through JustiFi errors."""
        try:
            error_data = error.response.json()
        except Exception:
            error_data = {}

        status_code = error.response.status_code

        # Extract error info from JustiFi response (nested under "error" key)
        justifi_error = (
            error_data.get("error", error_data)
            if isinstance(error_data, dict)
            else error_data
        )
        if isinstance(justifi_error, dict):
            error_code = justifi_error.get("code", f"http_{status_code}")
            error_message = justifi_error.get("message", error.response.text)
        else:
            error_code = f"http_{status_code}"
            error_message = str(justifi_error) if justifi_error else error.response.text

        logger.error(f"JustiFi API error {status_code}: {error_code} - {error_message}")

        if status_code == 401:
            logger.warning("Authentication failed - clearing token cache")
            self._token_cache = _TokenCache()
            raise AuthenticationError(
                error_message, error_code=error_code, details=error_data
            )
        elif status_code == 429:
            raise RateLimitError(
                error_message,
                status_code=429,
                error_code=error_code,
                details=error_data,
            )
        elif status_code in (400, 404, 422):
            raise ValidationError(
                error_message, error_code=error_code, details=error_data
            )
        else:
            raise APIError(
                error_message,
                status_code=status_code,
                error_code=error_code,
                details=error_data,
            )

    async def _handle_server_error(self, error: httpx.HTTPStatusError) -> None:
        """Handle 5xx server errors - pass through JustiFi errors."""
        try:
            error_data = error.response.json()
        except Exception:
            error_data = {}

        status_code = error.response.status_code

        # Extract error info from JustiFi response
        justifi_error = (
            error_data.get("error", error_data)
            if isinstance(error_data, dict)
            else error_data
        )
        if isinstance(justifi_error, dict):
            error_code = justifi_error.get("code", f"http_{status_code}")
            error_message = justifi_error.get("message", error.response.text)
        else:
            error_code = f"http_{status_code}"
            error_message = str(justifi_error) if justifi_error else error.response.text

        logger.error(f"JustiFi API error {status_code}: {error_code} - {error_message}")

        raise APIError(
            error_message,
            status_code=status_code,
            error_code=error_code,
            details=error_data,
        )

    async def _make_request(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None,
        data: dict[str, Any] | None,
        idempotency_key: str | None,
        extra_headers: dict[str, str] | None,
    ) -> dict[str, Any]:
        """Make the actual HTTP request with current token."""
        token = await self.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        if extra_headers:
            headers.update(extra_headers)

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.request(
                method.upper(), url, headers=headers, params=params, json=data
            )

            logger.debug(f"Response status: {resp.status_code}")
            resp.raise_for_status()
            result: dict[str, Any] = resp.json()
            logger.debug(f"Response received with {len(result)} top-level keys")
            return result
