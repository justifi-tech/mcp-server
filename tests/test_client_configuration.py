"""Tests for JustiFiClient configuration."""

import os
from unittest.mock import patch

import pytest

from python.core import AuthenticationError, JustiFiClient


def test_base_url_priority():
    """Test base URL priority: explicit parameter > env var > default."""
    # Explicit parameter wins
    with patch.dict(os.environ, {"JUSTIFI_BASE_URL": "https://env.com"}):
        client = JustiFiClient(
            "test_id", "test_secret", base_url="https://explicit.com"
        )
        assert client.base_url == "https://explicit.com"

    # Environment variable fallback
    with patch.dict(os.environ, {"JUSTIFI_BASE_URL": "https://env.com"}):
        client = JustiFiClient("test_id", "test_secret")
        assert client.base_url == "https://env.com"

    # Default fallback
    with patch.dict(os.environ, {}, clear=True):
        client = JustiFiClient("test_id", "test_secret")
        assert client.base_url == "https://api.justifi.ai"


def test_url_normalization():
    """Test URL normalization removes trailing slashes and /v1 suffix."""
    client = JustiFiClient(
        "test_id", "test_secret", base_url="https://api.justifi.ai/v1/"
    )
    assert client.base_url == "https://api.justifi.ai"


def test_missing_credentials():
    """Test that missing credentials raise AuthenticationError."""
    with pytest.raises(AuthenticationError):
        JustiFiClient("", "secret")
