"""
Tests for JustiFi Payment Intent Tools

Test suite for payment intent operations with PCI compliance.
"""

import pytest
import respx
from httpx import Response

from python.core import JustiFiClient
from python.tools.base import ToolError, ValidationError
from python.tools.payment_intents import (
    cancel_payment_intent,
    capture_payment_intent,
    confirm_payment_intent,
    create_payment_intent,
)
from python.tools.utils.security import PaymentSecurityError


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


@pytest.fixture
def mock_payment_intent_response():
    """Mock payment intent creation response."""
    return {
        "data": {
            "id": "pi_test123",
            "amount": 1000,
            "currency": "usd",
            "status": "requires_confirmation",
            "capture_method": "manual",
            "payment_method": {"id": "pm_test123"},
        }
    }


@pytest.fixture
def mock_captured_intent_response():
    """Mock captured payment intent response."""
    return {
        "data": {
            "id": "pi_test123",
            "amount": 1000,
            "currency": "usd",
            "status": "succeeded",
            "capture_method": "manual",
            "payment_method": {"id": "pm_test123"},
        }
    }


@pytest.fixture
def mock_cancelled_intent_response():
    """Mock cancelled payment intent response."""
    return {
        "data": {
            "id": "pi_test123",
            "amount": 1000,
            "currency": "usd",
            "status": "canceled",
            "cancellation_reason": "requested_by_customer",
        }
    }


class TestCreatePaymentIntent:
    """Test create_payment_intent function."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_create_payment_intent_success(self, test_client, mock_token_response, mock_payment_intent_response):
        """Test successful payment intent creation."""
        # Mock OAuth token request
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        
        # Mock payment intent creation request
        respx.post("https://api.justifi.ai/v1/payment_intents").mock(
            return_value=Response(200, json=mock_payment_intent_response)
        )
        
        result = await create_payment_intent(
            client=test_client,
            amount=1000,
            payment_method_id="pm_test123",
            description="Test payment intent",
            capture_method="manual",
        )
        
        assert result["data"]["id"] == "pi_test123"
        assert result["data"]["amount"] == 1000
        assert result["data"]["status"] == "requires_confirmation"

    @pytest.mark.asyncio
    async def test_create_payment_intent_production_without_test_key(self, production_client):
        """Test payment intent creation fails in production without test key."""
        with pytest.raises(PaymentSecurityError, match="Payment creation requires test API credentials"):
            await create_payment_intent(
                client=production_client,
                amount=1000,
                payment_method_id="pm_test123",
            )

    @pytest.mark.asyncio
    async def test_create_payment_intent_invalid_amount(self, test_client):
        """Test payment intent creation with invalid amount."""
        with pytest.raises(ValidationError, match="amount must be a positive integer"):
            await create_payment_intent(
                client=test_client,
                amount=-100,
                payment_method_id="pm_test123",
            )
        
        with pytest.raises(ValidationError, match="amount must be a positive integer"):
            await create_payment_intent(
                client=test_client,
                amount=0,
                payment_method_id="pm_test123",
            )

    @pytest.mark.asyncio
    async def test_create_payment_intent_invalid_payment_method_id(self, test_client):
        """Test payment intent creation with invalid payment method ID."""
        with pytest.raises(ValidationError, match="payment_method_id is required"):
            await create_payment_intent(
                client=test_client,
                amount=1000,
                payment_method_id="",
            )

    @pytest.mark.asyncio
    async def test_create_payment_intent_invalid_capture_method(self, test_client):
        """Test payment intent creation with invalid capture method."""
        with pytest.raises(ValidationError, match="capture_method must be 'automatic' or 'manual'"):
            await create_payment_intent(
                client=test_client,
                amount=1000,
                payment_method_id="pm_test123",
                capture_method="invalid",
            )

    @pytest.mark.asyncio
    async def test_create_payment_intent_invalid_confirmation_method(self, test_client):
        """Test payment intent creation with invalid confirmation method."""
        with pytest.raises(ValidationError, match="confirmation_method must be 'automatic' or 'manual'"):
            await create_payment_intent(
                client=test_client,
                amount=1000,
                payment_method_id="pm_test123",
                confirmation_method="invalid",
            )


class TestCapturePaymentIntent:
    """Test capture_payment_intent function."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_capture_payment_intent_success(self, test_client, mock_token_response, mock_captured_intent_response):
        """Test successful payment intent capture."""
        # Mock OAuth token request
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        
        # Mock payment intent capture request
        respx.post("https://api.justifi.ai/v1/payment_intents/pi_test123/capture").mock(
            return_value=Response(200, json=mock_captured_intent_response)
        )
        
        result = await capture_payment_intent(
            client=test_client,
            intent_id="pi_test123",
            amount=1000,
        )
        
        assert result["data"]["id"] == "pi_test123"
        assert result["data"]["status"] == "succeeded"

    @pytest.mark.asyncio
    async def test_capture_payment_intent_production_without_test_key(self, production_client):
        """Test payment intent capture fails in production without test key."""
        with pytest.raises(PaymentSecurityError, match="Payment creation requires test API credentials"):
            await capture_payment_intent(
                client=production_client,
                intent_id="pi_test123",
            )

    @pytest.mark.asyncio
    async def test_capture_payment_intent_invalid_intent_id(self, test_client):
        """Test payment intent capture with invalid intent ID."""
        with pytest.raises(ValidationError, match="intent_id is required"):
            await capture_payment_intent(
                client=test_client,
                intent_id="",
            )

    @pytest.mark.asyncio
    async def test_capture_payment_intent_invalid_amount(self, test_client):
        """Test payment intent capture with invalid amount."""
        with pytest.raises(ValidationError, match="amount must be a positive integer"):
            await capture_payment_intent(
                client=test_client,
                intent_id="pi_test123",
                amount=-100,
            )


class TestCancelPaymentIntent:
    """Test cancel_payment_intent function."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_cancel_payment_intent_success(self, test_client, mock_token_response, mock_cancelled_intent_response):
        """Test successful payment intent cancellation."""
        # Mock OAuth token request
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        
        # Mock payment intent cancel request
        respx.post("https://api.justifi.ai/v1/payment_intents/pi_test123/cancel").mock(
            return_value=Response(200, json=mock_cancelled_intent_response)
        )
        
        result = await cancel_payment_intent(
            client=test_client,
            intent_id="pi_test123",
            cancellation_reason="requested_by_customer",
        )
        
        assert result["data"]["id"] == "pi_test123"
        assert result["data"]["status"] == "canceled"

    @pytest.mark.asyncio
    async def test_cancel_payment_intent_production_without_test_key(self, production_client):
        """Test payment intent cancellation fails in production without test key."""
        with pytest.raises(PaymentSecurityError, match="Payment creation requires test API credentials"):
            await cancel_payment_intent(
                client=production_client,
                intent_id="pi_test123",
            )

    @pytest.mark.asyncio
    async def test_cancel_payment_intent_invalid_intent_id(self, test_client):
        """Test payment intent cancellation with invalid intent ID."""
        with pytest.raises(ValidationError, match="intent_id is required"):
            await cancel_payment_intent(
                client=test_client,
                intent_id="",
            )

    @pytest.mark.asyncio
    async def test_cancel_payment_intent_invalid_reason(self, test_client):
        """Test payment intent cancellation with invalid reason."""
        with pytest.raises(ValidationError, match="cancellation_reason must be a string"):
            await cancel_payment_intent(
                client=test_client,
                intent_id="pi_test123",
                cancellation_reason=123,
            )


class TestConfirmPaymentIntent:
    """Test confirm_payment_intent function."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_confirm_payment_intent_success(self, test_client, mock_token_response, mock_payment_intent_response):
        """Test successful payment intent confirmation."""
        # Mock OAuth token request
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        
        # Mock payment intent confirm request
        respx.post("https://api.justifi.ai/v1/payment_intents/pi_test123/confirm").mock(
            return_value=Response(200, json=mock_payment_intent_response)
        )
        
        result = await confirm_payment_intent(
            client=test_client,
            intent_id="pi_test123",
            payment_method_id="pm_test123",
        )
        
        assert result["data"]["id"] == "pi_test123"

    @pytest.mark.asyncio
    async def test_confirm_payment_intent_production_without_test_key(self, production_client):
        """Test payment intent confirmation fails in production without test key."""
        with pytest.raises(PaymentSecurityError, match="Payment creation requires test API credentials"):
            await confirm_payment_intent(
                client=production_client,
                intent_id="pi_test123",
            )

    @pytest.mark.asyncio
    async def test_confirm_payment_intent_invalid_intent_id(self, test_client):
        """Test payment intent confirmation with invalid intent ID."""
        with pytest.raises(ValidationError, match="intent_id is required"):
            await confirm_payment_intent(
                client=test_client,
                intent_id="",
            )

    @pytest.mark.asyncio
    async def test_confirm_payment_intent_invalid_payment_method_id(self, test_client):
        """Test payment intent confirmation with invalid payment method ID."""
        with pytest.raises(ValidationError, match="payment_method_id must be a string"):
            await confirm_payment_intent(
                client=test_client,
                intent_id="pi_test123",
                payment_method_id=123,
            )