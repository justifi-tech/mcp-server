"""Tests for sub account tools."""

from unittest.mock import AsyncMock

import pytest
import respx
from httpx import Response

from python.core import JustiFiClient
from python.tools.base import ToolError, ValidationError
from python.tools.sub_accounts import (
    get_sub_account,
    get_sub_account_payout_account,
    get_sub_account_settings,
    list_sub_accounts,
)


@pytest.fixture
def client():
    """Create a test JustiFi client."""
    client = JustiFiClient(client_id="test_id", client_secret="test_secret")
    client.get_access_token = AsyncMock(return_value="test_token")
    return client


@pytest.fixture
def mock_sub_account():
    """Mock sub account data."""
    return {
        "id": "acc_test123",
        "name": "Test Sub Account",
        "account_type": "test",
        "status": "enabled",
        "currency": "usd",
        "platform_account_id": "pla_test456",
        "payout_account_id": "pba_test789",
        "business_id": "biz_test101",
        "application_fee_rates": [],
    }


@pytest.fixture
def mock_payout_account():
    """Mock payout account data."""
    return {
        "id": "pba_test789",
        "account_type": "bank",
        "routing_number": "123456789",
        "account_number_last4": "1234",
        "status": "active",
    }


@pytest.fixture
def mock_sub_account_settings():
    """Mock sub account settings data."""
    return {
        "id": "acc_test123",
        "settings": {
            "payment_notifications": True,
            "dispute_notifications": True,
            "payout_notifications": False,
        },
    }


@pytest.mark.asyncio
class TestListSubAccounts:
    """Test list_sub_accounts function."""

    async def test_list_sub_accounts_success(self, client, mock_sub_account):
        """Test successful sub accounts listing."""
        expected_response = {
            "data": [mock_sub_account],
            "page_info": {
                "has_next": False,
                "has_previous": False,
                "start_cursor": "start123",
                "end_cursor": "end123",
            },
        }

        with respx.mock:
            respx.get("https://api.justifi.ai/v1/sub_accounts").mock(
                return_value=Response(200, json=expected_response)
            )

            result = await list_sub_accounts(client)
            assert result == expected_response

    async def test_list_sub_accounts_with_status_filter(self, client, mock_sub_account):
        """Test listing sub accounts with status filter."""
        expected_response = {
            "data": [mock_sub_account],
            "page_info": {
                "has_next": False,
                "has_previous": False,
                "start_cursor": "start123",
                "end_cursor": "end123",
            },
        }

        with respx.mock:
            respx.get("https://api.justifi.ai/v1/sub_accounts").mock(
                return_value=Response(200, json=expected_response)
            )

            result = await list_sub_accounts(client, status="enabled")
            assert result == expected_response

    async def test_list_sub_accounts_with_pagination(self, client, mock_sub_account):
        """Test listing sub accounts with pagination."""
        expected_response = {
            "data": [mock_sub_account],
            "page_info": {
                "has_next": True,
                "has_previous": False,
                "start_cursor": "start123",
                "end_cursor": "end123",
            },
        }

        with respx.mock:
            respx.get("https://api.justifi.ai/v1/sub_accounts").mock(
                return_value=Response(200, json=expected_response)
            )

            result = await list_sub_accounts(client, limit=10, after_cursor="cursor123")
            assert result == expected_response

    async def test_list_sub_accounts_invalid_limit(self, client):
        """Test list_sub_accounts with invalid limit."""
        with pytest.raises(ValidationError) as exc_info:
            await list_sub_accounts(client, limit=0)

        assert "limit must be an integer between 1 and 100" in str(exc_info.value)

    async def test_list_sub_accounts_invalid_limit_too_high(self, client):
        """Test list_sub_accounts with limit too high."""
        with pytest.raises(ValidationError) as exc_info:
            await list_sub_accounts(client, limit=101)

        assert "limit must be an integer between 1 and 100" in str(exc_info.value)

    async def test_list_sub_accounts_invalid_status(self, client):
        """Test list_sub_accounts with invalid status."""
        with pytest.raises(ValidationError) as exc_info:
            await list_sub_accounts(client, status="invalid_status")

        assert "status must be one of:" in str(exc_info.value)

    async def test_list_sub_accounts_both_cursors(self, client):
        """Test list_sub_accounts with both cursors specified."""
        with pytest.raises(ValidationError) as exc_info:
            await list_sub_accounts(
                client, after_cursor="after", before_cursor="before"
            )

        assert "Cannot specify both after_cursor and before_cursor" in str(
            exc_info.value
        )

    async def test_list_sub_accounts_api_error(self, client):
        """Test list_sub_accounts with API error."""
        with respx.mock:
            respx.get("https://api.justifi.ai/v1/sub_accounts").mock(
                return_value=Response(500, json={"error": "Server error"})
            )

            with pytest.raises(ToolError) as exc_info:
                await list_sub_accounts(client)

            assert "Failed to list sub accounts" in str(exc_info.value)


@pytest.mark.asyncio
class TestGetSubAccount:
    """Test get_sub_account function."""

    async def test_get_sub_account_success(self, client, mock_sub_account):
        """Test successful sub account retrieval."""
        sub_account_id = "acc_test123"

        with respx.mock:
            respx.get(f"https://api.justifi.ai/v1/sub_accounts/{sub_account_id}").mock(
                return_value=Response(200, json=mock_sub_account)
            )

            result = await get_sub_account(client, sub_account_id)
            assert result == mock_sub_account

    @pytest.mark.parametrize(
        "sub_account_id,expected_error",
        [
            ("", "sub_account_id cannot be empty or whitespace"),
            ("   ", "sub_account_id cannot be empty or whitespace"),
            (None, "sub_account_id is required and must be a non-empty string"),
        ],
    )
    async def test_get_sub_account_invalid_id(
        self, client, sub_account_id, expected_error
    ):
        """Test get_sub_account with invalid IDs."""
        with pytest.raises(ValidationError) as exc_info:
            await get_sub_account(client, sub_account_id)

        assert expected_error in str(exc_info.value)

    async def test_get_sub_account_not_found(self, client):
        """Test get_sub_account with non-existent ID."""
        sub_account_id = "acc_nonexistent"

        with respx.mock:
            respx.get(f"https://api.justifi.ai/v1/sub_accounts/{sub_account_id}").mock(
                return_value=Response(404, json={"error": "Sub account not found"})
            )

            with pytest.raises(ToolError) as exc_info:
                await get_sub_account(client, sub_account_id)

            assert f"Failed to retrieve sub account {sub_account_id}" in str(
                exc_info.value
            )


@pytest.mark.asyncio
class TestGetSubAccountPayoutAccount:
    """Test get_sub_account_payout_account function."""

    async def test_get_sub_account_payout_account_success(
        self, client, mock_payout_account
    ):
        """Test successful sub account payout account retrieval."""
        sub_account_id = "acc_test123"

        with respx.mock:
            respx.get(
                f"https://api.justifi.ai/v1/sub_accounts/{sub_account_id}/payout_account"
            ).mock(return_value=Response(200, json=mock_payout_account))

            result = await get_sub_account_payout_account(client, sub_account_id)
            assert result == mock_payout_account

    @pytest.mark.parametrize(
        "sub_account_id,expected_error",
        [
            ("", "sub_account_id cannot be empty or whitespace"),
            (None, "sub_account_id is required and must be a non-empty string"),
        ],
    )
    async def test_get_sub_account_payout_account_invalid_id(
        self, client, sub_account_id, expected_error
    ):
        """Test get_sub_account_payout_account with invalid IDs."""
        with pytest.raises(ValidationError) as exc_info:
            await get_sub_account_payout_account(client, sub_account_id)

        assert expected_error in str(exc_info.value)

    async def test_get_sub_account_payout_account_not_found(self, client):
        """Test get_sub_account_payout_account with non-existent ID."""
        sub_account_id = "acc_nonexistent"

        with respx.mock:
            respx.get(
                f"https://api.justifi.ai/v1/sub_accounts/{sub_account_id}/payout_account"
            ).mock(
                return_value=Response(404, json={"error": "Payout account not found"})
            )

            with pytest.raises(ToolError) as exc_info:
                await get_sub_account_payout_account(client, sub_account_id)

            assert (
                f"Failed to retrieve payout account for sub account {sub_account_id}"
                in str(exc_info.value)
            )


@pytest.mark.asyncio
class TestGetSubAccountSettings:
    """Test get_sub_account_settings function."""

    async def test_get_sub_account_settings_success(
        self, client, mock_sub_account_settings
    ):
        """Test successful sub account settings retrieval."""
        sub_account_id = "acc_test123"

        with respx.mock:
            respx.get(
                f"https://api.justifi.ai/v1/sub_accounts/{sub_account_id}/settings"
            ).mock(return_value=Response(200, json=mock_sub_account_settings))

            result = await get_sub_account_settings(client, sub_account_id)
            assert result == mock_sub_account_settings

    @pytest.mark.parametrize(
        "sub_account_id,expected_error",
        [
            ("", "sub_account_id cannot be empty or whitespace"),
            (None, "sub_account_id is required and must be a non-empty string"),
        ],
    )
    async def test_get_sub_account_settings_invalid_id(
        self, client, sub_account_id, expected_error
    ):
        """Test get_sub_account_settings with invalid IDs."""
        with pytest.raises(ValidationError) as exc_info:
            await get_sub_account_settings(client, sub_account_id)

        assert expected_error in str(exc_info.value)

    async def test_get_sub_account_settings_not_found(self, client):
        """Test get_sub_account_settings with non-existent ID."""
        sub_account_id = "acc_nonexistent"

        with respx.mock:
            respx.get(
                f"https://api.justifi.ai/v1/sub_accounts/{sub_account_id}/settings"
            ).mock(return_value=Response(404, json={"error": "Settings not found"}))

            with pytest.raises(ToolError) as exc_info:
                await get_sub_account_settings(client, sub_account_id)

            assert (
                f"Failed to retrieve settings for sub account {sub_account_id}"
                in str(exc_info.value)
            )
