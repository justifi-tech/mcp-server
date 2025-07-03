"""Test payout tools specifically."""

import pytest
import respx
from httpx import Response

from justifi_mcp.core import JustiFiClient
from justifi_mcp.tools.base import ToolError, ValidationError
from justifi_mcp.tools.payouts import (
    get_payout_status,
    get_recent_payouts,
    list_payouts,
    retrieve_payout,
)

# Mark all tests as async
pytestmark = pytest.mark.asyncio


@pytest.fixture
def justifi_client():
    """Create a test JustiFi client."""
    return JustiFiClient(
        client_id="test_client", client_secret="test_secret"  # noqa: S106
    )


@pytest.fixture
def mock_token_response():
    """Mock OAuth token response."""
    return {"access_token": "test_token", "expires_in": 3600}


@pytest.fixture
def mock_payout_data():
    """Mock payout data."""
    return {
        "data": {
            "id": "po_test123",
            "status": "completed",
            "amount": 10000,
            "currency": "USD",
            "created_at": "2025-01-25T12:00:00Z",
        }
    }


@pytest.fixture
def mock_payouts_list():
    """Mock payouts list response."""
    return {
        "data": [
            {
                "id": "po_test123",
                "status": "completed",
                "amount": 10000,
                "currency": "USD",
                "created_at": "2025-01-25T12:00:00Z",
            },
            {
                "id": "po_test456",
                "status": "pending",
                "amount": 5000,
                "currency": "USD",
                "created_at": "2025-01-25T11:00:00Z",
            },
        ],
        "has_more": False,
        "before_cursor": None,
        "after_cursor": None,
    }


class TestRetrievePayout:
    """Test retrieve_payout function."""

    @respx.mock
    async def test_retrieve_payout_success(
        self, justifi_client, mock_token_response, mock_payout_data
    ):
        """Test successful payout retrieval."""
        # Mock OAuth token request
        respx.post("https://api.justifi.ai/v1/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )

        # Mock payout retrieval
        respx.get("https://api.justifi.ai/v1/payouts/po_test123").mock(
            return_value=Response(200, json=mock_payout_data)
        )

        result = await retrieve_payout(justifi_client, "po_test123")
        assert result == mock_payout_data
        assert result["data"]["id"] == "po_test123"
        assert result["data"]["status"] == "completed"

    @respx.mock
    async def test_retrieve_payout_with_explicit_client(
        self, mock_token_response, mock_payout_data
    ):
        """Test payout retrieval with explicitly created client."""
        # Mock OAuth token request
        respx.post("https://api.justifi.ai/v1/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )

        # Mock payout retrieval
        respx.get("https://api.justifi.ai/v1/payouts/po_test123").mock(
            return_value=Response(200, json=mock_payout_data)
        )

        # Test with explicit credentials
        client = JustiFiClient(
            client_id="test_client", client_secret="test_secret"
        )  # noqa: S106
        result = await retrieve_payout(client, "po_test123")
        assert result == mock_payout_data

    async def test_retrieve_payout_empty_id(self, justifi_client):
        """Test error handling for empty payout ID."""
        with pytest.raises(ValidationError, match="payout_id cannot be empty"):
            await retrieve_payout(justifi_client, "")

        with pytest.raises(ValidationError, match="payout_id cannot be empty"):
            await retrieve_payout(justifi_client, "   ")

    @respx.mock
    async def test_retrieve_payout_not_found(self, justifi_client, mock_token_response):
        """Test handling of 404 error."""
        # Mock OAuth token request
        respx.post("https://api.justifi.ai/v1/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )

        # Mock 404 response
        respx.get("https://api.justifi.ai/v1/payouts/po_notfound").mock(
            return_value=Response(404, json={"error": "Payout not found"})
        )

        with pytest.raises(ToolError):  # Now wrapped in ToolError
            await retrieve_payout(justifi_client, "po_notfound")


class TestListPayouts:
    """Test list_payouts function."""

    @respx.mock
    async def test_list_payouts_success(
        self, justifi_client, mock_token_response, mock_payouts_list
    ):
        """Test successful payouts listing."""
        # Mock OAuth token request
        respx.post("https://api.justifi.ai/v1/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )

        # Mock payouts list
        respx.get("https://api.justifi.ai/v1/payouts").mock(
            return_value=Response(200, json=mock_payouts_list)
        )

        result = await list_payouts(justifi_client, limit=25)
        assert result == mock_payouts_list
        assert len(result["data"]) == 2

    @respx.mock
    async def test_list_payouts_with_pagination(
        self, justifi_client, mock_token_response, mock_payouts_list
    ):
        """Test payouts listing with pagination."""
        # Mock OAuth token request
        respx.post("https://api.justifi.ai/v1/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )

        # Mock payouts list with cursor
        respx.get("https://api.justifi.ai/v1/payouts").mock(
            return_value=Response(200, json=mock_payouts_list)
        )

        result = await list_payouts(justifi_client, limit=10, after_cursor="cursor_123")
        assert result == mock_payouts_list

    async def test_list_payouts_invalid_limit(self, justifi_client):
        """Test error handling for invalid limit."""
        with pytest.raises(ValidationError, match="limit must be between 1 and 100"):
            await list_payouts(justifi_client, limit=0)

        with pytest.raises(ValidationError, match="limit must be between 1 and 100"):
            await list_payouts(justifi_client, limit=101)

    async def test_list_payouts_both_cursors(self, justifi_client):
        """Test error handling when both cursors are provided."""
        with pytest.raises(
            ValidationError, match="Cannot specify both after_cursor and before_cursor"
        ):
            await list_payouts(
                justifi_client, after_cursor="cursor1", before_cursor="cursor2"
            )


class TestGetPayoutStatus:
    """Test get_payout_status function."""

    @respx.mock
    async def test_get_payout_status_success(
        self, justifi_client, mock_token_response, mock_payout_data
    ):
        """Test successful payout status retrieval."""
        # Mock OAuth token request
        respx.post("https://api.justifi.ai/v1/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )

        # Mock payout retrieval
        respx.get("https://api.justifi.ai/v1/payouts/po_test123").mock(
            return_value=Response(200, json=mock_payout_data)
        )

        result = await get_payout_status(justifi_client, "po_test123")
        assert result == "completed"

    @respx.mock
    async def test_get_payout_status_missing_field(
        self, justifi_client, mock_token_response
    ):
        """Test error handling when status field is missing."""
        # Mock OAuth token request
        respx.post("https://api.justifi.ai/v1/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )

        # Mock payout retrieval with missing status
        respx.get("https://api.justifi.ai/v1/payouts/po_test123").mock(
            return_value=Response(200, json={"data": {"id": "po_test123"}})
        )

        with pytest.raises(ToolError, match="Payout response missing expected field"):
            await get_payout_status(justifi_client, "po_test123")


class TestGetRecentPayouts:
    """Test get_recent_payouts function."""

    @respx.mock
    async def test_get_recent_payouts_success(
        self, justifi_client, mock_token_response, mock_payouts_list
    ):
        """Test successful recent payouts retrieval."""
        # Mock OAuth token request
        respx.post("https://api.justifi.ai/v1/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )

        # Mock payouts list
        respx.get("https://api.justifi.ai/v1/payouts").mock(
            return_value=Response(200, json=mock_payouts_list)
        )

        result = await get_recent_payouts(justifi_client, limit=10)
        assert result == mock_payouts_list["data"]
        assert len(result) == 2

    async def test_get_recent_payouts_invalid_limit(self, justifi_client):
        """Test error handling for invalid limit."""
        with pytest.raises(ValidationError, match="limit must be between 1 and 25"):
            await get_recent_payouts(justifi_client, limit=0)

        with pytest.raises(ValidationError, match="limit must be between 1 and 25"):
            await get_recent_payouts(justifi_client, limit=26)
