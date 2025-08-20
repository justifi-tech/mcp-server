"""Tests for JustiFi dispute tools - focused on preventing customer-facing bugs."""

import pytest
import respx
from httpx import Response

from python.core import JustiFiClient
from python.tools.base import ToolError, ValidationError
from python.tools.disputes import list_disputes, retrieve_dispute


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


class TestListDisputes:
    """Tests for list_disputes function - only valuable scenarios."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_list_disputes_success(self, mock_client, mock_oauth_token):
        """Test one successful dispute listing to prove happy path works."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_oauth_token)
        )

        mock_response = {
            "type": "array",
            "data": [{"id": "dp_test123", "status": "under_review"}],
        }
        respx.get("https://api.justifi.ai/v1/disputes").mock(
            return_value=Response(200, json=mock_response)
        )

        result = await list_disputes(mock_client)
        assert result["data"][0]["id"] == "dp_test123"

    @pytest.mark.asyncio
    async def test_list_disputes_invalid_limit(self, mock_client):
        """Test invalid limit - users will pass bad data."""
        with pytest.raises(ValidationError) as exc_info:
            await list_disputes(mock_client, limit=0)
        assert "limit must be between 1 and 100" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_disputes_both_cursors(self, mock_client):
        """Test both cursors provided - users will make this mistake."""
        with pytest.raises(ValidationError) as exc_info:
            await list_disputes(mock_client, after_cursor="c1", before_cursor="c2")
        assert "Cannot specify both after_cursor and before_cursor" in str(
            exc_info.value
        )


class TestRetrieveDispute:
    """Tests for retrieve_dispute function - only valuable scenarios."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_retrieve_dispute_success(self, mock_client, mock_oauth_token):
        """Test one successful dispute retrieval to prove happy path works."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_oauth_token)
        )

        mock_response = {
            "type": "dispute",
            "data": {"id": "dp_test123", "status": "under_review"},
        }
        respx.get("https://api.justifi.ai/v1/disputes/dp_test123").mock(
            return_value=Response(200, json=mock_response)
        )

        result = await retrieve_dispute(mock_client, "dp_test123")
        assert result["data"]["id"] == "dp_test123"

    @pytest.mark.asyncio
    async def test_retrieve_dispute_empty_id(self, mock_client):
        """Test empty dispute_id - users will pass bad data."""
        with pytest.raises(ValidationError) as exc_info:
            await retrieve_dispute(mock_client, "")
        assert "dispute_id cannot be empty" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_retrieve_dispute_whitespace_id(self, mock_client):
        """Test whitespace dispute_id - users will pass bad data."""
        with pytest.raises(ValidationError) as exc_info:
            await retrieve_dispute(mock_client, "   ")
        assert "dispute_id cannot be empty" in str(exc_info.value)

    @pytest.mark.asyncio
    @respx.mock
    async def test_retrieve_dispute_not_found(self, mock_client, mock_oauth_token):
        """Test 404 error - users will request non-existent disputes."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_oauth_token)
        )
        respx.get("https://api.justifi.ai/v1/disputes/dp_nonexistent").mock(
            return_value=Response(404, json={"error": "Dispute not found"})
        )

        with pytest.raises(ToolError) as exc_info:
            await retrieve_dispute(mock_client, "dp_nonexistent")
        assert "Resource not found" in str(exc_info.value)
