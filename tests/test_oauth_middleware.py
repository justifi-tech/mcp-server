"""Tests for OAuth 2.1 middleware using FastMCP Context."""

from __future__ import annotations

import pytest
from fastmcp import Context
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from modelcontextprotocol.middleware.oauth import OAuthMiddleware


@pytest.fixture
def mock_app_with_context():
    """Create a test Starlette application with OAuth middleware that uses fastmcp.Context."""

    async def protected_endpoint(request: Request):
        """Protected endpoint that requires authentication."""
        try:
            ctx = Context.get_current()
            return JSONResponse(
                {
                    "auth_type": ctx.metadata.get("auth_type"),
                    "bearer_token": ctx.metadata.get("bearer_token"),
                }
            )
        except LookupError:
            return JSONResponse({"error": "No context available"}, status_code=500)

    async def health_endpoint(request: Request):
        """Health check endpoint."""
        return JSONResponse({"status": "ok"})

    app = Starlette(
        routes=[
            Route("/test-protected", protected_endpoint),
            Route("/health", health_endpoint),
            Route(
                "/.well-known/oauth-protected-resource",
                lambda r: JSONResponse({"metadata": "public"}),
            ),
        ],
        middleware=[Middleware(OAuthMiddleware)],
    )

    return app


class TestOAuthMiddleware:
    """Essential tests for OAuthMiddleware authentication behavior."""

    def test_bearer_token_extraction_with_context_setup(self):
        """Test bearer token extraction with manual Context setup."""
        from unittest.mock import Mock, patch

        mock_ctx = Mock()
        mock_ctx.metadata = {}

        with patch("modelcontextprotocol.middleware.oauth.Context") as MockContext:
            MockContext.get_current.return_value = mock_ctx

            from starlette.applications import Starlette
            from starlette.middleware import Middleware
            from starlette.responses import JSONResponse
            from starlette.routing import Route

            async def test_endpoint(request):
                ctx = MockContext.get_current()
                return JSONResponse(
                    {
                        "auth_type": ctx.metadata.get("auth_type"),
                        "bearer_token": ctx.metadata.get("bearer_token"),
                    }
                )

            app = Starlette(
                routes=[Route("/test", test_endpoint)],
                middleware=[Middleware(OAuthMiddleware)],
            )

            client = TestClient(app)
            response = client.get(
                "/test", headers={"Authorization": "Bearer test_token_12345"}
            )

            assert response.status_code == 200
            assert mock_ctx.metadata["auth_type"] == "oauth"
            assert mock_ctx.metadata["bearer_token"] == "test_token_12345"

    def test_returns_401_without_auth(self):
        """Test requests without auth return 401 with WWW-Authenticate header."""
        from unittest.mock import Mock, patch

        with patch("modelcontextprotocol.middleware.oauth.Context") as MockContext:
            mock_ctx = Mock()
            mock_ctx.metadata = {}
            MockContext.get_current.return_value = mock_ctx

            from starlette.applications import Starlette
            from starlette.middleware import Middleware
            from starlette.responses import JSONResponse
            from starlette.routing import Route

            async def test_endpoint(request):
                return JSONResponse({"protected": True})

            app = Starlette(
                routes=[Route("/test", test_endpoint)],
                middleware=[Middleware(OAuthMiddleware)],
            )

            client = TestClient(app)
            response = client.get("/test")

            assert response.status_code == 401
            assert response.text == "Unauthorized"
            assert "WWW-Authenticate" in response.headers

            www_auth = response.headers["WWW-Authenticate"]
            assert www_auth.startswith("Bearer ")
            assert "resource_metadata=" in www_auth
            assert ".well-known/oauth-protected-resource" in www_auth

    def test_public_endpoints_skip_auth(self):
        """Test /health and /.well-known/* endpoints don't require auth."""
        from unittest.mock import patch

        with patch("modelcontextprotocol.middleware.oauth.Context"):
            from starlette.applications import Starlette
            from starlette.middleware import Middleware
            from starlette.responses import PlainTextResponse
            from starlette.routing import Route

            async def health_endpoint(request):
                return PlainTextResponse("OK")

            async def well_known_endpoint(request):
                return PlainTextResponse("metadata")

            app = Starlette(
                routes=[
                    Route("/health", health_endpoint),
                    Route("/.well-known/oauth-protected-resource", well_known_endpoint),
                ],
                middleware=[Middleware(OAuthMiddleware)],
            )

            client = TestClient(app)

            response = client.get("/health")
            assert response.status_code == 200
            assert response.text == "OK"

            response = client.get("/.well-known/oauth-protected-resource")
            assert response.status_code == 200
            assert response.text == "metadata"

    def test_client_credentials_bypass(self):
        """Test X-Client-Id/X-Client-Secret headers work as developer bypass."""
        from unittest.mock import Mock, patch

        with patch("modelcontextprotocol.middleware.oauth.Context") as MockContext:
            mock_ctx = Mock()
            mock_ctx.metadata = {}
            MockContext.get_current.return_value = mock_ctx

            from starlette.applications import Starlette
            from starlette.middleware import Middleware
            from starlette.responses import JSONResponse
            from starlette.routing import Route

            async def test_endpoint(request):
                ctx = MockContext.get_current()
                return JSONResponse(
                    {
                        "auth_type": ctx.metadata.get("auth_type"),
                        "bearer_token": ctx.metadata.get("bearer_token"),
                    }
                )

            app = Starlette(
                routes=[Route("/test", test_endpoint)],
                middleware=[Middleware(OAuthMiddleware)],
            )

            client = TestClient(app)
            response = client.get(
                "/test",
                headers={
                    "X-Client-Id": "test_client",
                    "X-Client-Secret": "test_secret",
                },
            )

            assert response.status_code == 200
            assert mock_ctx.metadata["auth_type"] == "client_credentials"
            assert mock_ctx.metadata.get("bearer_token") is None
