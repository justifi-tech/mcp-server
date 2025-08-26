"""
Tests for JustiFi Payment Creation Tools

Test suite for secure payment creation operations with PCI compliance.
"""

import pytest
import respx
from httpx import Response

from python.core import JustiFiClient
from python.tools.base import ToolError, ValidationError
from python.tools.payments_create import (
    create_payment,
    create_payment_with_card,
    tokenize_payment_method,
)
from python.tools.utils.security import PaymentSecurityError, SecurityError


@pytest.fixture
def test_client():
    """JustiFi test client for testing."""
    return JustiFiClient(
        client_id="test_client_id",
        client_secret="test_client_secret",
        base_url="https://api.justifi.ai",
    )


@pytest.fixture
def custom_client():
    """JustiFi custom environment client for testing."""
    return JustiFiClient(
        client_id="custom_client_id",
        client_secret="custom_client_secret",
        base_url="https://custom-api.example.com",
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


@pytest.fixture
def mock_payment_response():
    """Mock payment creation response."""
    return {
        "data": {
            "id": "py_test123",
            "amount": 1000,
            "currency": "usd",
            "status": "succeeded",
            "payment_method": {"id": "pm_test123"},
        }
    }


@pytest.fixture
def mock_payment_method_response():
    """Mock payment method tokenization response."""
    return {
        "data": {
            "id": "pm_test123",
            "card": {
                "brand": "visa",
                "last4": "4242",
                "exp_month": 12,
                "exp_year": 2025,
            },
        }
    }


class TestCreatePayment:
    """Test create_payment function."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_create_payment_success(self, test_client, mock_token_response, mock_payment_response):
        """Test successful payment creation."""
        # Mock OAuth token request
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        
        # Mock payment creation request
        respx.post("https://api.justifi.ai/v1/payments").mock(
            return_value=Response(200, json=mock_payment_response)
        )
        
        result = await create_payment(
            client=test_client,
            amount=1000,
            payment_method_id="pm_test123",
            description="Test payment",
        )
        
        assert result["data"]["id"] == "py_test123"
        assert result["data"]["amount"] == 1000
        assert result["data"]["status"] == "succeeded"

    @pytest.mark.asyncio
    async def test_create_payment_production_without_test_key(self, production_client):
        """Test payment creation fails in production without test key."""
        with pytest.raises(PaymentSecurityError, match="Payment creation requires test API credentials"):
            await create_payment(
                client=production_client,
                amount=1000,
                payment_method_id="pm_test123",
            )

    @pytest.mark.asyncio
    @respx.mock
    async def test_create_payment_custom_environment(self, custom_client, mock_token_response, mock_payment_response):
        """Test payment creation in custom environment."""
        # Mock OAuth token request
        respx.post("https://custom-api.example.com/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        
        # Mock payment creation request
        respx.post("https://custom-api.example.com/v1/payments").mock(
            return_value=Response(200, json=mock_payment_response)
        )
        
        result = await create_payment(
            client=custom_client,
            amount=1000,
            payment_method_id="pm_test123",
        )
        
        assert result["data"]["id"] == "py_test123"

    @pytest.mark.asyncio
    async def test_create_payment_invalid_amount(self, test_client):
        """Test payment creation with invalid amount."""
        with pytest.raises(ValidationError, match="amount must be a positive integer"):
            await create_payment(
                client=test_client,
                amount=-100,
                payment_method_id="pm_test123",
            )
        
        with pytest.raises(ValidationError, match="amount must be a positive integer"):
            await create_payment(
                client=test_client,
                amount=0,
                payment_method_id="pm_test123",
            )

    @pytest.mark.asyncio
    async def test_create_payment_invalid_payment_method_id(self, test_client):
        """Test payment creation with invalid payment method ID."""
        with pytest.raises(ValidationError, match="payment_method_id is required"):
            await create_payment(
                client=test_client,
                amount=1000,
                payment_method_id="",
            )
        
        with pytest.raises(ValidationError, match="payment_method_id is required"):
            await create_payment(
                client=test_client,
                amount=1000,
                payment_method_id=None,
            )

    @pytest.mark.asyncio
    async def test_create_payment_invalid_currency(self, test_client):
        """Test payment creation with invalid currency."""
        with pytest.raises(ValidationError, match="currency must be a 3-character currency code"):
            await create_payment(
                client=test_client,
                amount=1000,
                payment_method_id="pm_test123",
                currency="us",  # Too short
            )

    @pytest.mark.asyncio
    async def test_create_payment_with_metadata(self, test_client):
        """Test payment creation with valid metadata."""
        # Test invalid metadata type
        with pytest.raises(ValidationError, match="metadata must be a dictionary"):
            await create_payment(
                client=test_client,
                amount=1000,
                payment_method_id="pm_test123",
                metadata="invalid",
            )


class TestTokenizePaymentMethod:
    """Test tokenize_payment_method function."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_tokenize_payment_method_success(self, test_client, mock_token_response, mock_payment_method_response):
        """Test successful payment method tokenization."""
        # Mock OAuth token request
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        
        # Mock payment method creation request
        respx.post("https://api.justifi.ai/v1/payment_methods").mock(
            return_value=Response(200, json=mock_payment_method_response)
        )
        
        result = await tokenize_payment_method(
            client=test_client,
            card_number="4242424242424242",
            exp_month=12,
            exp_year=2025,
            cvc="123",
        )
        
        assert result["data"]["id"] == "pm_test123"
        assert result["data"]["card"]["last4"] == "4242"

    @pytest.mark.asyncio
    async def test_tokenize_payment_method_production_without_test_key(self, production_client):
        """Test tokenization fails in production without test key."""
        with pytest.raises(PaymentSecurityError, match="Payment creation requires test API credentials"):
            await tokenize_payment_method(
                client=production_client,
                card_number="4242424242424242",
                exp_month=12,
                exp_year=2025,
                cvc="123",
            )

    @pytest.mark.asyncio
    async def test_tokenize_payment_method_invalid_test_card(self, test_client):
        """Test tokenization fails with invalid test card."""
        with pytest.raises(SecurityError, match="Only JustiFi test cards are allowed"):
            await tokenize_payment_method(
                client=test_client,
                card_number="1234567890123456",
                exp_month=12,
                exp_year=2025,
                cvc="123",
            )

    @pytest.mark.asyncio
    async def test_tokenize_payment_method_invalid_card_number(self, test_client):
        """Test tokenization with invalid card number."""
        with pytest.raises(ValidationError, match="card_number is required"):
            await tokenize_payment_method(
                client=test_client,
                card_number="",
                exp_month=12,
                exp_year=2025,
                cvc="123",
            )

    @pytest.mark.asyncio
    async def test_tokenize_payment_method_invalid_exp_month(self, test_client):
        """Test tokenization with invalid expiration month."""
        with pytest.raises(ValidationError, match="exp_month must be an integer between 1 and 12"):
            await tokenize_payment_method(
                client=test_client,
                card_number="4242424242424242",
                exp_month=13,
                exp_year=2025,
                cvc="123",
            )

    @pytest.mark.asyncio
    async def test_tokenize_payment_method_invalid_exp_year(self, test_client):
        """Test tokenization with invalid expiration year."""
        with pytest.raises(ValidationError, match="exp_year must be a 4-digit year"):
            await tokenize_payment_method(
                client=test_client,
                card_number="4242424242424242",
                exp_month=12,
                exp_year=25,  # 2-digit year
                cvc="123",
            )

    @pytest.mark.asyncio
    async def test_tokenize_payment_method_invalid_cvc(self, test_client):
        """Test tokenization with invalid CVC."""
        with pytest.raises(ValidationError, match="cvc must be 3 or 4 digits"):
            await tokenize_payment_method(
                client=test_client,
                card_number="4242424242424242",
                exp_month=12,
                exp_year=2025,
                cvc="12",  # Too short
            )
        
        with pytest.raises(ValidationError, match="cvc must be 3 or 4 digits"):
            await tokenize_payment_method(
                client=test_client,
                card_number="4242424242424242",
                exp_month=12,
                exp_year=2025,
                cvc="abc",  # Not digits
            )


class TestCreatePaymentWithCard:
    """Test create_payment_with_card function."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_create_payment_with_card_success(self, test_client, mock_token_response, mock_payment_method_response, mock_payment_response):
        """Test successful payment creation with card."""
        # Mock OAuth token request
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        
        # Mock payment method creation request
        respx.post("https://api.justifi.ai/v1/payment_methods").mock(
            return_value=Response(200, json=mock_payment_method_response)
        )
        
        # Mock payment creation request
        respx.post("https://api.justifi.ai/v1/payments").mock(
            return_value=Response(200, json=mock_payment_response)
        )
        
        result = await create_payment_with_card(
            client=test_client,
            amount=1000,
            card_number="4242424242424242",
            exp_month=12,
            exp_year=2025,
            cvc="123",
            description="Test payment with card",
        )
        
        assert result["data"]["id"] == "py_test123"
        assert result["data"]["amount"] == 1000

    @pytest.mark.asyncio
    async def test_create_payment_with_card_production_without_test_key(self, production_client):
        """Test payment with card fails in production without test key."""
        with pytest.raises(PaymentSecurityError, match="Payment creation requires test API credentials"):
            await create_payment_with_card(
                client=production_client,
                amount=1000,
                card_number="4242424242424242",
                exp_month=12,
                exp_year=2025,
                cvc="123",
            )

    @pytest.mark.asyncio
    async def test_create_payment_with_card_invalid_test_card(self, test_client):
        """Test payment with card fails with invalid test card."""
        with pytest.raises(SecurityError, match="Only JustiFi test cards are allowed"):
            await create_payment_with_card(
                client=test_client,
                amount=1000,
                card_number="1234567890123456",
                exp_month=12,
                exp_year=2025,
                cvc="123",
            )

    @pytest.mark.asyncio
    async def test_create_payment_with_card_invalid_amount(self, test_client):
        """Test payment with card fails with invalid amount."""
        with pytest.raises(ValidationError, match="amount must be a positive integer"):
            await create_payment_with_card(
                client=test_client,
                amount=-100,
                card_number="4242424242424242",
                exp_month=12,
                exp_year=2025,
                cvc="123",
            )