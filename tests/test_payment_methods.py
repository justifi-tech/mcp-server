"""Unit tests for JustiFi Payment Method MCP tools.

Tests payment method creation and retrieval functionality.
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
    create_payment_method,
    retrieve_payment_method,
)

# Test constants - not real credentials
TEST_CLIENT_ID = "test_client_id"
TEST_CLIENT_SECRET = "test_client_secret"  # noqa: S105
TEST_BASE_URL = "https://api.justifi.ai/v1"
TEST_ACCESS_TOKEN = "test_token"  # noqa: S105
TEST_PAYMENT_METHOD_ID = "pm_test123"
TEST_NONEXISTENT_PM_ID = "pm_nonexistent"


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
            "JUSTIFI_BASE_URL": "https://api.justifi.ai/v1",
        },
    ):
        yield


class TestPaymentMethodTools:
    """Test JustiFi payment method tool functions."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_payment_method_success(self):
        """Test successful payment method creation."""
        # Mock OAuth token
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(
                200, json={"access_token": TEST_ACCESS_TOKEN, "expires_in": 3600}
            )
        )

        # Mock payment method creation
        respx.post("https://api.justifi.ai/v1/payment_methods").mock(
            return_value=Response(
                201,
                json={
                    "id": TEST_PAYMENT_METHOD_ID,
                    "customer_id": "cust_456",
                    "type": "card",
                    "card": {
                        "brand": "visa",
                        "last4": "4242",
                        "exp_month": 12,
                        "exp_year": 2025,
                    },
                    "status": "active",
                },
            )
        )

        result = await create_payment_method(
            customer_id="cust_456",
            card_number="4242424242424242",
            exp_month=12,
            exp_year=2025,
            cvc="123",
        )

        assert isinstance(result, dict)
        assert result["id"] == TEST_PAYMENT_METHOD_ID
        assert result["customer_id"] == "cust_456"
        assert result["type"] == "card"
        assert result["card"]["last4"] == "4242"

    @respx.mock
    @pytest.mark.asyncio
    async def test_retrieve_payment_method_success(self):
        """Test successful payment method retrieval."""
        # Mock OAuth token
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(
                200, json={"access_token": TEST_ACCESS_TOKEN, "expires_in": 3600}
            )
        )

        # Mock payment method retrieval
        respx.get("https://api.justifi.ai/v1/payment_methods/pm_test123").mock(
            return_value=Response(
                200,
                json={
                    "id": TEST_PAYMENT_METHOD_ID,
                    "customer_id": "cust_456",
                    "type": "card",
                    "card": {
                        "brand": "visa",
                        "last4": "4242",
                        "exp_month": 12,
                        "exp_year": 2025,
                    },
                    "status": "active",
                },
            )
        )

        result = await retrieve_payment_method(payment_method_token=TEST_PAYMENT_METHOD_ID)
        assert isinstance(result, dict)
        assert result["id"] == TEST_PAYMENT_METHOD_ID
        assert result["customer_id"] == "cust_456"
        assert result["type"] == "card"

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_payment_method_error_handling(self):
        """Test error handling in payment method creation."""
        # Mock OAuth token
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(
                200, json={"access_token": TEST_ACCESS_TOKEN, "expires_in": 3600}
            )
        )

        # Mock API error
        respx.post("https://api.justifi.ai/v1/payment_methods").mock(
            return_value=Response(
                400,
                json={
                    "error": "invalid_request",
                    "message": "Invalid card number",
                },
            )
        )

        with pytest.raises(httpx.HTTPStatusError):
            await create_payment_method(
                customer_id="cust_456",
                card_number="invalid_card",
            )

    @respx.mock
    @pytest.mark.asyncio
    async def test_retrieve_payment_method_not_found(self):
        """Test payment method retrieval with not found error."""
        # Mock OAuth token
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(
                200, json={"access_token": TEST_ACCESS_TOKEN, "expires_in": 3600}
            )
        )

        # Mock 404 error
        respx.get("https://api.justifi.ai/v1/payment_methods/pm_nonexistent").mock(
            return_value=Response(
                404,
                json={
                    "error": "not_found",
                    "message": "Payment method not found",
                },
            )
        )

        with pytest.raises(httpx.HTTPStatusError):
            await retrieve_payment_method(payment_method_token=TEST_NONEXISTENT_PM_ID)
