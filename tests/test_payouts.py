"""
Unit tests for JustiFi Payout MCP tools.

Tests payout retrieval and listing functionality.
Uses respx to mock HTTP calls - no external API calls during testing.
"""

import os
from unittest.mock import patch

import pytest
import respx
from httpx import Response

from tools.justifi import (
    _TOKEN_CACHE,
    list_payouts,
    retrieve_payout,
)


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
            "JUSTIFI_CLIENT_SECRET": "test_client_secret",
            "JUSTIFI_BASE_URL": "https://api.justifi.ai/v1",
        },
    ):
        yield


class TestPayoutTools:
    """Test JustiFi payout tool functions."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_retrieve_payout_success(self):
        """Test successful payout retrieval."""
        # Mock OAuth token
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(
                200, json={"access_token": "test_token", "expires_in": 3600}
            )
        )

        # Mock payout retrieval
        respx.get("https://api.justifi.ai/v1/payouts/po_test123").mock(
            return_value=Response(
                200,
                json={
                    "id": "po_test123",
                    "amount": 50000,
                    "currency": "USD",
                    "status": "paid",
                    "payout_type": "standard",
                    "arrival_date": "2025-01-26",
                },
            )
        )

        result = await retrieve_payout(payout_id="po_test123")
        assert isinstance(result, dict)
        assert result["id"] == "po_test123"
        assert result["amount"] == 50000
        assert result["status"] == "paid"
        assert result["payout_type"] == "standard"

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_payouts_success(self):
        """Test successful payout listing."""
        # Mock OAuth token
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(
                200, json={"access_token": "test_token", "expires_in": 3600}
            )
        )

        # Mock payout listing
        respx.get("https://api.justifi.ai/v1/payouts").mock(
            return_value=Response(
                200,
                json={
                    "data": [
                        {
                            "id": "po_1",
                            "amount": 25000,
                            "status": "paid",
                            "payout_type": "standard",
                        },
                        {
                            "id": "po_2",
                            "amount": 75000,
                            "status": "pending",
                            "payout_type": "expedited",
                        },
                    ],
                    "page_info": {"has_next": False, "end_cursor": "cursor_456"},
                },
            )
        )

        result = await list_payouts(limit=25)
        assert isinstance(result, dict)
        assert "data" in result
        assert len(result["data"]) == 2
        assert result["data"][0]["id"] == "po_1"
        assert result["data"][1]["id"] == "po_2"
        assert "page_info" in result

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_payouts_with_pagination(self):
        """Test payout listing with pagination parameters."""
        # Mock OAuth token
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(
                200, json={"access_token": "test_token", "expires_in": 3600}
            )
        )

        # Mock payout listing with pagination
        respx.get("https://api.justifi.ai/v1/payouts").mock(
            return_value=Response(
                200,
                json={
                    "data": [{"id": "po_3", "amount": 10000, "status": "paid"}],
                    "page_info": {"has_next": True, "end_cursor": "cursor_789"},
                },
            )
        )

        result = await list_payouts(
            limit=10, after_cursor="cursor_123", before_cursor="cursor_456"
        )
        assert isinstance(result, dict)
        assert "data" in result
        assert len(result["data"]) == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_retrieve_payout_not_found(self):
        """Test payout retrieval with not found error."""
        # Mock OAuth token
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(
                200, json={"access_token": "test_token", "expires_in": 3600}
            )
        )

        # Mock 404 error
        respx.get("https://api.justifi.ai/v1/payouts/po_nonexistent").mock(
            return_value=Response(
                404,
                json={
                    "error": "not_found",
                    "message": "Payout not found",
                },
            )
        )

        with pytest.raises(Exception):
            await retrieve_payout(payout_id="po_nonexistent")
