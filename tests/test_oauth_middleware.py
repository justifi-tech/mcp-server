"""Tests for OAuth 2.1 middleware."""

from __future__ import annotations

import pytest
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from modelcontextprotocol.middleware.oauth import OAuthMiddleware


@pytest.fixture
def mock_app():
    """Create a test Starlette application with OAuth middleware."""

    async def protected_endpoint(request: Request):
        """Protected endpoint that requires authentication."""
        auth_type = getattr(request.state, "auth_type", None)
        bearer_token = getattr(request.state, "bearer_token", None)

        response_data = {
            "auth_type": auth_type,
            "bearer_token": bearer_token,
        }
        return PlainTextResponse(str(response_data))

    async def public_endpoint(request: Request):
        """Public endpoint that doesn't require authentication."""
        return PlainTextResponse("public")

    async def health_endpoint(request: Request):
        """Health check endpoint."""
        return PlainTextResponse("OK")

    app = Starlette(
        routes=[
            Route("/protected", protected_endpoint),
            Route("/health", health_endpoint),
            Route("/.well-known/oauth-protected-resource", public_endpoint),
        ],
        middleware=[Middleware(OAuthMiddleware)],
    )

    return app


class TestOAuthMiddleware:
    """Essential tests for OAuthMiddleware authentication behavior."""

    def test_bearer_token_extraction(self, mock_app):
        """Test bearer token is extracted and stored in request state with oauth auth_type."""
        client = TestClient(mock_app)
        response = client.get(
            "/protected", headers={"Authorization": "Bearer test_token_12345"}
        )

        assert response.status_code == 200
        assert "auth_type': 'oauth'" in response.text
        assert "bearer_token': 'test_token_12345'" in response.text

    def test_returns_401_without_auth(self, mock_app):
        """Test requests without auth return 401 with WWW-Authenticate header."""
        client = TestClient(mock_app)
        response = client.get("/protected")

        assert response.status_code == 401
        assert response.text == "Unauthorized"
        assert "WWW-Authenticate" in response.headers

        www_auth = response.headers["WWW-Authenticate"]
        assert www_auth.startswith("Bearer ")
        assert "resource_metadata=" in www_auth
        assert ".well-known/oauth-protected-resource" in www_auth

    def test_public_endpoints_skip_auth(self, mock_app):
        """Test /health and /.well-known/* endpoints don't require auth."""
        client = TestClient(mock_app)

        response = client.get("/health")
        assert response.status_code == 200
        assert response.text == "OK"

        response = client.get("/.well-known/oauth-protected-resource")
        assert response.status_code == 200
        assert response.text == "public"
