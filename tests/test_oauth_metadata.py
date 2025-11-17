"""Test OAuth 2.0 Protected Resource Metadata (RFC 9728) functionality."""

import os
from unittest.mock import patch

import pytest

from modelcontextprotocol.oauth_metadata import get_protected_resource_metadata
from python.config import JustiFiConfig


class TestOAuthMetadata:
    """Test OAuth metadata generation per RFC 9728."""

    def test_default_configuration(self):
        """Test metadata with default Auth0 configuration."""
        with patch.dict(
            os.environ,
            {
                "JUSTIFI_CLIENT_ID": "test_id",
                "JUSTIFI_CLIENT_SECRET": "test_secret",
            },
        ):
            config = JustiFiConfig()
            metadata = get_protected_resource_metadata(config)

            assert "authorization_servers" in metadata
            assert len(metadata["authorization_servers"]) == 1
            assert (
                metadata["authorization_servers"][0]["issuer"]
                == "https://justifi.us.auth0.com"
            )
            assert "scopes_supported" in metadata
            assert metadata["scopes_supported"] == []

    def test_custom_auth0_domain(self):
        """Test metadata with custom Auth0 domain."""
        with patch.dict(
            os.environ,
            {
                "JUSTIFI_CLIENT_ID": "test_id",
                "JUSTIFI_CLIENT_SECRET": "test_secret",
                "JUSTIFI_AUTH0_DOMAIN": "custom.auth0.com",
            },
        ):
            config = JustiFiConfig()
            metadata = get_protected_resource_metadata(config)

            assert (
                metadata["authorization_servers"][0]["issuer"]
                == "https://custom.auth0.com"
            )

    def test_oauth_scopes_from_env(self):
        """Test metadata with OAuth scopes from environment."""
        with patch.dict(
            os.environ,
            {
                "JUSTIFI_CLIENT_ID": "test_id",
                "JUSTIFI_CLIENT_SECRET": "test_secret",
                "JUSTIFI_OAUTH_SCOPES": "read:payments,write:payments,read:refunds",
            },
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
                "JUSTIFI_OAUTH_SCOPES": "read:payments , write:payments,  read:refunds",
            },
        ):
            config = JustiFiConfig()
            metadata = get_protected_resource_metadata(config)

            assert metadata["scopes_supported"] == [
                "read:payments",
                "write:payments",
                "read:refunds",
            ]

    def test_programmatic_configuration(self):
        """Test metadata with programmatically set configuration."""
        with patch.dict(
            os.environ,
            {
                "JUSTIFI_CLIENT_ID": "test_id",
                "JUSTIFI_CLIENT_SECRET": "test_secret",
            },
        ):
            config = JustiFiConfig(
                auth0_domain="example.auth0.com",
                auth0_audience="https://api.example.com",
                oauth_scopes=["read:payments", "write:payments"],
            )
            metadata = get_protected_resource_metadata(config)

            assert (
                metadata["authorization_servers"][0]["issuer"]
                == "https://example.auth0.com"
            )
            assert metadata["scopes_supported"] == [
                "read:payments",
                "write:payments",
            ]

    def test_metadata_structure(self):
        """Test metadata conforms to RFC 9728 structure."""
        with patch.dict(
            os.environ,
            {
                "JUSTIFI_CLIENT_ID": "test_id",
                "JUSTIFI_CLIENT_SECRET": "test_secret",
            },
        ):
            config = JustiFiConfig()
            metadata = get_protected_resource_metadata(config)

            assert isinstance(metadata, dict)
            assert "authorization_servers" in metadata
            assert isinstance(metadata["authorization_servers"], list)
            assert len(metadata["authorization_servers"]) > 0
            assert "issuer" in metadata["authorization_servers"][0]
            assert "scopes_supported" in metadata
            assert isinstance(metadata["scopes_supported"], list)
