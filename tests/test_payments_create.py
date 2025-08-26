"""
Tests for JustiFi Payment Creation Tools
"""

import pytest
import respx
from httpx import Response

from python.core import JustiFiClient
from python.tools.base import ValidationError
from python.tools.payments_create import create_payment, tokenize_payment_method
from python.tools.utils.payment_security import PaymentSecurityError


@pytest.fixture
def test_client():
    """JustiFi test client for testing."""
    return JustiFiClient(
        client_id="test_client_id",
        client_secret="test_client_secret",
        base_url="https://api.justifi.ai",
    )


@pytest.fixture
def production_client():
    """JustiFi production client (non-test key) for testing."""
    return JustiFiClient(
        client_id="live_client_id",
        client_secret="live_client_secret",
        base_url="https://api.justifi.ai",
    )


@pytest.fixture
def mock_token_response():
    """Mock OAuth token response."""
    return {"access_token": "test_token", "expires_in": 3600}


class TestCreatePayment:
    """Test create_payment function."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_create_payment_success(self, test_client, mock_token_response):
        """Test successful payment creation with test client."""
        # Mock OAuth token request
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )

        # Mock the API response
        respx.post("https://api.justifi.ai/v1/payments").mock(
            return_value=Response(
                200,
                json={
                    "data": {
                        "id": "py_test123",
                        "amount": 1000,
                        "status": "succeeded",
                        "payment_method_id": "pm_test123",
                    }
                },
            )
        )

        result = await create_payment(
            client=test_client,
            amount=1000,
            payment_method_id="pm_test123",
            description="Test payment",
        )

        assert result["data"][0]["id"] == "py_test123"
        assert result["data"][0]["amount"] == 1000

    @pytest.mark.asyncio
    async def test_create_payment_security_failure(self, production_client):
        """Test payment creation fails with production client."""
        with pytest.raises(PaymentSecurityError):
            await create_payment(
                client=production_client, amount=1000, payment_method_id="pm_test123"
            )

    @pytest.mark.asyncio
    async def test_create_payment_validation_errors(self, test_client):
        """Test parameter validation errors."""
        # Invalid amount
        with pytest.raises(ValidationError, match="amount must be a positive integer"):
            await create_payment(test_client, -100, "pm_test123")

        # Missing payment method ID
        with pytest.raises(ValidationError, match="payment_method_id is required"):
            await create_payment(test_client, 1000, "")


class TestTokenizePaymentMethod:
    """Test tokenize_payment_method function."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_tokenize_success(self, test_client, mock_token_response):
        """Test successful tokenization with test client and test card."""
        # Mock OAuth token request
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )

        respx.post("https://api.justifi.ai/v1/payment_methods").mock(
            return_value=Response(
                200,
                json={
                    "data": {
                        "id": "pm_test123",
                        "card": {
                            "last4": "4242",
                            "brand": "visa",
                        },
                    }
                },
            )
        )

        result = await tokenize_payment_method(
            client=test_client,
            card_number="4242424242424242",  # Test card
            exp_month=12,
            exp_year=2025,
            cvc="123",
        )

        assert result["data"][0]["id"] == "pm_test123"
        assert result["data"][0]["card"]["last4"] == "4242"

    @pytest.mark.asyncio
    async def test_tokenize_invalid_test_card(self, test_client):
        """Test tokenization fails with invalid test card."""
        with pytest.raises(
            PaymentSecurityError, match="Only JustiFi test cards are allowed"
        ):
            await tokenize_payment_method(
                client=test_client,
                card_number="1234567890123456",  # Not a test card
                exp_month=12,
                exp_year=2025,
                cvc="123",
            )

    @pytest.mark.asyncio
    async def test_tokenize_validation_errors(self, test_client):
        """Test parameter validation errors."""
        # Invalid expiration month
        with pytest.raises(
            ValidationError, match="exp_month must be an integer between 1 and 12"
        ):
            await tokenize_payment_method(
                test_client,
                "4242424242424242",
                13,  # Invalid month
                2025,
                "123",
            )
