"""
Tests for Payment Method Group Tools

Covers validation, error scenarios, and successful operations for payment method group management.
"""

import pytest
import respx
from httpx import Response

from python.core import JustiFiClient
from python.tools.base import ToolError, ValidationError
from python.tools.payment_method_groups import (
    create_payment_method_group,
    list_payment_method_groups,
    remove_payment_method_from_group,
    retrieve_payment_method_group,
    update_payment_method_group,
)


@pytest.fixture
def mock_client():
    return JustiFiClient(
        client_id="test_client_id",
        client_secret="test_client_secret",
    )


@pytest.fixture
def mock_oauth_token():
    return {
        "access_token": "test_access_token_12345",
        "token_type": "Bearer",
        "expires_in": 3600,
    }


class TestCreatePaymentMethodGroup:
    """Test create_payment_method_group function."""

    @pytest.mark.asyncio
    async def test_create_group_success(self, mock_client, mock_oauth_token):
        """Test successful group creation with minimal data."""
        mock_response = {
            "data": {
                "id": "pmg_123abc",
                "name": "Test Group",
                "description": None,
                "payment_method_count": 0,
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
            }
        }

        with respx.mock:
            respx.post("https://api.justifi.ai/oauth/token").mock(
                return_value=Response(200, json=mock_oauth_token)
            )

            respx.post("https://api.justifi.ai/v1/payment_method_groups").mock(
                return_value=Response(200, json=mock_response)
            )

            result = await create_payment_method_group(mock_client, "Test Group")

            assert result["data"][0]["name"] == "Test Group"
            assert result["metadata"]["tool"] == "create_payment_method_group"

    @pytest.mark.asyncio
    async def test_create_group_with_description_and_payment_methods(
        self, mock_client, mock_oauth_token
    ):
        """Test group creation with description and payment methods."""

        mock_response = {
            "data": {
                "id": "pmg_123abc",
                "name": "Test Group",
                "description": "Test Description",
                "payment_method_count": 2,
                "payment_methods": ["pm_123", "pm_456"],
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
            }
        }

        with respx.mock:
            respx.post("https://api.justifi.ai/oauth/token").mock(
                return_value=Response(200, json=mock_oauth_token)
            )
            respx.post("https://api.justifi.ai/v1/payment_method_groups").mock(
                return_value=Response(200, json=mock_response)
            )

            result = await create_payment_method_group(
                mock_client,
                "Test Group",
                description="Test Description",
                payment_method_ids=["pm_123", "pm_456"],
            )

            assert result["data"][0]["description"] == "Test Description"
            assert result["data"][0]["payment_method_count"] == 2

    @pytest.mark.asyncio
    async def test_create_group_empty_name_error(self):
        """Test validation error for empty name."""

        with pytest.raises(ValidationError) as exc_info:
            await create_payment_method_group(mock_client, "")

        assert "name is required and must be a non-empty string" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_group_none_name_error(self):
        """Test validation error for None name."""

        with pytest.raises(ValidationError) as exc_info:
            await create_payment_method_group(mock_client, None)

        assert "name is required and must be a non-empty string" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_group_invalid_description_type_error(self):
        """Test validation error for invalid description type."""

        with pytest.raises(ValidationError) as exc_info:
            await create_payment_method_group(mock_client, "Test", description=123)

        assert "description must be a string if provided" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_group_invalid_payment_method_ids_type_error(self):
        """Test validation error for invalid payment_method_ids type."""

        with pytest.raises(ValidationError) as exc_info:
            await create_payment_method_group(
                mock_client, "Test", payment_method_ids="not_a_list"
            )

        assert "payment_method_ids must be a list if provided" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_group_empty_payment_method_id_error(self):
        """Test validation error for empty payment method ID in list."""

        with pytest.raises(ValidationError) as exc_info:
            await create_payment_method_group(
                mock_client, "Test", payment_method_ids=["pm_123", ""]
            )

        assert "payment_method_ids[1] must be a non-empty string" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_group_http_400_error(self):
        """Test HTTP 400 error handling."""

        with respx.mock:
            respx.post("https://api.justifi.ai/v1/payment_method_groups").mock(
                return_value=Response(400, json={"error": "Bad Request"})
            )

            with pytest.raises(ToolError) as exc_info:
                await create_payment_method_group(mock_client, "Test Group")

            assert "Failed to create payment method group" in str(exc_info.value)
            assert exc_info.value.error_type == "PaymentMethodGroupCreationError"


class TestListPaymentMethodGroups:
    """Test list_payment_method_groups function."""

    @pytest.mark.asyncio
    async def test_list_groups_success(self, mock_client, mock_oauth_token):
        """Test successful groups listing."""

        mock_response = {
            "data": [
                {
                    "id": "pmg_123abc",
                    "name": "Group 1",
                    "payment_method_count": 2,
                },
                {
                    "id": "pmg_456def",
                    "name": "Group 2",
                    "payment_method_count": 0,
                },
            ],
            "page_info": {
                "has_next_page": False,
                "has_previous_page": False,
            },
        }

        with respx.mock:
            respx.post("https://api.justifi.ai/oauth/token").mock(
                return_value=Response(200, json=mock_oauth_token)
            )
            respx.get("https://api.justifi.ai/v1/payment_method_groups").mock(
                return_value=Response(200, json=mock_response)
            )

            result = await list_payment_method_groups(mock_client)

            assert len(result["data"]) == 2
            assert result["data"][0]["name"] == "Group 1"
            assert result["metadata"]["tool"] == "list_payment_method_groups"

    @pytest.mark.asyncio
    async def test_list_groups_with_pagination(self, mock_client, mock_oauth_token):
        """Test groups listing with pagination parameters."""

        mock_response = {
            "data": [{"id": "pmg_123abc", "name": "Group 1"}],
            "page_info": {"has_next_page": True, "has_previous_page": False},
        }

        with respx.mock:
            respx.post("https://api.justifi.ai/oauth/token").mock(
                return_value=Response(200, json=mock_oauth_token)
            )
            request = respx.get("https://api.justifi.ai/v1/payment_method_groups").mock(
                return_value=Response(200, json=mock_response)
            )

            result = await list_payment_method_groups(
                mock_client, limit=10, after_cursor="cursor_123"
            )

            assert len(result["data"]) == 1
            assert request.call_count == 1

            # Check that the correct parameters were sent
            called_request = request.calls[0].request
            assert "limit=10" in str(called_request.url)
            assert "after_cursor=cursor_123" in str(called_request.url)

    @pytest.mark.asyncio
    async def test_list_groups_invalid_limit_error(self):
        """Test validation error for invalid limit."""

        with pytest.raises(ValidationError) as exc_info:
            await list_payment_method_groups(mock_client, limit=0)

        assert "limit must be an integer between 1 and 100" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_groups_limit_too_high_error(self):
        """Test validation error for limit too high."""

        with pytest.raises(ValidationError) as exc_info:
            await list_payment_method_groups(mock_client, limit=101)

        assert "limit must be an integer between 1 and 100" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_groups_both_cursors_error(self, mock_client):
        """Test validation error for both cursors provided."""

        with pytest.raises(ValidationError) as exc_info:
            await list_payment_method_groups(
                mock_client, after_cursor="cursor1", before_cursor="cursor2"
            )

        assert "Cannot specify both after_cursor and before_cursor" in str(
            exc_info.value
        )


class TestRetrievePaymentMethodGroup:
    """Test retrieve_payment_method_group function."""

    @pytest.mark.asyncio
    async def test_retrieve_group_success(self, mock_client, mock_oauth_token):
        """Test successful group retrieval."""

        mock_response = {
            "data": {
                "id": "pmg_123abc",
                "name": "Test Group",
                "description": "Test Description",
                "payment_method_count": 2,
                "payment_methods": [
                    {"id": "pm_123", "type": "card"},
                    {"id": "pm_456", "type": "bank_account"},
                ],
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
            }
        }

        with respx.mock:
            respx.post("https://api.justifi.ai/oauth/token").mock(
                return_value=Response(200, json=mock_oauth_token)
            )
            respx.get(
                "https://api.justifi.ai/v1/payment_method_groups/pmg_123abc"
            ).mock(return_value=Response(200, json=mock_response))

            result = await retrieve_payment_method_group(mock_client, "pmg_123abc")

            assert result["data"][0]["name"] == "Test Group"
            assert result["data"][0]["payment_method_count"] == 2
            assert result["metadata"]["tool"] == "retrieve_payment_method_group"

    @pytest.mark.asyncio
    async def test_retrieve_group_empty_id_error(self):
        """Test validation error for empty group_id."""

        with pytest.raises(ValidationError) as exc_info:
            await retrieve_payment_method_group(mock_client, "")

        assert "group_id is required and must be a non-empty string" in str(
            exc_info.value
        )

    @pytest.mark.asyncio
    async def test_retrieve_group_none_id_error(self):
        """Test validation error for None group_id."""

        with pytest.raises(ValidationError) as exc_info:
            await retrieve_payment_method_group(mock_client, None)

        assert "group_id is required and must be a non-empty string" in str(
            exc_info.value
        )

    @pytest.mark.asyncio
    async def test_retrieve_group_http_404_error(self):
        """Test HTTP 404 error handling."""

        with respx.mock:
            respx.get(
                "https://api.justifi.ai/v1/payment_method_groups/pmg_notfound"
            ).mock(return_value=Response(404, json={"error": "Not Found"}))

            with pytest.raises(ToolError) as exc_info:
                await retrieve_payment_method_group(mock_client, "pmg_notfound")

            assert "Failed to retrieve payment method group pmg_notfound" in str(
                exc_info.value
            )
            assert exc_info.value.error_type == "PaymentMethodGroupRetrievalError"


class TestUpdatePaymentMethodGroup:
    """Test update_payment_method_group function."""

    @pytest.mark.asyncio
    async def test_update_group_name_only(self, mock_client, mock_oauth_token):
        """Test updating group name only."""

        mock_response = {
            "data": {
                "id": "pmg_123abc",
                "name": "Updated Name",
                "description": "Original Description",
                "payment_method_count": 2,
                "updated_at": "2023-01-02T00:00:00Z",
            }
        }

        with respx.mock:
            respx.post("https://api.justifi.ai/oauth/token").mock(
                return_value=Response(200, json=mock_oauth_token)
            )
            respx.patch(
                "https://api.justifi.ai/v1/payment_method_groups/pmg_123abc"
            ).mock(return_value=Response(200, json=mock_response))

            result = await update_payment_method_group(
                mock_client, "pmg_123abc", name="Updated Name"
            )

            assert result["data"][0]["name"] == "Updated Name"
            assert result["metadata"]["tool"] == "update_payment_method_group"

    @pytest.mark.asyncio
    async def test_update_group_all_fields(self, mock_client, mock_oauth_token):
        """Test updating all fields."""

        mock_response = {
            "data": {
                "id": "pmg_123abc",
                "name": "Updated Name",
                "description": "Updated Description",
                "payment_method_count": 1,
                "payment_methods": [{"id": "pm_789", "type": "card"}],
                "updated_at": "2023-01-02T00:00:00Z",
            }
        }

        with respx.mock:
            respx.post("https://api.justifi.ai/oauth/token").mock(
                return_value=Response(200, json=mock_oauth_token)
            )
            respx.patch(
                "https://api.justifi.ai/v1/payment_method_groups/pmg_123abc"
            ).mock(return_value=Response(200, json=mock_response))

            result = await update_payment_method_group(
                mock_client,
                "pmg_123abc",
                name="Updated Name",
                description="Updated Description",
                payment_method_ids=["pm_789"],
            )

            assert result["data"][0]["name"] == "Updated Name"
            assert result["data"][0]["description"] == "Updated Description"
            assert result["data"][0]["payment_method_count"] == 1

    @pytest.mark.asyncio
    async def test_update_group_empty_id_error(self):
        """Test validation error for empty group_id."""

        with pytest.raises(ValidationError) as exc_info:
            await update_payment_method_group(mock_client, "", name="Test")

        assert "group_id is required and must be a non-empty string" in str(
            exc_info.value
        )

    @pytest.mark.asyncio
    async def test_update_group_no_fields_error(self):
        """Test validation error for no update fields provided."""

        with pytest.raises(ValidationError) as exc_info:
            await update_payment_method_group(mock_client, "pmg_123abc")

        assert (
            "At least one of name, description, or payment_method_ids must be provided"
            in str(exc_info.value)
        )

    @pytest.mark.asyncio
    async def test_update_group_empty_name_error(self):
        """Test validation error for empty name."""

        with pytest.raises(ValidationError) as exc_info:
            await update_payment_method_group(mock_client, "pmg_123abc", name="")

        assert "name cannot be empty or whitespace if provided" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_group_invalid_payment_method_ids_error(self):
        """Test validation error for invalid payment_method_ids."""

        with pytest.raises(ValidationError) as exc_info:
            await update_payment_method_group(
                mock_client, "pmg_123abc", payment_method_ids=["valid", ""]
            )

        assert "payment_method_ids[1] must be a non-empty string" in str(exc_info.value)


class TestRemovePaymentMethodFromGroup:
    """Test remove_payment_method_from_group function."""

    @pytest.mark.asyncio
    async def test_remove_payment_method_success(self, mock_client, mock_oauth_token):
        """Test successful payment method removal."""

        mock_response = {
            "data": {
                "id": "pmg_123abc",
                "name": "Test Group",
                "payment_method_count": 1,  # Decreased after removal
                "payment_methods": [{"id": "pm_456", "type": "card"}],
                "updated_at": "2023-01-02T00:00:00Z",
            }
        }

        with respx.mock:
            respx.post("https://api.justifi.ai/oauth/token").mock(
                return_value=Response(200, json=mock_oauth_token)
            )
            respx.delete(
                "https://api.justifi.ai/v1/payment_method_groups/pmg_123abc/payment_methods/pm_123"
            ).mock(return_value=Response(200, json=mock_response))

            result = await remove_payment_method_from_group(
                mock_client, "pmg_123abc", "pm_123"
            )

            assert result["data"][0]["payment_method_count"] == 1
            assert result["metadata"]["tool"] == "remove_payment_method_from_group"

    @pytest.mark.asyncio
    async def test_remove_payment_method_empty_group_id_error(self):
        """Test validation error for empty group_id."""

        with pytest.raises(ValidationError) as exc_info:
            await remove_payment_method_from_group(mock_client, "", "pm_123")

        assert "group_id is required and must be a non-empty string" in str(
            exc_info.value
        )

    @pytest.mark.asyncio
    async def test_remove_payment_method_empty_payment_method_id_error(self):
        """Test validation error for empty payment_method_id."""

        with pytest.raises(ValidationError) as exc_info:
            await remove_payment_method_from_group(mock_client, "pmg_123abc", "")

        assert "payment_method_id is required and must be a non-empty string" in str(
            exc_info.value
        )

    @pytest.mark.asyncio
    async def test_remove_payment_method_none_payment_method_id_error(self):
        """Test validation error for None payment_method_id."""

        with pytest.raises(ValidationError) as exc_info:
            await remove_payment_method_from_group(mock_client, "pmg_123abc", None)

        assert "payment_method_id is required and must be a non-empty string" in str(
            exc_info.value
        )

    @pytest.mark.asyncio
    async def test_remove_payment_method_http_404_error(self):
        """Test HTTP 404 error handling."""

        with respx.mock:
            respx.delete(
                "https://api.justifi.ai/v1/payment_method_groups/pmg_123abc/payment_methods/pm_notfound"
            ).mock(return_value=Response(404, json={"error": "Not Found"}))

            with pytest.raises(ToolError) as exc_info:
                await remove_payment_method_from_group(
                    mock_client, "pmg_123abc", "pm_notfound"
                )

            assert (
                "Failed to remove payment method pm_notfound from group pmg_123abc"
                in str(exc_info.value)
            )
            assert exc_info.value.error_type == "PaymentMethodGroupRemovalError"


class TestGeneralErrorScenarios:
    """Test general error scenarios for all payment method group tools."""
