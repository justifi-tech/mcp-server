"""
Tests for JustiFi Terminal Tools

Test suite for terminal-related operations including listing, retrieval, updates, status checks, and identification.
"""

import pytest
import respx
from httpx import Response

from python.core import JustiFiClient
from python.tools.base import ToolError, ValidationError
from python.tools.terminals import (
    get_terminal_status,
    identify_terminal,
    list_terminals,
    retrieve_terminal,
    update_terminal,
)


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
def mock_terminal_data():
    """Mock terminal data."""
    return {
        "id": "trm_test123",
        "account_id": "acc_123xyz",
        "platform_account_id": "acct_789abc",
        "provider": "verifone",
        "status": "connected",
        "provider_id": "23456789",
        "provider_serial_number": "888-222-444",
        "nickname": "Store Front Terminal",
        "verified_at": "2024-01-01T15:00:00Z",
        "model_name": "e285",
        "terminal_order_created_at": "2024-01-01T15:00:00Z",
        "status_last_requested_at": "2024-01-01T15:00:00Z",
        "created_at": "2021-01-01T12:00:00Z",
        "updated_at": "2021-01-01T12:00:00Z",
    }


@pytest.fixture
def mock_terminal_status_data():
    """Mock terminal status data."""
    return {
        "id": "trm_test123",
        "status": "CONNECTED",
        "last_date_time_connected": "2024-01-01T15:00:00Z",
    }


class TestListTerminals:
    """Test list_terminals function."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_terminals_success(
        self, justifi_client, mock_token_response, mock_terminal_data
    ):
        """Test successful terminals listing."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        mock_terminals_list = {
            "data": [mock_terminal_data],
            "page_info": {
                "has_next": False,
                "has_previous": False,
                "start_cursor": "cursor_start",
                "end_cursor": "cursor_end",
            },
        }
        respx.get("https://api.justifi.ai/v1/terminals").mock(
            return_value=Response(200, json=mock_terminals_list)
        )

        result = await list_terminals(justifi_client)
        assert result["data"][0]["id"] == "trm_test123"
        assert result["page_info"]["has_next"] is False

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_terminals_with_filters(
        self, justifi_client, mock_token_response, mock_terminal_data
    ):
        """Test terminals listing with various filters."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        mock_terminals_list = {
            "data": [mock_terminal_data],
            "page_info": {"has_next": False, "has_previous": False},
        }
        respx.get("https://api.justifi.ai/v1/terminals").mock(
            return_value=Response(200, json=mock_terminals_list)
        )

        result = await list_terminals(
            justifi_client,
            limit=10,
            status="connected",
            terminal_id="trm_test123",
            provider_id="23456789",
            terminal_order_id="to_123",
            sub_account="sub_456",
        )
        assert result["data"][0]["id"] == "trm_test123"

    @pytest.mark.asyncio
    async def test_list_terminals_invalid_limit(self, justifi_client):
        """Test terminals listing with invalid limit."""
        with pytest.raises(ValidationError, match="limit must be an integer"):
            await list_terminals(justifi_client, limit=0)

        with pytest.raises(ValidationError, match="limit must be an integer"):
            await list_terminals(justifi_client, limit=101)

    @pytest.mark.asyncio
    async def test_list_terminals_invalid_cursors(self, justifi_client):
        """Test terminals listing with invalid cursor parameters."""
        with pytest.raises(ValidationError, match="Cannot specify both"):
            await list_terminals(
                justifi_client, after_cursor="abc", before_cursor="def"
            )

    @pytest.mark.asyncio
    async def test_list_terminals_invalid_status(self, justifi_client):
        """Test terminals listing with invalid status filter."""
        with pytest.raises(ValidationError, match="status must be one of"):
            await list_terminals(justifi_client, status="invalid_status")

    @pytest.mark.asyncio
    async def test_list_terminals_invalid_parameters(self, justifi_client):
        """Test terminals listing with invalid parameter types."""
        with pytest.raises(ValidationError, match="terminal_id must be a string"):
            await list_terminals(justifi_client, terminal_id=123)

        with pytest.raises(ValidationError, match="provider_id must be a string"):
            await list_terminals(justifi_client, provider_id=123)

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_terminals_api_error(self, justifi_client, mock_token_response):
        """Test terminals listing with API error."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        respx.get("https://api.justifi.ai/v1/terminals").mock(
            return_value=Response(500, json={"error": "Internal server error"})
        )

        with pytest.raises(ToolError, match="Failed to list terminals"):
            await list_terminals(justifi_client)


class TestRetrieveTerminal:
    """Test retrieve_terminal function."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_retrieve_terminal_success(
        self, justifi_client, mock_token_response, mock_terminal_data
    ):
        """Test successful terminal retrieval."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        mock_terminal_response = {"data": mock_terminal_data}
        respx.get("https://api.justifi.ai/v1/terminals/trm_test123").mock(
            return_value=Response(200, json=mock_terminal_response)
        )

        result = await retrieve_terminal(justifi_client, "trm_test123")
        assert result["data"][0]["id"] == "trm_test123"
        assert result["data"][0]["provider"] == "verifone"

    @pytest.mark.asyncio
    async def test_retrieve_terminal_invalid_id(self, justifi_client):
        """Test terminal retrieval with invalid ID."""
        with pytest.raises(ValidationError, match="terminal_id is required"):
            await retrieve_terminal(justifi_client, "")

        with pytest.raises(ValidationError, match="terminal_id is required"):
            await retrieve_terminal(justifi_client, None)

        with pytest.raises(ValidationError, match="terminal_id cannot be empty"):
            await retrieve_terminal(justifi_client, "   ")

    @respx.mock
    @pytest.mark.asyncio
    async def test_retrieve_terminal_not_found(
        self, justifi_client, mock_token_response
    ):
        """Test terminal retrieval when terminal doesn't exist."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        respx.get("https://api.justifi.ai/v1/terminals/trm_nonexistent").mock(
            return_value=Response(404, json={"error": "Terminal not found"})
        )

        with pytest.raises(ToolError, match="Failed to retrieve terminal"):
            await retrieve_terminal(justifi_client, "trm_nonexistent")

    @respx.mock
    @pytest.mark.asyncio
    async def test_retrieve_terminal_unauthorized(
        self, justifi_client, mock_token_response
    ):
        """Test terminal retrieval with unauthorized access."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        respx.get("https://api.justifi.ai/v1/terminals/trm_test123").mock(
            return_value=Response(401, json={"error": "Unauthorized"})
        )

        with pytest.raises(ToolError, match="Failed to retrieve terminal"):
            await retrieve_terminal(justifi_client, "trm_test123")


class TestUpdateTerminal:
    """Test update_terminal function."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_update_terminal_success(
        self, justifi_client, mock_token_response, mock_terminal_data
    ):
        """Test successful terminal update."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        updated_terminal = mock_terminal_data.copy()
        updated_terminal["nickname"] = "Updated Terminal Name"
        mock_update_response = {"data": updated_terminal}
        respx.patch("https://api.justifi.ai/v1/terminals/trm_test123").mock(
            return_value=Response(200, json=mock_update_response)
        )

        result = await update_terminal(
            justifi_client, "trm_test123", nickname="Updated Terminal Name"
        )
        assert result["data"][0]["id"] == "trm_test123"
        assert result["data"][0]["nickname"] == "Updated Terminal Name"

    @pytest.mark.asyncio
    async def test_update_terminal_invalid_id(self, justifi_client):
        """Test terminal update with invalid ID."""
        with pytest.raises(ValidationError, match="terminal_id is required"):
            await update_terminal(justifi_client, "", nickname="Test")

        with pytest.raises(ValidationError, match="terminal_id cannot be empty"):
            await update_terminal(justifi_client, "   ", nickname="Test")

    @pytest.mark.asyncio
    async def test_update_terminal_no_fields(self, justifi_client):
        """Test terminal update with no fields to update."""
        with pytest.raises(
            ValidationError, match="At least one field must be provided"
        ):
            await update_terminal(justifi_client, "trm_test123")

    @pytest.mark.asyncio
    async def test_update_terminal_invalid_nickname(self, justifi_client):
        """Test terminal update with invalid nickname type."""
        with pytest.raises(ValidationError, match="nickname must be a string"):
            await update_terminal(justifi_client, "trm_test123", nickname=123)

    @respx.mock
    @pytest.mark.asyncio
    async def test_update_terminal_not_found(self, justifi_client, mock_token_response):
        """Test terminal update when terminal doesn't exist."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        respx.patch("https://api.justifi.ai/v1/terminals/trm_nonexistent").mock(
            return_value=Response(404, json={"error": "Terminal not found"})
        )

        with pytest.raises(ToolError, match="Failed to update terminal"):
            await update_terminal(justifi_client, "trm_nonexistent", nickname="Test")


class TestGetTerminalStatus:
    """Test get_terminal_status function."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_terminal_status_success(
        self, justifi_client, mock_token_response, mock_terminal_status_data
    ):
        """Test successful terminal status retrieval."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        mock_status_response = {"data": mock_terminal_status_data}
        respx.get("https://api.justifi.ai/v1/terminals/trm_test123/status").mock(
            return_value=Response(200, json=mock_status_response)
        )

        result = await get_terminal_status(justifi_client, "trm_test123")
        assert result["data"][0]["id"] == "trm_test123"
        assert result["data"][0]["status"] == "CONNECTED"

    @pytest.mark.asyncio
    async def test_get_terminal_status_invalid_id(self, justifi_client):
        """Test terminal status retrieval with invalid ID."""
        with pytest.raises(ValidationError, match="terminal_id is required"):
            await get_terminal_status(justifi_client, "")

        with pytest.raises(ValidationError, match="terminal_id cannot be empty"):
            await get_terminal_status(justifi_client, "   ")

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_terminal_status_not_found(
        self, justifi_client, mock_token_response
    ):
        """Test terminal status retrieval when terminal doesn't exist."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        respx.get("https://api.justifi.ai/v1/terminals/trm_nonexistent/status").mock(
            return_value=Response(404, json={"error": "Terminal not found"})
        )

        with pytest.raises(ToolError, match="Failed to get status for terminal"):
            await get_terminal_status(justifi_client, "trm_nonexistent")

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_terminal_status_server_error(
        self, justifi_client, mock_token_response
    ):
        """Test terminal status retrieval with server error."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        respx.get("https://api.justifi.ai/v1/terminals/trm_test123/status").mock(
            return_value=Response(500, json={"error": "Internal server error"})
        )

        with pytest.raises(ToolError, match="Failed to get status for terminal"):
            await get_terminal_status(justifi_client, "trm_test123")


class TestIdentifyTerminal:
    """Test identify_terminal function."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_identify_terminal_success(self, justifi_client, mock_token_response):
        """Test successful terminal identification."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        mock_identify_response = {"message": "Identify request sent to terminal"}
        respx.post("https://api.justifi.ai/v1/terminals/trm_test123/identify").mock(
            return_value=Response(200, json=mock_identify_response)
        )

        result = await identify_terminal(justifi_client, "trm_test123")
        # The response should be standardized
        assert "data" in result
        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_identify_terminal_invalid_id(self, justifi_client):
        """Test terminal identification with invalid ID."""
        with pytest.raises(ValidationError, match="terminal_id is required"):
            await identify_terminal(justifi_client, "")

        with pytest.raises(ValidationError, match="terminal_id cannot be empty"):
            await identify_terminal(justifi_client, "   ")

    @respx.mock
    @pytest.mark.asyncio
    async def test_identify_terminal_not_found(
        self, justifi_client, mock_token_response
    ):
        """Test terminal identification when terminal doesn't exist."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        respx.post("https://api.justifi.ai/v1/terminals/trm_nonexistent/identify").mock(
            return_value=Response(404, json={"error": "Terminal not found"})
        )

        with pytest.raises(ToolError, match="Failed to identify terminal"):
            await identify_terminal(justifi_client, "trm_nonexistent")

    @respx.mock
    @pytest.mark.asyncio
    async def test_identify_terminal_forbidden(
        self, justifi_client, mock_token_response
    ):
        """Test terminal identification with forbidden access."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        respx.post("https://api.justifi.ai/v1/terminals/trm_test123/identify").mock(
            return_value=Response(403, json={"error": "Access forbidden"})
        )

        with pytest.raises(ToolError, match="Failed to identify terminal"):
            await identify_terminal(justifi_client, "trm_test123")

    @respx.mock
    @pytest.mark.asyncio
    async def test_identify_terminal_offline(self, justifi_client, mock_token_response):
        """Test terminal identification when terminal is offline."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )
        respx.post("https://api.justifi.ai/v1/terminals/trm_test123/identify").mock(
            return_value=Response(422, json={"error": "Terminal is offline"})
        )

        with pytest.raises(ToolError, match="Failed to identify terminal"):
            await identify_terminal(justifi_client, "trm_test123")


class TestTerminalToolsIntegration:
    """Integration tests for terminal tools."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_terminal_workflow(
        self,
        justifi_client,
        mock_token_response,
        mock_terminal_data,
        mock_terminal_status_data,
    ):
        """Test complete terminal workflow: list, retrieve, update, status, identify."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )

        # Mock list terminals
        mock_terminals_list = {"data": [mock_terminal_data]}
        respx.get("https://api.justifi.ai/v1/terminals").mock(
            return_value=Response(200, json=mock_terminals_list)
        )

        # Mock retrieve terminal
        respx.get("https://api.justifi.ai/v1/terminals/trm_test123").mock(
            return_value=Response(200, json={"data": mock_terminal_data})
        )

        # Mock update terminal
        updated_terminal = mock_terminal_data.copy()
        updated_terminal["nickname"] = "Updated Name"
        respx.patch("https://api.justifi.ai/v1/terminals/trm_test123").mock(
            return_value=Response(200, json={"data": updated_terminal})
        )

        # Mock get status
        respx.get("https://api.justifi.ai/v1/terminals/trm_test123/status").mock(
            return_value=Response(200, json={"data": mock_terminal_status_data})
        )

        # Mock identify
        respx.post("https://api.justifi.ai/v1/terminals/trm_test123/identify").mock(
            return_value=Response(200, json={"message": "Identify request sent"})
        )

        # Execute workflow
        terminals_list = await list_terminals(justifi_client)
        terminal_id = terminals_list["data"][0]["id"]

        terminal_details = await retrieve_terminal(justifi_client, terminal_id)
        assert terminal_details["data"][0]["id"] == terminal_id

        updated = await update_terminal(
            justifi_client, terminal_id, nickname="Updated Name"
        )
        assert updated["data"][0]["nickname"] == "Updated Name"

        status = await get_terminal_status(justifi_client, terminal_id)
        assert status["data"][0]["status"] == "CONNECTED"

        identify_result = await identify_terminal(justifi_client, terminal_id)
        assert "data" in identify_result
