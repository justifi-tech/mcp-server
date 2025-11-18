"""OAuth 2.1 Middleware for JustiFi MCP Server using FastMCP.

This middleware implements OAuth 2.1 authentication for HTTP transport mode.
It extracts Bearer tokens from Authorization headers and stores authentication
context in fastmcp.Context for downstream tools to access.

For stdio transport (local development), this middleware is not used.
"""

from __future__ import annotations

import logging
from typing import Awaitable, Callable

from fastmcp import Context
from starlette.datastructures import Headers
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger(__name__)


class OAuthMiddleware:
    """Extract OAuth bearer token and enforce authentication for protected endpoints.

    This middleware:
    1. Skips authentication for public endpoints (/.well-known/*, /health)
    2. Extracts Bearer token from Authorization header (OAuth 2.1 flow)
    3. Falls back to X-Client-Id/X-Client-Secret headers (developer bypass)
    4. Returns 401 with WWW-Authenticate header if no valid auth found
    5. Stores auth context in fastmcp.Context for tools to access
    """

    PUBLIC_PATHS = {
        "/.well-known/oauth-protected-resource",
        "/health",
    }

    def __init__(self, app: ASGIApp):
        """Initialize the OAuth middleware.

        Args:
            app: The ASGI application to wrap
        """
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Process request and enforce OAuth authentication.

        Args:
            scope: ASGI scope dictionary
            receive: ASGI receive callable
            send: ASGI send callable
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")

        if self._is_public_path(path):
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        auth_header = headers.get("Authorization", "")

        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()
            if token:
                ctx = Context.get_current()
                ctx.metadata["bearer_token"] = token
                ctx.metadata["auth_type"] = "oauth"
                logger.debug("OAuth bearer token extracted from request")
                await self.app(scope, receive, send)
                return

        client_id = headers.get("X-Client-Id")
        client_secret = headers.get("X-Client-Secret")
        if client_id and client_secret:
            ctx = Context.get_current()
            ctx.metadata["client_id"] = client_id
            ctx.metadata["client_secret"] = client_secret
            ctx.metadata["auth_type"] = "client_credentials"
            logger.debug("Client credentials extracted from request headers")
            await self.app(scope, receive, send)
            return

        logger.warning(f"Unauthorized request to protected path: {path}")
        response = Response(
            status_code=401,
            content="Unauthorized",
            headers={
                "WWW-Authenticate": (
                    'Bearer resource_metadata="https://mcp.justifi.ai/'
                    '.well-known/oauth-protected-resource"'
                )
            },
        )
        await response(scope, receive, send)

    def _is_public_path(self, path: str) -> bool:
        """Check if the given path is a public endpoint.

        Args:
            path: Request URL path

        Returns:
            True if path is public and doesn't require authentication
        """
        if path in self.PUBLIC_PATHS:
            return True

        if path.startswith("/.well-known/"):
            return True

        return False
