"""Unit tests for JustiFi Balance Transaction MCP tools.

Tests balance transaction listing functionality.
Uses respx to mock HTTP calls - no external API calls during testing.
"""

import os
from unittest.mock import patch

import httpx
import pytest
import respx
from httpx import Response

from tools.justifi import (
    _TOKEN_CACHE,
    list_balance_transactions,
)

# Test constants - not real credentials
TEST_CLIENT_ID = "test_client_id"
TEST_CLIENT_SECRET = "test_client_secret"  # noqa: S105
TEST_BASE_URL = "https://api.justifi.ai/v1"
TEST_ACCESS_TOKEN = "test_token"  # noqa: S105


@pytest.fixture(autouse=True)
def clear_token_cache():
    """Clear token cache before each test."""
    _TOKEN_CACHE.token = None
    _TOKEN_CACHE.expires_at = 0.0


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for testing."""
    with patch.dict(
        os.environ,
        {
            "JUSTIFI_CLIENT_ID": "test_client_id",
            "JUSTIFI_CLIENT_SECRET": TEST_CLIENT_SECRET,
            "JUSTIFI_BASE_URL": "https://api.justifi.ai/v1",
        },
    ):
        yield


class TestBalanceTransactionTools:
    """Test JustiFi balance transaction tool functions."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_balance_transactions_success(self):
        """Test successful balance transaction listing."""
        # Mock OAuth token
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(
                200, json={"access_token": TEST_ACCESS_TOKEN, "expires_in": 3600}
            )
        )

        # Mock balance transaction listing
        respx.get("https://api.justifi.ai/v1/balance_transactions").mock(
            return_value=Response(
                200,
                json={
                    "data": [
                        {
                            "id": "bt_1",
                            "amount": 1000,
                            "currency": "USD",
                            "type": "payment",
                            "status": "completed",
                            "created_at": "2025-01-25T10:00:00Z",
                        },
                        {
                            "id": "bt_2",
                            "amount": -50,
                            "currency": "USD",
                            "type": "fee",
                            "status": "completed",
                            "created_at": "2025-01-25T10:01:00Z",
                        },
                        {
                            "id": "bt_3",
                            "amount": -200,
                            "currency": "USD",
                            "type": "refund",
                            "status": "completed",
                            "created_at": "2025-01-25T11:00:00Z",
                        },
                    ],
                    "page_info": {"has_next": False, "end_cursor": "cursor_789"},
                },
            )
        )

        result = await list_balance_transactions(limit=25)
        assert isinstance(result, dict)
        assert "data" in result
        assert len(result["data"]) == 3
        assert result["data"][0]["type"] == "payment"
        assert result["data"][1]["type"] == "fee"
        assert result["data"][2]["type"] == "refund"
        assert "page_info" in result

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_balance_transactions_with_pagination(self):
        """Test balance transaction listing with pagination parameters."""
        # Mock OAuth token
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(
                200, json={"access_token": TEST_ACCESS_TOKEN, "expires_in": 3600}
            )
        )

        # Mock balance transaction listing with pagination
        respx.get("https://api.justifi.ai/v1/balance_transactions").mock(
            return_value=Response(
                200,
                json={
                    "data": [
                        {
                            "id": "bt_4",
                            "amount": 2000,
                            "currency": "USD",
                            "type": "payout",
                            "status": "pending",
                        }
                    ],
                    "page_info": {"has_next": True, "end_cursor": "cursor_next"},
                },
            )
        )

        result = await list_balance_transactions(
            limit=10, after_cursor="cursor_123", before_cursor="cursor_456"
        )
        assert isinstance(result, dict)
        assert "data" in result
        assert len(result["data"]) == 1
        assert result["data"][0]["type"] == "payout"

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_balance_transactions_empty_result(self):
        """Test balance transaction listing with empty result."""
        # Mock OAuth token
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(
                200, json={"access_token": TEST_ACCESS_TOKEN, "expires_in": 3600}
            )
        )

        # Mock empty balance transaction listing
        respx.get("https://api.justifi.ai/v1/balance_transactions").mock(
            return_value=Response(
                200,
                json={
                    "data": [],
                    "page_info": {"has_next": False, "end_cursor": None},
                },
            )
        )

        result = await list_balance_transactions(limit=25)
        assert isinstance(result, dict)
        assert "data" in result
        assert len(result["data"]) == 0
        assert "page_info" in result

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_balance_transactions_error_handling(self):
        """Test error handling in balance transaction listing."""
        # Mock OAuth token
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(
                200, json={"access_token": TEST_ACCESS_TOKEN, "expires_in": 3600}
            )
        )

        # Mock API error
        respx.get("https://api.justifi.ai/v1/balance_transactions").mock(
            return_value=Response(
                403,
                json={
                    "error": "forbidden",
                    "message": "Insufficient permissions",
                },
            )
        )

        with pytest.raises(httpx.HTTPStatusError):
            await list_balance_transactions(limit=25)
