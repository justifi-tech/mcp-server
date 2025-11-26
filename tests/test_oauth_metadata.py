"""Test OAuth 2.0 Metadata (RFC 9728 and RFC 8414) functionality."""

import os
from unittest.mock import patch

from modelcontextprotocol.oauth_metadata import (
    get_authorization_server_metadata,
    get_protected_resource_metadata,
)
from python.config import JustiFiConfig


class TestProtectedResourceMetadata:
    """Test OAuth Protected Resource Metadata per RFC 9728."""

    def test_with_mcp_server_url(self):
        """Test metadata with MCP server URL configured."""
        config = JustiFiConfig(
            client_id="test_id",
            client_secret="test_secret",
            mcp_server_url="https://mcp.justifi.ai",
            oauth_scopes=["read:payments", "write:payments"],
        )
        metadata = get_protected_resource_metadata(config)

        assert "authorization_servers" in metadata
        assert len(metadata["authorization_servers"]) == 1
        assert (
            metadata["authorization_servers"][0]["issuer"] == "https://mcp.justifi.ai"
        )
        assert metadata["resource"] == "https://mcp.justifi.ai"
        assert metadata["scopes_supported"] == ["read:payments", "write:payments"]

    def test_without_mcp_server_url(self):
        """Test metadata without MCP server URL."""
        with patch.dict(os.environ, {}, clear=True):
            config = JustiFiConfig(
                client_id="test_id",
                client_secret="test_secret",
            )
            metadata = get_protected_resource_metadata(config)

            assert "authorization_servers" in metadata
            assert metadata["authorization_servers"][0]["issuer"] is None
            assert "resource" not in metadata
            assert metadata["scopes_supported"] == []

    def test_oauth_scopes_from_env(self):
        """Test metadata with OAuth scopes from environment."""
        with patch.dict(
            os.environ,
            {
                "JUSTIFI_CLIENT_ID": "test_id",
                "JUSTIFI_CLIENT_SECRET": "test_secret",
                "OAUTH_SCOPES": "read:payments,write:payments,read:refunds",
                "MCP_SERVER_URL": "https://mcp.example.com",
            },
            clear=True,
        ):
            config = JustiFiConfig()
            metadata = get_protected_resource_metadata(config)

            assert metadata["scopes_supported"] == [
                "read:payments",
                "write:payments",
                "read:refunds",
            ]

    def test_oauth_scopes_with_whitespace(self):
        """Test metadata handles scopes with extra whitespace."""
        with patch.dict(
            os.environ,
            {
                "JUSTIFI_CLIENT_ID": "test_id",
                "JUSTIFI_CLIENT_SECRET": "test_secret",
                "OAUTH_SCOPES": "read:payments , write:payments,  read:refunds",
            },
            clear=True,
        ):
            config = JustiFiConfig()
            metadata = get_protected_resource_metadata(config)

            assert metadata["scopes_supported"] == [
                "read:payments",
                "write:payments",
                "read:refunds",
            ]

    def test_metadata_structure(self):
        """Test metadata conforms to RFC 9728 structure."""
        config = JustiFiConfig(
            client_id="test_id",
            client_secret="test_secret",
            mcp_server_url="https://mcp.justifi.ai",
        )
        metadata = get_protected_resource_metadata(config)

        assert isinstance(metadata, dict)
        assert "authorization_servers" in metadata
        assert isinstance(metadata["authorization_servers"], list)
        assert len(metadata["authorization_servers"]) > 0
        assert "issuer" in metadata["authorization_servers"][0]
        assert "scopes_supported" in metadata
        assert isinstance(metadata["scopes_supported"], list)


class TestAuthorizationServerMetadata:
    """Test OAuth Authorization Server Metadata per RFC 8414."""

    def test_default_configuration(self):
        """Test metadata with default Auth0 configuration."""
        config = JustiFiConfig(
            client_id="test_id",
            client_secret="test_secret",
            mcp_server_url="https://mcp.justifi.ai",
        )
        metadata = get_authorization_server_metadata(config)

        # Should point to Auth0 for authorization/token
        assert metadata["issuer"] == "https://justifi.us.auth0.com"
        assert (
            metadata["authorization_endpoint"]
            == "https://justifi.us.auth0.com/authorize"
        )
        assert metadata["token_endpoint"] == "https://justifi.us.auth0.com/oauth/token"

        # Should point to MCP server for registration
        assert metadata["registration_endpoint"] == "https://mcp.justifi.ai/register"

    def test_custom_oauth_issuer(self):
        """Test metadata with custom OAuth issuer."""
        config = JustiFiConfig(
            client_id="test_id",
            client_secret="test_secret",
            oauth_issuer="https://custom.auth0.com",
            mcp_server_url="https://mcp.justifi.ai",
        )
        metadata = get_authorization_server_metadata(config)

        assert metadata["issuer"] == "https://custom.auth0.com"
        assert (
            metadata["authorization_endpoint"] == "https://custom.auth0.com/authorize"
        )
        assert metadata["token_endpoint"] == "https://custom.auth0.com/oauth/token"

    def test_without_mcp_server_url(self):
        """Test metadata without MCP server URL."""
        config = JustiFiConfig(
            client_id="test_id",
            client_secret="test_secret",
        )
        metadata = get_authorization_server_metadata(config)

        # Should still have auth endpoints
        assert "authorization_endpoint" in metadata
        assert "token_endpoint" in metadata
        # Should not have registration endpoint without MCP server URL
        assert "registration_endpoint" not in metadata

    def test_oauth_capabilities(self):
        """Test OAuth capability fields."""
        config = JustiFiConfig(
            client_id="test_id",
            client_secret="test_secret",
        )
        metadata = get_authorization_server_metadata(config)

        assert "code" in metadata["response_types_supported"]
        assert "authorization_code" in metadata["grant_types_supported"]
        assert "refresh_token" in metadata["grant_types_supported"]
        assert "S256" in metadata["code_challenge_methods_supported"]

    def test_scopes_included(self):
        """Test that configured scopes are included."""
        config = JustiFiConfig(
            client_id="test_id",
            client_secret="test_secret",
            oauth_scopes=["read:payments", "write:payments"],
        )
        metadata = get_authorization_server_metadata(config)

        assert metadata["scopes_supported"] == ["read:payments", "write:payments"]
