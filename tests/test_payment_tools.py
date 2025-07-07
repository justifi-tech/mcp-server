"""
Tests for JustiFi Payment Tools

Test suite for payment-related operations including retrieval and listing.
"""

import pytest
import respx
from httpx import Response

from justifi_mcp.core import JustiFiClient
from justifi_mcp.tools.base import ToolError, ValidationError
from justifi_mcp.tools.payment_methods import retrieve_payment_method
from justifi_mcp.tools.payments import list_payments, retrieve_payment


@pytest.fixture
def justifi_client():
    """JustiFi client for testing."""
    return JustiFiClient(
        client_id="test_client_id",
        client_secret="test_client_secret",
    )


@pytest.fixture
def mock_token_response():
    """Mock OAuth token response."""
    return {"access_token": "test_token", "expires_in": 3600}


class TestRetrievePayment:
    """Test retrieve_payment function."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_retrieve_payment_success(self, justifi_client, mock_token_response):
        """Test successful payment retrieval."""
        # Mock OAuth token request
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )

        # Mock payment retrieval
        mock_payment_data = {
            "data": {
                "id": "py_test123",
                "status": "succeeded",
                "amount": 10000,
            }
        }
        respx.get("https://api.justifi.ai/v1/payments/py_test123").mock(
            return_value=Response(200, json=mock_payment_data)
        )

        result = await retrieve_payment(justifi_client, "py_test123")
        assert result["data"]["id"] == "py_test123"

    @pytest.mark.asyncio
    async def test_retrieve_payment_invalid_id(self, justifi_client):
        """Test payment retrieval with invalid ID."""
        with pytest.raises(ValidationError, match="payment_id is required"):
            await retrieve_payment(justifi_client, "")

    @respx.mock
    @pytest.mark.asyncio
    async def test_retrieve_payment_not_found(
        self, justifi_client, mock_token_response
    ):
        """Test payment retrieval when payment doesn't exist."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        respx.get("https://api.justifi.ai/v1/payments/py_nonexistent").mock(
            return_value=Response(404, json={"error": "Payment not found"})
        )

        with pytest.raises(ToolError, match="Failed to retrieve payment"):
            await retrieve_payment(justifi_client, "py_nonexistent")


class TestListPayments:
    """Test list_payments function."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_payments_success(self, justifi_client, mock_token_response):
        """Test successful payments listing."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        mock_payments_list = {
            "data": [{"id": "py_test123", "status": "succeeded"}],
            "has_more": False,
        }
        respx.get("https://api.justifi.ai/v1/payments").mock(
            return_value=Response(200, json=mock_payments_list)
        )

        result = await list_payments(justifi_client)
        assert result["data"][0]["id"] == "py_test123"

    @pytest.mark.asyncio
    async def test_list_payments_invalid_limit(self, justifi_client):
        """Test payments listing with invalid limit."""
        with pytest.raises(ValidationError, match="limit must be an integer"):
            await list_payments(justifi_client, limit=0)

    @pytest.mark.asyncio
    async def test_list_payments_invalid_cursors(self, justifi_client):
        """Test payments listing with invalid cursor parameters."""
        with pytest.raises(ValidationError, match="Cannot specify both"):
            await list_payments(justifi_client, after_cursor="abc", before_cursor="def")


class TestRetrievePaymentMethod:
    """Test retrieve_payment_method function."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_retrieve_payment_method_success(
        self, justifi_client, mock_token_response
    ):
        """Test successful payment method retrieval."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        mock_payment_method_data = {
            "data": {
                "id": "pm_test123",
                "type": "card",
            }
        }
        respx.get("https://api.justifi.ai/v1/payment_methods/pm_test123").mock(
            return_value=Response(200, json=mock_payment_method_data)
        )

        result = await retrieve_payment_method(justifi_client, "pm_test123")
        assert result["data"]["id"] == "pm_test123"

    @pytest.mark.asyncio
    async def test_retrieve_payment_method_invalid_token(self, justifi_client):
        """Test payment method retrieval with invalid token."""
        with pytest.raises(ValidationError, match="payment_method_token is required"):
            await retrieve_payment_method(justifi_client, "")

    @respx.mock
    @pytest.mark.asyncio
    async def test_retrieve_payment_method_not_found(
        self, justifi_client, mock_token_response
    ):
        """Test payment method retrieval when payment method doesn't exist."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        respx.get("https://api.justifi.ai/v1/payment_methods/pm_nonexistent").mock(
            return_value=Response(404, json={"error": "Payment method not found"})
        )

        with pytest.raises(ToolError, match="Failed to retrieve payment method"):
            await retrieve_payment_method(justifi_client, "pm_nonexistent")
