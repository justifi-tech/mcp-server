"""Unit tests for JustiFi MCP tools.

Tests OAuth token handling, HTTP requests, and all four payment tools.
Uses respx to mock HTTP calls - no external API calls during testing.
"""

import os
import time
from unittest.mock import patch

import pytest
import respx
from httpx import Response

from tools.justifi import (
    _TOKEN_CACHE,
    _get_access_token,
    create_payment,
    list_payments,
    refund_payment,
    retrieve_payment,
)

# Test constants - not real credentials
TEST_CLIENT_ID = "test_client_id"
TEST_CLIENT_SECRET = "test_client_secret"  # noqa: S105
TEST_BASE_URL = "https://api.justifi.ai/v1"
TEST_ACCESS_TOKEN = "test_token"  # noqa: S105
TEST_ACCESS_TOKEN_123 = "test_token_123"  # noqa: S105
TEST_CACHED_TOKEN = "cached_token"  # noqa: S105
TEST_EXPIRED_TOKEN = "expired_token"  # noqa: S105
TEST_NEW_TOKEN = "new_token_456"  # noqa: S105


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
            "JUSTIFI_CLIENT_ID": TEST_CLIENT_ID,
            "JUSTIFI_CLIENT_SECRET": TEST_CLIENT_SECRET,
            "JUSTIFI_BASE_URL": TEST_BASE_URL,
        },
    ):
        yield


class TestTokenManagement:
    """Test OAuth token management functionality."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_access_token_success(self):
        """Test successful token retrieval."""
        # Mock OAuth token endpoint
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(
                200, json={"access_token": TEST_ACCESS_TOKEN_123, "expires_in": 3600}
            )
        )

        token = await _get_access_token()
        assert token == TEST_ACCESS_TOKEN_123
        assert _TOKEN_CACHE.token == TEST_ACCESS_TOKEN_123
        assert _TOKEN_CACHE.expires_at > time.time()

    @respx.mock
    @pytest.mark.asyncio
    async def test_token_caching(self):
        """Test that tokens are cached and reused."""
        # Set up a cached token
        _TOKEN_CACHE.token = TEST_CACHED_TOKEN
        _TOKEN_CACHE.expires_at = time.time() + 1800  # 30 minutes from now

        # Should return cached token without making HTTP request
        token = await _get_access_token()
        assert token == TEST_CACHED_TOKEN

    @respx.mock
    @pytest.mark.asyncio
    async def test_token_refresh_when_expired(self):
        """Test token refresh when cached token is expired."""
        # Set up an expired token
        _TOKEN_CACHE.token = TEST_EXPIRED_TOKEN
        _TOKEN_CACHE.expires_at = time.time() - 100  # Expired

        # Mock new token request
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(
                200,
                json={
                    "access_token": TEST_NEW_TOKEN,
                    "token_type": "Bearer",
                    "expires_in": 3600,
                },
            )
        )

        token = await _get_access_token()
        assert token == TEST_NEW_TOKEN
        assert _TOKEN_CACHE.token == TEST_NEW_TOKEN


class TestPaymentTools:
    """Test JustiFi payment tool functions."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_payment_success(self):
        """Test successful payment creation."""
        # Mock OAuth token
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(
                200, json={"access_token": TEST_ACCESS_TOKEN, "expires_in": 3600}
            )
        )

        # Mock payment creation
        respx.post("https://api.justifi.ai/v1/payments").mock(
            return_value=Response(
                201,
                json={
                    "id": "py_test123",
                    "amount": 1050,
                    "currency": "USD",
                    "status": "pending",
                },
            )
        )

        result = await create_payment(
            amount_cents=1050, currency="USD", idempotency_key="test_key_123"
        )

        assert isinstance(result, dict)
        assert result["id"] == "py_test123"
        assert result["amount"] == 1050
        assert result["currency"] == "USD"
        assert result["status"] == "pending"

    @respx.mock
    @pytest.mark.asyncio
    async def test_retrieve_payment_success(self):
        """Test successful payment retrieval."""
        # Mock OAuth token
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(
                200, json={"access_token": TEST_ACCESS_TOKEN, "expires_in": 3600}
            )
        )

        # Mock payment retrieval
        respx.get("https://api.justifi.ai/v1/payments/py_test123").mock(
            return_value=Response(
                200,
                json={
                    "id": "py_test123",
                    "amount": 2000,
                    "currency": "USD",
                    "status": "succeeded",
                },
            )
        )

        result = await retrieve_payment(payment_id="py_test123")
        assert isinstance(result, dict)
        assert result["id"] == "py_test123"
        assert result["amount"] == 2000
        assert result["status"] == "succeeded"

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_payments_success(self):
        """Test successful payment listing."""
        # Mock OAuth token
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(
                200, json={"access_token": TEST_ACCESS_TOKEN, "expires_in": 3600}
            )
        )

        # Mock payment listing
        respx.get("https://api.justifi.ai/v1/payments").mock(
            return_value=Response(
                200,
                json={
                    "data": [
                        {"id": "py_1", "amount": 1000, "status": "succeeded"},
                        {"id": "py_2", "amount": 2000, "status": "pending"},
                    ],
                    "page_info": {"has_next": False, "end_cursor": "cursor_123"},
                },
            )
        )

        result = await list_payments(limit=25)
        assert isinstance(result, dict)
        assert "data" in result
        assert len(result["data"]) == 2
        assert result["data"][0]["id"] == "py_1"
        assert result["data"][1]["id"] == "py_2"
        assert "page_info" in result

    @respx.mock
    @pytest.mark.asyncio
    async def test_refund_payment_success(self):
        """Test successful payment refund."""
        # Mock OAuth token
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(
                200, json={"access_token": TEST_ACCESS_TOKEN, "expires_in": 3600}
            )
        )

        # Mock refund creation
        respx.post("https://api.justifi.ai/v1/payments/py_test123/refunds").mock(
            return_value=Response(
                201,
                json={
                    "id": "rf_test456",
                    "payment_id": "py_test123",
                    "amount": 1000,
                    "status": "succeeded",
                },
            )
        )

        result = await refund_payment(payment_id="py_test123", amount_cents=1000)

        assert isinstance(result, dict)
        assert result["id"] == "rf_test456"
        assert result["payment_id"] == "py_test123"
        assert result["amount"] == 1000
        assert result["status"] == "succeeded"



    @respx.mock
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in payment operations."""
        # Mock OAuth token
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(
                200, json={"access_token": TEST_ACCESS_TOKEN, "expires_in": 3600}
            )
        )

        # Mock API error
        respx.post("https://api.justifi.ai/v1/payments").mock(
            return_value=Response(
                400,
                json={"error": "invalid_request", "message": "Amount must be positive"},
            )
        )

        # Test that the function raises an HTTPStatusError for 400 responses
        from httpx import HTTPStatusError

        with pytest.raises(HTTPStatusError):
            await create_payment(
                amount_cents=-100,  # Invalid amount
                currency="USD",
                idempotency_key="test_key",
            )


class TestMCPIntegration:
    """Test MCP server integration."""

    @pytest.mark.asyncio
    async def test_mcp_server_import(self):
        """Test that MCP server can be imported without errors."""
        try:
            from main import handle_call_tool, handle_list_tools, server

            assert server is not None
            assert callable(handle_list_tools)
            assert callable(handle_call_tool)
        except ImportError as e:
            pytest.fail(f"Failed to import MCP server components: {e}")

    @pytest.mark.asyncio
    async def test_tool_listing(self):
        """Test that tools are properly listed."""
        from main import handle_list_tools

        tools = await handle_list_tools()
        assert len(tools) == 9  # Updated: removed list_refunds (endpoint doesn't exist)

        tool_names = [tool.name for tool in tools]
        # Payment tools
        assert "create_payment" in tool_names
        assert "retrieve_payment" in tool_names
        assert "list_payments" in tool_names
        assert "refund_payment" in tool_names
        # Payment method tools
        assert "create_payment_method" in tool_names
        assert "retrieve_payment_method" in tool_names
        # Payout tools
        assert "retrieve_payout" in tool_names
        assert "list_payouts" in tool_names
        # Balance tools
        assert "list_balance_transactions" in tool_names

    @respx.mock
    @pytest.mark.asyncio
    async def test_tool_execution(self):
        """Test tool execution through MCP interface."""
        from main import handle_call_tool

        # Mock OAuth token
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(
                200, json={"access_token": TEST_ACCESS_TOKEN, "expires_in": 3600}
            )
        )

        # Mock payment creation
        respx.post("https://api.justifi.ai/v1/payments").mock(
            return_value=Response(
                201,
                json={
                    "id": "py_test123",
                    "amount": 1050,
                    "currency": "USD",
                    "status": "pending",
                },
            )
        )

        result = await handle_call_tool(
            name="create_payment",
            arguments={
                "amount_cents": 1050,
                "currency": "USD",
                "idempotency_key": "test_key",
            },
        )

        assert len(result) == 1
        assert result[0].type == "text"
        assert "py_test123" in result[0].text
