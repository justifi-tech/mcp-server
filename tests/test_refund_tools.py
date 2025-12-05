"""Test refund tools functionality."""

import pytest
import respx
from httpx import Response

from python.core import JustiFiClient
from python.tools.base import ToolError, ValidationError
from python.tools.refunds import (
    list_payment_refunds,
    list_refunds,
    retrieve_refund,
)

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
def mock_refund_response():
    """Mock refund response."""
    return {
        "type": "refund",
        "data": {
            "id": "re_test123",
            "payment_id": "py_test123",
            "amount": 1000,
            "description": "Test refund",
            "reason": "customer_request",
            "status": "succeeded",
            "metadata": {},
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-01T12:00:00Z",
        },
    }


@pytest.fixture
def mock_refunds_list_response():
    """Mock refunds list response."""
    return {
        "type": "array",
        "data": [
            {
                "id": "re_test123",
                "payment_id": "py_test123",
                "amount": 1000,
                "description": "Test refund",
                "reason": "customer_request",
                "status": "succeeded",
                "metadata": {},
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
            }
        ],
        "page_info": {"has_next": False, "has_previous": False},
    }


@pytest.fixture
def mock_payment_response():
    """Mock payment response with refunds."""
    return {
        "type": "payment",
        "data": {
            "id": "py_test123",
            "amount": 10000,
            "refunds": [
                {
                    "id": "re_test123",
                    "payment_id": "py_test123",
                    "amount": 1000,
                    "description": "Test refund",
                    "reason": "customer_request",
                    "status": "succeeded",
                    "metadata": {},
                    "created_at": "2024-01-01T12:00:00Z",
                    "updated_at": "2024-01-01T12:00:00Z",
                }
            ],
        },
    }


class TestListRefunds:
    """Test list_refunds function."""

    @respx.mock
    async def test_list_refunds_success(
        self, mock_client, mock_token_response, mock_refunds_list_response
    ):
        """Test successful refunds listing."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        respx.get("https://api.justifi.ai/v1/refunds").mock(
            return_value=Response(200, json=mock_refunds_list_response)
        )

        result = await list_refunds(mock_client)

        assert result["type"] == "array"
        assert len(result["data"]) == 1
        assert result["data"][0]["id"] == "re_test123"

    @respx.mock
    async def test_list_refunds_with_pagination(
        self, mock_client, mock_token_response, mock_refunds_list_response
    ):
        """Test refunds listing with pagination."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        respx.get("https://api.justifi.ai/v1/refunds").mock(
            return_value=Response(200, json=mock_refunds_list_response)
        )

        result = await list_refunds(mock_client, limit=10, after_cursor="cursor123")

        assert result["type"] == "array"

    async def test_list_refunds_invalid_limit(self, mock_client):
        """Test list_refunds with invalid limit."""
        with pytest.raises(ValidationError) as exc_info:
            await list_refunds(mock_client, limit=0)

        assert "limit must be an integer between 1 and 100" in str(exc_info.value)

    async def test_list_refunds_both_cursors(self, mock_client):
        """Test list_refunds with both cursors (should fail)."""
        with pytest.raises(ValidationError) as exc_info:
            await list_refunds(
                mock_client, after_cursor="after", before_cursor="before"
            )

        assert "Cannot specify both after_cursor and before_cursor" in str(
            exc_info.value
        )


class TestRetrieveRefund:
    """Test retrieve_refund function."""

    @respx.mock
    async def test_retrieve_refund_success(
        self, mock_client, mock_token_response, mock_refund_response
    ):
        """Test successful refund retrieval."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        respx.get("https://api.justifi.ai/v1/refunds/re_test123").mock(
            return_value=Response(200, json=mock_refund_response)
        )

        result = await retrieve_refund(mock_client, "re_test123")

        assert result["type"] == "refund"
        assert result["data"]["id"] == "re_test123"

    async def test_retrieve_refund_empty_id(self, mock_client):
        """Test retrieve_refund with empty refund_id."""
        with pytest.raises(ValidationError) as exc_info:
            await retrieve_refund(mock_client, "")

        assert "refund_id must be a non-empty string" in str(exc_info.value)

    async def test_retrieve_refund_whitespace_id(self, mock_client):
        """Test retrieve_refund with whitespace refund_id."""
        with pytest.raises(ValidationError) as exc_info:
            await retrieve_refund(mock_client, "   ")

        assert "refund_id cannot be empty or contain only whitespace" in str(
            exc_info.value
        )

    @respx.mock
    async def test_retrieve_refund_not_found(self, mock_client, mock_token_response):
        """Test retrieve_refund with non-existent refund."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        respx.get("https://api.justifi.ai/v1/refunds/re_nonexistent").mock(
            return_value=Response(404, json={"error": "Not found"})
        )

        with pytest.raises(ToolError) as exc_info:
            await retrieve_refund(mock_client, "re_nonexistent")

        assert "Not found" in str(exc_info.value)


class TestListPaymentRefunds:
    """Test list_payment_refunds function."""

    @respx.mock
    async def test_list_payment_refunds_success(
        self, mock_client, mock_token_response, mock_payment_response
    ):
        """Test successful payment refunds listing."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        respx.get("https://api.justifi.ai/v1/payments/py_test123").mock(
            return_value=Response(200, json=mock_payment_response)
        )

        result = await list_payment_refunds(mock_client, "py_test123")

        assert result["type"] == "array"
        assert len(result["data"]) == 1
        assert result["data"][0]["id"] == "re_test123"
        assert result["page_info"] is None

    async def test_list_payment_refunds_empty_id(self, mock_client):
        """Test list_payment_refunds with empty payment_id."""
        with pytest.raises(ValidationError) as exc_info:
            await list_payment_refunds(mock_client, "")

        assert "payment_id must be a non-empty string" in str(exc_info.value)

    @respx.mock
    async def test_list_payment_refunds_no_refunds(
        self, mock_client, mock_token_response
    ):
        """Test list_payment_refunds for payment with no refunds."""
        payment_response = {
            "type": "payment",
            "data": {"id": "py_test123", "amount": 10000, "refunds": []},
        }

        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        respx.get("https://api.justifi.ai/v1/payments/py_test123").mock(
            return_value=Response(200, json=payment_response)
        )

        result = await list_payment_refunds(mock_client, "py_test123")

        assert result["type"] == "array"
        assert len(result["data"]) == 0
