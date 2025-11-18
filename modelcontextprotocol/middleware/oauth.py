"""OAuth 2.1 Middleware for JustiFi MCP Server.

This middleware implements OAuth 2.1 authentication for HTTP transport mode.
It extracts Bearer tokens from Authorization headers and stores authentication
context in request.state for downstream tools to access.

For stdio transport (local development), this middleware is not used.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class OAuthMiddleware(BaseHTTPMiddleware):
    """Extract OAuth bearer token and enforce authentication for protected endpoints.

    This middleware:
    1. Skips authentication for public endpoints (/.well-known/*, /health)
    2. Extracts Bearer token from Authorization header (OAuth 2.1 flow)
    3. Falls back to X-Client-Id/X-Client-Secret headers (developer bypass)
    4. Returns 401 with WWW-Authenticate header if no valid auth found
    5. Stores auth context in request.state for tools to access
    """

    # Public endpoints that don't require authentication
    PUBLIC_PATHS = {
        "/.well-known/oauth-protected-resource",
        "/health",
    }

    async def dispatch(self, request: Request, call_next: callable) -> Response:
        """Process request and enforce OAuth authentication.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in the chain

        Returns:
            Response from next handler or 401 if authentication fails
        """
        # Skip authentication for public endpoints
        if self._is_public_path(request.url.path):
            return await call_next(request)

        # Check for Bearer token (OAuth 2.1 flow from Claude Desktop)
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()
            if token:
                request.state.bearer_token = token
                request.state.auth_type = "oauth"
                return await call_next(request)

        # Check for client credentials (developer bypass for internal testing)
        client_id = request.headers.get("X-Client-Id")
        client_secret = request.headers.get("X-Client-Secret")
        if client_id and client_secret:
            request.state.client_id = client_id
            request.state.client_secret = client_secret
            request.state.auth_type = "client_credentials"
            return await call_next(request)

        # No valid authentication found - return 401 with OAuth metadata location
        return Response(
            status_code=401,
            content="Unauthorized",
            headers={
                "WWW-Authenticate": (
                    'Bearer resource_metadata="https://mcp.justifi.ai/'
                    '.well-known/oauth-protected-resource"'
                )
            },
        )

    def _is_public_path(self, path: str) -> bool:
        """Check if the given path is a public endpoint.

        Args:
            path: Request URL path

        Returns:
            True if path is public and doesn't require authentication
        """
        # Exact match for public paths
        if path in self.PUBLIC_PATHS:
            return True

        # Allow all /.well-known/ paths
        if path.startswith("/.well-known/"):
            return True

        return False
