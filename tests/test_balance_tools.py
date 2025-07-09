"""Test balance transaction tools functionality."""

import pytest
import respx
from httpx import Response

from python.core import JustiFiClient
from python.tools.balances import (
    list_balance_transactions,
    retrieve_balance_transaction,
)
from python.tools.base import ToolError, ValidationError

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_client():
    """Create a mock JustiFi client."""
    # Use explicit string values to avoid type issues
    return JustiFiClient("test_id", "test_secret")


@pytest.fixture
def mock_token_response():
    """Mock OAuth token response."""
    return {"access_token": "test_token_123"}


@pytest.fixture
def mock_balance_transaction_response():
    """Mock balance transaction response."""
    return {
        "type": "balance_transaction",
        "data": {
            "id": "bt_test123",
            "amount": 9850,
            "balance": 9850,
            "currency": "usd",
            "description": "Payment for order #123",
            "type": "payment",
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-01T12:00:00Z",
        },
    }


@pytest.fixture
def mock_balance_transactions_list_response():
    """Mock balance transactions list response."""
    return {
        "type": "array",
        "data": [
            {
                "id": "bt_test123",
                "amount": 9850,
                "balance": 9850,
                "currency": "usd",
                "description": "Payment for order #123",
                "type": "payment",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
            },
            {
                "id": "bt_test456",
                "amount": -150,
                "balance": 9700,
                "currency": "usd",
                "description": "Processing fee",
                "type": "fee",
                "created_at": "2024-01-01T12:01:00Z",
                "updated_at": "2024-01-01T12:01:00Z",
            },
        ],
        "page_info": {"has_next": False, "has_previous": False},
    }


class TestListBalanceTransactions:
    """Test list_balance_transactions function."""

    @respx.mock
    async def test_list_balance_transactions_success(
        self, mock_client, mock_token_response, mock_balance_transactions_list_response
    ):
        """Test successful balance transactions listing."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        respx.get("https://api.justifi.ai/v1/balance_transactions").mock(
            return_value=Response(200, json=mock_balance_transactions_list_response)
        )

        result = await list_balance_transactions(mock_client)

        assert result["type"] == "array"
        assert len(result["data"]) == 2
        assert result["data"][0]["id"] == "bt_test123"
        assert result["data"][1]["id"] == "bt_test456"

    @respx.mock
    async def test_list_balance_transactions_with_pagination(
        self, mock_client, mock_token_response, mock_balance_transactions_list_response
    ):
        """Test balance transactions listing with pagination."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        respx.get("https://api.justifi.ai/v1/balance_transactions").mock(
            return_value=Response(200, json=mock_balance_transactions_list_response)
        )

        result = await list_balance_transactions(
            mock_client, limit=10, after_cursor="cursor123"
        )

        assert result["type"] == "array"

    @respx.mock
    async def test_list_balance_transactions_with_payout_filter(
        self, mock_client, mock_token_response, mock_balance_transactions_list_response
    ):
        """Test balance transactions listing with payout filter."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        respx.get("https://api.justifi.ai/v1/balance_transactions").mock(
            return_value=Response(200, json=mock_balance_transactions_list_response)
        )

        result = await list_balance_transactions(mock_client, payout_id="po_test123")

        assert result["type"] == "array"

    async def test_list_balance_transactions_invalid_limit(self, mock_client):
        """Test list_balance_transactions with invalid limit."""
        with pytest.raises(ValidationError) as exc_info:
            await list_balance_transactions(mock_client, limit=0)

        assert "limit must be an integer between 1 and 100" in str(exc_info.value)

    async def test_list_balance_transactions_limit_too_high(self, mock_client):
        """Test list_balance_transactions with limit too high."""
        with pytest.raises(ValidationError) as exc_info:
            await list_balance_transactions(mock_client, limit=101)

        assert "limit must be an integer between 1 and 100" in str(exc_info.value)

    async def test_list_balance_transactions_both_cursors(self, mock_client):
        """Test list_balance_transactions with both cursors (should fail)."""
        with pytest.raises(ValidationError) as exc_info:
            await list_balance_transactions(
                mock_client, after_cursor="after", before_cursor="before"
            )

        assert "Cannot specify both after_cursor and before_cursor" in str(
            exc_info.value
        )


class TestRetrieveBalanceTransaction:
    """Test retrieve_balance_transaction function."""

    @respx.mock
    async def test_retrieve_balance_transaction_success(
        self, mock_client, mock_token_response, mock_balance_transaction_response
    ):
        """Test successful balance transaction retrieval."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        respx.get("https://api.justifi.ai/v1/balance_transactions/bt_test123").mock(
            return_value=Response(200, json=mock_balance_transaction_response)
        )

        result = await retrieve_balance_transaction(mock_client, "bt_test123")

        assert result["type"] == "balance_transaction"
        assert result["data"]["id"] == "bt_test123"
        assert result["data"]["amount"] == 9850

    async def test_retrieve_balance_transaction_empty_id(self, mock_client):
        """Test retrieve_balance_transaction with empty balance_transaction_id."""
        with pytest.raises(ValidationError) as exc_info:
            await retrieve_balance_transaction(mock_client, "")

        assert "balance_transaction_id must be a non-empty string" in str(
            exc_info.value
        )

    async def test_retrieve_balance_transaction_whitespace_id(self, mock_client):
        """Test retrieve_balance_transaction with whitespace balance_transaction_id."""
        with pytest.raises(ValidationError) as exc_info:
            await retrieve_balance_transaction(mock_client, "   ")

        assert (
            "balance_transaction_id cannot be empty or contain only whitespace"
            in str(exc_info.value)
        )

    async def test_retrieve_balance_transaction_none_id(self, mock_client):
        """Test retrieve_balance_transaction with None balance_transaction_id."""
        with pytest.raises(ValidationError) as exc_info:
            await retrieve_balance_transaction(mock_client, None)

        assert "balance_transaction_id must be a non-empty string" in str(
            exc_info.value
        )

    @respx.mock
    async def test_retrieve_balance_transaction_not_found(
        self, mock_client, mock_token_response
    ):
        """Test retrieve_balance_transaction with non-existent balance transaction."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        respx.get("https://api.justifi.ai/v1/balance_transactions/bt_nonexistent").mock(
            return_value=Response(404, json={"error": "Not found"})
        )

        with pytest.raises(ToolError):
            await retrieve_balance_transaction(mock_client, "bt_nonexistent")

    @respx.mock
    async def test_retrieve_balance_transaction_server_error(
        self, mock_client, mock_token_response
    ):
        """Test retrieve_balance_transaction with server error."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        respx.get("https://api.justifi.ai/v1/balance_transactions/bt_test123").mock(
            return_value=Response(500, json={"error": "Internal server error"})
        )

        with pytest.raises(ToolError):
            await retrieve_balance_transaction(mock_client, "bt_test123")
