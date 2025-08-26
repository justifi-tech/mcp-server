"""
Tests for JustiFi Checkout Creation Tools

Test suite for checkout creation operations with PCI compliance.
"""

import pytest
import respx
from httpx import Response

from python.core import JustiFiClient
from python.tools.base import ToolError, ValidationError
from python.tools.checkouts_create import (
    complete_checkout,
    create_checkout,
    expire_checkout,
    update_checkout,
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
def mock_checkout_response():
    """Mock checkout creation response."""
    return {
        "data": {
            "id": "checkout_test123",
            "amount": 1000,
            "currency": "usd",
            "description": "Test checkout",
            "status": "open",
            "url": "https://checkout.justifi.ai/checkout_test123",
            "payment_method_group_id": "pmg_test123",
        }
    }


@pytest.fixture
def mock_completed_checkout_response():
    """Mock completed checkout response."""
    return {
        "data": {
            "id": "checkout_test123",
            "amount": 1000,
            "currency": "usd",
            "status": "completed",
            "payment": {"id": "py_test123", "status": "succeeded"},
        }
    }


@pytest.fixture
def mock_expired_checkout_response():
    """Mock expired checkout response."""
    return {
        "data": {
            "id": "checkout_test123",
            "status": "expired",
        }
    }


class TestCreateCheckout:
    """Test create_checkout function."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_create_checkout_success(self, test_client, mock_token_response, mock_checkout_response):
        """Test successful checkout creation."""
        # Mock OAuth token request
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        
        # Mock checkout creation request
        respx.post("https://api.justifi.ai/v1/checkouts").mock(
            return_value=Response(200, json=mock_checkout_response)
        )
        
        result = await create_checkout(
            client=test_client,
            amount=1000,
            description="Test checkout",
            payment_method_group_id="pmg_test123",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
        )
        
        assert result["data"]["id"] == "checkout_test123"
        assert result["data"]["amount"] == 1000
        assert result["data"]["description"] == "Test checkout"
        assert result["data"]["status"] == "open"

    @pytest.mark.asyncio
    async def test_create_checkout_production_without_test_key(self, production_client):
        """Test checkout creation fails in production without test key."""
        with pytest.raises(PaymentSecurityError, match="Payment creation requires test API credentials"):
            await create_checkout(
                client=production_client,
                amount=1000,
                description="Test checkout",
                payment_method_group_id="pmg_test123",
            )

    @pytest.mark.asyncio
    async def test_create_checkout_invalid_amount(self, test_client):
        """Test checkout creation with invalid amount."""
        with pytest.raises(ValidationError, match="amount must be a positive integer"):
            await create_checkout(
                client=test_client,
                amount=-100,
                description="Test checkout",
                payment_method_group_id="pmg_test123",
            )
        
        with pytest.raises(ValidationError, match="amount must be a positive integer"):
            await create_checkout(
                client=test_client,
                amount=0,
                description="Test checkout",
                payment_method_group_id="pmg_test123",
            )

    @pytest.mark.asyncio
    async def test_create_checkout_invalid_description(self, test_client):
        """Test checkout creation with invalid description."""
        with pytest.raises(ValidationError, match="description is required"):
            await create_checkout(
                client=test_client,
                amount=1000,
                description="",
                payment_method_group_id="pmg_test123",
            )
        
        with pytest.raises(ValidationError, match="description is required"):
            await create_checkout(
                client=test_client,
                amount=1000,
                description=None,
                payment_method_group_id="pmg_test123",
            )

    @pytest.mark.asyncio
    async def test_create_checkout_invalid_payment_method_group_id(self, test_client):
        """Test checkout creation with invalid payment method group ID."""
        with pytest.raises(ValidationError, match="payment_method_group_id is required"):
            await create_checkout(
                client=test_client,
                amount=1000,
                description="Test checkout",
                payment_method_group_id="",
            )

    @pytest.mark.asyncio
    async def test_create_checkout_invalid_currency(self, test_client):
        """Test checkout creation with invalid currency."""
        with pytest.raises(ValidationError, match="currency must be a 3-character currency code"):
            await create_checkout(
                client=test_client,
                amount=1000,
                description="Test checkout",
                payment_method_group_id="pmg_test123",
                currency="us",  # Too short
            )

    @pytest.mark.asyncio
    async def test_create_checkout_invalid_urls(self, test_client):
        """Test checkout creation with invalid URL types."""
        with pytest.raises(ValidationError, match="success_url must be a string"):
            await create_checkout(
                client=test_client,
                amount=1000,
                description="Test checkout",
                payment_method_group_id="pmg_test123",
                success_url=123,
            )
        
        with pytest.raises(ValidationError, match="cancel_url must be a string"):
            await create_checkout(
                client=test_client,
                amount=1000,
                description="Test checkout",
                payment_method_group_id="pmg_test123",
                cancel_url=123,
            )


class TestUpdateCheckout:
    """Test update_checkout function."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_update_checkout_success(self, test_client, mock_token_response, mock_checkout_response):
        """Test successful checkout update."""
        # Mock OAuth token request
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        
        # Mock checkout update request
        respx.patch("https://api.justifi.ai/v1/checkouts/checkout_test123").mock(
            return_value=Response(200, json=mock_checkout_response)
        )
        
        result = await update_checkout(
            client=test_client,
            checkout_id="checkout_test123",
            description="Updated checkout",
            metadata={"key": "value"},
        )
        
        assert result["data"]["id"] == "checkout_test123"

    @pytest.mark.asyncio
    async def test_update_checkout_production_without_test_key(self, production_client):
        """Test checkout update fails in production without test key."""
        with pytest.raises(PaymentSecurityError, match="Payment creation requires test API credentials"):
            await update_checkout(
                client=production_client,
                checkout_id="checkout_test123",
                description="Updated checkout",
            )

    @pytest.mark.asyncio
    async def test_update_checkout_invalid_checkout_id(self, test_client):
        """Test checkout update with invalid checkout ID."""
        with pytest.raises(ValidationError, match="checkout_id is required"):
            await update_checkout(
                client=test_client,
                checkout_id="",
                description="Updated checkout",
            )

    @pytest.mark.asyncio
    async def test_update_checkout_no_fields(self, test_client):
        """Test checkout update with no fields to update."""
        with pytest.raises(ValidationError, match="At least one field must be provided"):
            await update_checkout(
                client=test_client,
                checkout_id="checkout_test123",
            )

    @pytest.mark.asyncio
    async def test_update_checkout_invalid_metadata(self, test_client):
        """Test checkout update with invalid metadata."""
        with pytest.raises(ValidationError, match="metadata must be a dictionary"):
            await update_checkout(
                client=test_client,
                checkout_id="checkout_test123",
                metadata="invalid",
            )


class TestCompleteCheckout:
    """Test complete_checkout function."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_complete_checkout_success(self, test_client, mock_token_response, mock_completed_checkout_response):
        """Test successful checkout completion."""
        # Mock OAuth token request
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        
        # Mock checkout complete request
        respx.post("https://api.justifi.ai/v1/checkouts/checkout_test123/complete").mock(
            return_value=Response(200, json=mock_completed_checkout_response)
        )
        
        result = await complete_checkout(
            client=test_client,
            checkout_id="checkout_test123",
            payment_method_id="pm_test123",
        )
        
        assert result["data"]["id"] == "checkout_test123"
        assert result["data"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_complete_checkout_production_without_test_key(self, production_client):
        """Test checkout completion fails in production without test key."""
        with pytest.raises(PaymentSecurityError, match="Payment creation requires test API credentials"):
            await complete_checkout(
                client=production_client,
                checkout_id="checkout_test123",
                payment_method_id="pm_test123",
            )

    @pytest.mark.asyncio
    async def test_complete_checkout_invalid_checkout_id(self, test_client):
        """Test checkout completion with invalid checkout ID."""
        with pytest.raises(ValidationError, match="checkout_id is required"):
            await complete_checkout(
                client=test_client,
                checkout_id="",
                payment_method_id="pm_test123",
            )

    @pytest.mark.asyncio
    async def test_complete_checkout_invalid_payment_method_id(self, test_client):
        """Test checkout completion with invalid payment method ID."""
        with pytest.raises(ValidationError, match="payment_method_id is required"):
            await complete_checkout(
                client=test_client,
                checkout_id="checkout_test123",
                payment_method_id="",
            )


class TestExpireCheckout:
    """Test expire_checkout function."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_expire_checkout_success(self, test_client, mock_token_response, mock_expired_checkout_response):
        """Test successful checkout expiration."""
        # Mock OAuth token request
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        
        # Mock checkout expire request
        respx.post("https://api.justifi.ai/v1/checkouts/checkout_test123/expire").mock(
            return_value=Response(200, json=mock_expired_checkout_response)
        )
        
        result = await expire_checkout(
            client=test_client,
            checkout_id="checkout_test123",
        )
        
        assert result["data"]["id"] == "checkout_test123"
        assert result["data"]["status"] == "expired"

    @pytest.mark.asyncio
    async def test_expire_checkout_production_without_test_key(self, production_client):
        """Test checkout expiration fails in production without test key."""
        with pytest.raises(PaymentSecurityError, match="Payment creation requires test API credentials"):
            await expire_checkout(
                client=production_client,
                checkout_id="checkout_test123",
            )

    @pytest.mark.asyncio
    async def test_expire_checkout_invalid_checkout_id(self, test_client):
        """Test checkout expiration with invalid checkout ID."""
        with pytest.raises(ValidationError, match="checkout_id is required"):
            await expire_checkout(
                client=test_client,
                checkout_id="",
            )