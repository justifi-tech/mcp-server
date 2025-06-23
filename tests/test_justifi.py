"""
Unit tests for JustiFi MCP tools.

Tests OAuth token handling, HTTP requests, and all four payment tools.
Uses respx to mock HTTP calls - no external API calls during testing.
"""
import asyncio
import os
import time
from unittest.mock import patch

import pytest
import respx
from httpx import Response

from tools.justifi import (
    create_payment,
    retrieve_payment,
    list_payments,
    refund_payment,
    _get_access_token,
    _TOKEN_CACHE,
)


@pytest.fixture(autouse=True)
def clear_token_cache():
    """Clear token cache before each test."""
    _TOKEN_CACHE.token = None
    _TOKEN_CACHE.expires_at = 0.0


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for testing."""
    with patch.dict(os.environ, {
        "JUSTIFI_CLIENT_ID": "test_client_id",
        "JUSTIFI_CLIENT_SECRET": "test_client_secret",
        "JUSTIFI_BASE_URL": "https://api.justifi.ai/v1"
    }):
        yield


class TestTokenManagement:
    """Test OAuth token management functionality."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_access_token_success(self):
        """Test successful token retrieval."""
        # Mock OAuth token endpoint
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json={
                "access_token": "test_token_123",
                "token_type": "Bearer",
                "expires_in": 3600
            })
        )

        token = await _get_access_token()
        assert token == "test_token_123"
        assert _TOKEN_CACHE.token == "test_token_123"
        assert _TOKEN_CACHE.expires_at > time.time()

    @respx.mock
    @pytest.mark.asyncio
    async def test_token_caching(self):
        """Test that tokens are cached and reused."""
        # Set up a cached token
        _TOKEN_CACHE.token = "cached_token"
        _TOKEN_CACHE.expires_at = time.time() + 1800  # 30 minutes from now

        # Should return cached token without making HTTP request
        token = await _get_access_token()
        assert token == "cached_token"

    @respx.mock
    @pytest.mark.asyncio
    async def test_token_refresh_when_expired(self):
        """Test token refresh when cached token is expired."""
        # Set up an expired token
        _TOKEN_CACHE.token = "expired_token"
        _TOKEN_CACHE.expires_at = time.time() - 100  # Expired

        # Mock new token request
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json={
                "access_token": "new_token_456",
                "token_type": "Bearer",
                "expires_in": 3600
            })
        )

        token = await _get_access_token()
        assert token == "new_token_456"
        assert _TOKEN_CACHE.token == "new_token_456"


class TestPaymentTools:
    """Test JustiFi payment tool functions."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_payment_success(self):
        """Test successful payment creation."""
        # Mock OAuth token
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json={
                "access_token": "test_token",
                "expires_in": 3600
            })
        )

        # Mock payment creation
        respx.post("https://api.justifi.ai/v1/payments").mock(
            return_value=Response(201, json={
                "id": "py_test123",
                "amount": 1050,
                "currency": "USD",
                "status": "pending"
            })
        )

        result = await create_payment(
            amount_cents=1050,
            currency="USD",
            idempotency_key="test_key_123"
        )

        assert "py_test123" in result
        assert "1050" in result

    @respx.mock
    @pytest.mark.asyncio
    async def test_retrieve_payment_success(self):
        """Test successful payment retrieval."""
        # Mock OAuth token
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json={
                "access_token": "test_token",
                "expires_in": 3600
            })
        )

        # Mock payment retrieval
        respx.get("https://api.justifi.ai/v1/payments/py_test123").mock(
            return_value=Response(200, json={
                "id": "py_test123",
                "amount": 2000,
                "currency": "USD",
                "status": "succeeded"
            })
        )

        result = await retrieve_payment(payment_id="py_test123")
        assert "py_test123" in result
        assert "succeeded" in result

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_payments_success(self):
        """Test successful payment listing."""
        # Mock OAuth token
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json={
                "access_token": "test_token",
                "expires_in": 3600
            })
        )

        # Mock payment listing
        respx.get("https://api.justifi.ai/v1/payments").mock(
            return_value=Response(200, json={
                "data": [
                    {"id": "py_1", "amount": 1000, "status": "succeeded"},
                    {"id": "py_2", "amount": 2000, "status": "pending"}
                ],
                "page_info": {
                    "has_next": False,
                    "end_cursor": "cursor_123"
                }
            })
        )

        result = await list_payments(limit=25)
        assert "py_1" in result
        assert "py_2" in result

    @respx.mock
    @pytest.mark.asyncio
    async def test_refund_payment_success(self):
        """Test successful payment refund."""
        # Mock OAuth token
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json={
                "access_token": "test_token",
                "expires_in": 3600
            })
        )

        # Mock refund creation
        respx.post("https://api.justifi.ai/v1/payments/py_test123/refunds").mock(
            return_value=Response(201, json={
                "id": "rf_test456",
                "payment_id": "py_test123",
                "amount": 1000,
                "status": "succeeded"
            })
        )

        result = await refund_payment(
            payment_id="py_test123",
            amount_cents=1000
        )

        assert "rf_test456" in result
        assert "succeeded" in result

    @respx.mock
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in payment operations."""
        # Mock OAuth token
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json={
                "access_token": "test_token",
                "expires_in": 3600
            })
        )

        # Mock API error
        respx.post("https://api.justifi.ai/v1/payments").mock(
            return_value=Response(400, json={
                "error": "invalid_request",
                "message": "Amount must be positive"
            })
        )

        result = await create_payment(
            amount_cents=-100,  # Invalid amount
            currency="USD",
            idempotency_key="test_key"
        )

        assert "Error" in result
        assert "400" in result


class TestMCPIntegration:
    """Test MCP server integration."""

    @pytest.mark.asyncio
    async def test_mcp_server_import(self):
        """Test that MCP server can be imported without errors."""
        try:
            from main import server, handle_list_tools, handle_call_tool
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
        assert len(tools) == 4
        
        tool_names = [tool.name for tool in tools]
        assert "create_payment" in tool_names
        assert "retrieve_payment" in tool_names
        assert "list_payments" in tool_names
        assert "refund_payment" in tool_names

    @respx.mock
    @pytest.mark.asyncio
    async def test_tool_execution(self):
        """Test tool execution through MCP interface."""
        from main import handle_call_tool
        
        # Mock OAuth token
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json={
                "access_token": "test_token",
                "expires_in": 3600
            })
        )

        # Mock payment creation
        respx.post("https://api.justifi.ai/v1/payments").mock(
            return_value=Response(201, json={
                "id": "py_test123",
                "amount": 1050,
                "currency": "USD",
                "status": "pending"
            })
        )

        result = await handle_call_tool(
            name="create_payment",
            arguments={
                "amount_cents": 1050,
                "currency": "USD",
                "idempotency_key": "test_key"
            }
        )

        assert len(result) == 1
        assert result[0].type == "text"
        assert "py_test123" in result[0].text 