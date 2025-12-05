"""Tests for JustiFi checkout tools - focused on preventing customer-facing bugs."""

import pytest
import respx
from httpx import Response

from python.core import JustiFiClient
from python.tools.base import ToolError, ValidationError
from python.tools.checkouts import list_checkouts, retrieve_checkout


@pytest.fixture
def mock_client():
    """Create a mock JustiFi client for testing."""
    return JustiFiClient(
        client_id="test_client_id",
        client_secret="test_client_secret",
    )


@pytest.fixture
def mock_oauth_token():
    """Mock OAuth token response."""
    return {
        "access_token": "test_access_token_12345",
        "token_type": "Bearer",
        "expires_in": 3600,
    }


class TestListCheckouts:
    """Tests for list_checkouts function - only valuable scenarios."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_list_checkouts_success(self, mock_client, mock_oauth_token):
        """Test one successful checkout listing to prove happy path works."""

        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_oauth_token)
        )

        # Mock checkouts endpoint
        mock_response = {
            "type": "array",
            "data": [
                {
                    "id": "co_test123",
                    "status": "completed",
                    "amount": 5000,
                    "currency": "USD",
                }
            ],
        }
        respx.get("https://api.justifi.ai/v1/checkouts").mock(
            return_value=Response(200, json=mock_response)
        )

        result = await list_checkouts(mock_client)
        assert result["data"][0]["id"] == "co_test123"

    @pytest.mark.asyncio
    async def test_list_checkouts_invalid_limit(self, mock_client):
        """Test invalid limit - users will pass bad data."""
        with pytest.raises(ValidationError) as exc_info:
            await list_checkouts(mock_client, limit=0)
        assert "limit must be between 1 and 100" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_checkouts_invalid_payment_mode(self, mock_client):
        """Test invalid payment_mode - users will pass bad data."""
        with pytest.raises(ValidationError) as exc_info:
            await list_checkouts(mock_client, payment_mode="invalid")
        assert "payment_mode must be 'bnpl' or 'ecom'" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_checkouts_invalid_status(self, mock_client):
        """Test invalid status - users will pass bad data."""
        with pytest.raises(ValidationError) as exc_info:
            await list_checkouts(mock_client, status="invalid")
        assert "status must be one of: created, completed, attempted, expired" in str(
            exc_info.value
        )

    @pytest.mark.asyncio
    async def test_list_checkouts_both_cursors(self, mock_client):
        """Test both cursors provided - users will make this mistake."""
        with pytest.raises(ValidationError) as exc_info:
            await list_checkouts(mock_client, after_cursor="c1", before_cursor="c2")
        assert "Cannot specify both after_cursor and before_cursor" in str(
            exc_info.value
        )


class TestRetrieveCheckout:
    """Tests for retrieve_checkout function - only valuable scenarios."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_retrieve_checkout_success(self, mock_client, mock_oauth_token):
        """Test one successful checkout retrieval to prove happy path works."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_oauth_token)
        )

        mock_response = {
            "type": "checkout",
            "data": {
                "id": "co_test123",
                "status": "completed",
                "amount": 5000,
            },
        }
        respx.get("https://api.justifi.ai/v1/checkouts/co_test123").mock(
            return_value=Response(200, json=mock_response)
        )

        result = await retrieve_checkout(mock_client, "co_test123")
        assert result["data"]["id"] == "co_test123"

    @pytest.mark.asyncio
    async def test_retrieve_checkout_empty_id(self, mock_client):
        """Test empty checkout_id - users will pass bad data."""
        with pytest.raises(ValidationError) as exc_info:
            await retrieve_checkout(mock_client, "")
        assert "checkout_id cannot be empty" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_retrieve_checkout_whitespace_id(self, mock_client):
        """Test whitespace checkout_id - users will pass bad data."""
        with pytest.raises(ValidationError) as exc_info:
            await retrieve_checkout(mock_client, "   ")
        assert "checkout_id cannot be empty" in str(exc_info.value)

    @pytest.mark.asyncio
    @respx.mock
    async def test_retrieve_checkout_not_found(self, mock_client, mock_oauth_token):
        """Test 404 error - users will request non-existent checkouts."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_oauth_token)
        )
        respx.get("https://api.justifi.ai/v1/checkouts/co_nonexistent").mock(
            return_value=Response(404, json={"error": "Checkout not found"})
        )

        with pytest.raises(ToolError) as exc_info:
            await retrieve_checkout(mock_client, "co_nonexistent")
        assert "Checkout not found" in str(exc_info.value)
