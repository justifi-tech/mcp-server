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


def test_platform_account_id_stored():
    """Test that platform_account_id is stored on client."""
    client = JustiFiClient("test_id", "test_secret", platform_account_id="acc_123")
    assert client.platform_account_id == "acc_123"


def test_platform_account_id_none_by_default():
    """Test that platform_account_id is None by default."""
    client = JustiFiClient("test_id", "test_secret")
    assert client.platform_account_id is None


class TestSubAccountHeader:
    """Tests for Sub-Account header logic in requests."""

    @pytest.fixture
    def mock_client(self):
        """Create a client with platform_account_id for testing."""
        return JustiFiClient(
            "test_id",
            "test_secret",
            base_url="https://api.justifi.ai",
            bearer_token="test_token",
            platform_account_id="acc_platform",
        )

    @pytest.fixture
    def mock_client_no_platform(self):
        """Create a client without platform_account_id for testing."""
        return JustiFiClient(
            "test_id",
            "test_secret",
            base_url="https://api.justifi.ai",
            bearer_token="test_token",
        )

    @pytest.mark.asyncio
    async def test_sub_account_header_from_platform_account_id(self, mock_client):
        """Test Sub-Account header is set from platform_account_id."""
        import respx
        from httpx import Response

        with respx.mock:
            route = respx.get("https://api.justifi.ai/v1/payments").mock(
                return_value=Response(200, json={"data": []})
            )

            await mock_client.request("GET", "/v1/payments")

            assert route.called
            request = route.calls[0].request
            assert request.headers.get("Sub-Account") == "acc_platform"

    @pytest.mark.asyncio
    async def test_sub_account_id_overrides_platform_account_id(self, mock_client):
        """Test sub_account_id parameter overrides platform_account_id."""
        import respx
        from httpx import Response

        with respx.mock:
            route = respx.get("https://api.justifi.ai/v1/payments").mock(
                return_value=Response(200, json={"data": []})
            )

            await mock_client.request(
                "GET", "/v1/payments", sub_account_id="acc_override"
            )

            assert route.called
            request = route.calls[0].request
            assert request.headers.get("Sub-Account") == "acc_override"

    @pytest.mark.asyncio
    async def test_no_sub_account_header_when_not_configured(
        self, mock_client_no_platform
    ):
        """Test no Sub-Account header when platform_account_id not set."""
        import respx
        from httpx import Response

        with respx.mock:
            route = respx.get("https://api.justifi.ai/v1/payments").mock(
                return_value=Response(200, json={"data": []})
            )

            await mock_client_no_platform.request("GET", "/v1/payments")

            assert route.called
            request = route.calls[0].request
            assert "Sub-Account" not in request.headers

    @pytest.mark.asyncio
    async def test_sub_account_id_sets_header_without_platform_account_id(
        self, mock_client_no_platform
    ):
        """Test sub_account_id sets header even without platform_account_id."""
        import respx
        from httpx import Response

        with respx.mock:
            route = respx.get("https://api.justifi.ai/v1/payments").mock(
                return_value=Response(200, json={"data": []})
            )

            await mock_client_no_platform.request(
                "GET", "/v1/payments", sub_account_id="acc_explicit"
            )

            assert route.called
            request = route.calls[0].request
            assert request.headers.get("Sub-Account") == "acc_explicit"

    @pytest.mark.asyncio
    async def test_extra_headers_sub_account_not_overwritten(self, mock_client):
        """Test extra_headers Sub-Account is not overwritten by platform_account_id."""
        import respx
        from httpx import Response

        with respx.mock:
            route = respx.get("https://api.justifi.ai/v1/payments").mock(
                return_value=Response(200, json={"data": []})
            )

            await mock_client.request(
                "GET",
                "/v1/payments",
                extra_headers={"Sub-Account": "acc_extra_header"},
            )

            assert route.called
            request = route.calls[0].request
            assert request.headers.get("Sub-Account") == "acc_extra_header"
