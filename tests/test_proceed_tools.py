"""
Tests for JustiFi Proceed Tools

Test suite for proceed-related operations including retrieval and listing.
"""

import pytest
import respx
from httpx import Response

from python.core import JustiFiClient
from python.tools.base import ToolError, ValidationError
from python.tools.proceeds import list_proceeds, retrieve_proceed


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


@pytest.fixture
def mock_proceed_data():
    """Mock proceed data for testing."""
    return {
        "data": {
            "id": "pr_test123",
            "status": "pending",
            "amount": 10000,
            "currency": "usd",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
        }
    }


@pytest.fixture
def mock_proceeds_list():
    """Mock proceeds list response."""
    return {
        "data": [
            {
                "id": "pr_test123",
                "status": "pending",
                "amount": 10000,
                "currency": "usd",
            },
            {
                "id": "pr_test456",
                "status": "completed",
                "amount": 5000,
                "currency": "usd",
            },
        ],
        "has_more": False,
        "page_info": {
            "start_cursor": "pr_test123",
            "end_cursor": "pr_test456",
        },
    }


class TestRetrieveProceed:
    """Test retrieve_proceed function."""

    @pytest.mark.asyncio
    async def test_retrieve_proceed_invalid_id_empty(self, justifi_client):
        """Test proceed retrieval with empty ID."""
        with pytest.raises(ValidationError, match="proceed_id cannot be empty"):
            await retrieve_proceed(justifi_client, "")

    @pytest.mark.asyncio
    async def test_retrieve_proceed_invalid_id_whitespace(self, justifi_client):
        """Test proceed retrieval with whitespace-only ID."""
        with pytest.raises(ValidationError, match="proceed_id cannot be empty"):
            await retrieve_proceed(justifi_client, "   ")

    @pytest.mark.asyncio
    async def test_retrieve_proceed_invalid_id_none(self, justifi_client):
        """Test proceed retrieval with None ID."""
        with pytest.raises(ValidationError, match="proceed_id cannot be empty"):
            await retrieve_proceed(justifi_client, None)

    @respx.mock
    @pytest.mark.asyncio
    async def test_retrieve_proceed_success(
        self, justifi_client, mock_token_response, mock_proceed_data
    ):
        """Test successful proceed retrieval."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        respx.get("https://api.justifi.ai/v1/proceeds/pr_test123").mock(
            return_value=Response(200, json=mock_proceed_data)
        )

        result = await retrieve_proceed(justifi_client, "pr_test123")
        assert result["data"][0]["id"] == "pr_test123"
        assert result["data"][0]["status"] == "pending"
        assert result["data"][0]["amount"] == 10000

    @respx.mock
    @pytest.mark.asyncio
    async def test_retrieve_proceed_not_found(
        self, justifi_client, mock_token_response
    ):
        """Test proceed retrieval when proceed doesn't exist."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        respx.get("https://api.justifi.ai/v1/proceeds/pr_nonexistent").mock(
            return_value=Response(404, json={"error": "Proceed not found"})
        )

        with pytest.raises(ToolError):
            await retrieve_proceed(justifi_client, "pr_nonexistent")


class TestListProceeds:
    """Test list_proceeds function."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_proceeds_success_default(
        self, justifi_client, mock_token_response, mock_proceeds_list
    ):
        """Test successful proceeds listing with default parameters."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        respx.get("https://api.justifi.ai/v1/proceeds").mock(
            return_value=Response(200, json=mock_proceeds_list)
        )

        result = await list_proceeds(justifi_client)
        assert len(result["data"]) == 2
        assert result["data"][0]["id"] == "pr_test123"
        assert result["data"][1]["id"] == "pr_test456"

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_proceeds_success_with_limit(
        self, justifi_client, mock_token_response, mock_proceeds_list
    ):
        """Test successful proceeds listing with custom limit."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        respx.get("https://api.justifi.ai/v1/proceeds").mock(
            return_value=Response(200, json=mock_proceeds_list)
        )

        result = await list_proceeds(justifi_client, limit=50)
        assert len(result["data"]) == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_proceeds_success_with_after_cursor(
        self, justifi_client, mock_token_response, mock_proceeds_list
    ):
        """Test successful proceeds listing with after_cursor pagination."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        respx.get("https://api.justifi.ai/v1/proceeds").mock(
            return_value=Response(200, json=mock_proceeds_list)
        )

        result = await list_proceeds(justifi_client, after_cursor="cursor_abc123")
        assert len(result["data"]) == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_proceeds_success_with_before_cursor(
        self, justifi_client, mock_token_response, mock_proceeds_list
    ):
        """Test successful proceeds listing with before_cursor pagination."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        respx.get("https://api.justifi.ai/v1/proceeds").mock(
            return_value=Response(200, json=mock_proceeds_list)
        )

        result = await list_proceeds(justifi_client, before_cursor="cursor_def456")
        assert len(result["data"]) == 2

    @pytest.mark.asyncio
    async def test_list_proceeds_invalid_limit_zero(self, justifi_client):
        """Test proceeds listing with limit of 0."""
        with pytest.raises(ValidationError, match="limit must be between 1 and 100"):
            await list_proceeds(justifi_client, limit=0)

    @pytest.mark.asyncio
    async def test_list_proceeds_invalid_limit_negative(self, justifi_client):
        """Test proceeds listing with negative limit."""
        with pytest.raises(ValidationError, match="limit must be between 1 and 100"):
            await list_proceeds(justifi_client, limit=-1)

    @pytest.mark.asyncio
    async def test_list_proceeds_invalid_limit_too_large(self, justifi_client):
        """Test proceeds listing with limit exceeding maximum."""
        with pytest.raises(ValidationError, match="limit must be between 1 and 100"):
            await list_proceeds(justifi_client, limit=101)

    @pytest.mark.asyncio
    async def test_list_proceeds_invalid_both_cursors(self, justifi_client):
        """Test proceeds listing with both cursors provided."""
        with pytest.raises(
            ValidationError, match="Cannot specify both after_cursor and before_cursor"
        ):
            await list_proceeds(
                justifi_client,
                after_cursor="cursor_abc",
                before_cursor="cursor_def",
            )

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_proceeds_empty_response(
        self, justifi_client, mock_token_response
    ):
        """Test proceeds listing with empty response."""
        empty_response = {"data": [], "has_more": False}
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        respx.get("https://api.justifi.ai/v1/proceeds").mock(
            return_value=Response(200, json=empty_response)
        )

        result = await list_proceeds(justifi_client)
        assert len(result["data"]) == 0
        assert result["metadata"]["count"] == 0
