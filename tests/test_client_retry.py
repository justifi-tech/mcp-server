"""Test JustiFi client retry logic and error handling.

This module contains comprehensive tests for the retry behavior, exponential backoff,
and error handling in the JustiFiClient. Tool-specific tests should mock the client
to avoid these retry delays and focus on tool-specific logic.
"""

import pytest
import respx
from httpx import Response

from python.core import APIError, AuthenticationError, JustiFiClient

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_client():
    """Create a mock JustiFi client."""
    return JustiFiClient("test_id", "test_secret")


@pytest.fixture
def mock_token_response():
    """Mock OAuth token response."""
    return {"access_token": "test_token_123", "expires_in": 3600}


class TestClientRetryLogic:
    """Test comprehensive retry logic and exponential backoff."""

    @respx.mock
    async def test_server_error_retry_with_backoff(
        self, mock_client, mock_token_response
    ):
        """Test server errors trigger exponential backoff retry."""
        # Mock OAuth token
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )

        # Mock API endpoint to fail with 500 errors for all retries
        respx.get("https://api.justifi.ai/v1/test").mock(
            return_value=Response(500, json={"error": "Internal server error"})
        )

        with pytest.raises(APIError) as exc_info:
            await mock_client.request("GET", "/v1/test", retries=2)

        assert exc_info.value.status_code == 500
        assert "JustiFi API is experiencing issues" in str(exc_info.value)

        # Verify it made multiple attempts (original + 2 retries = 3 total)
        assert len(respx.calls) == 4  # 1 OAuth + 3 API calls

    @respx.mock
    async def test_server_error_eventual_success(
        self, mock_client, mock_token_response
    ):
        """Test server error that succeeds on retry."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )

        # First call fails, second succeeds
        respx.get("https://api.justifi.ai/v1/test").mock(
            side_effect=[
                Response(500, json={"error": "Temporary error"}),
                Response(200, json={"data": "success"}),
            ]
        )

        result = await mock_client.request("GET", "/v1/test", retries=2)

        assert result == {"data": "success"}
        assert len(respx.calls) == 3  # 1 OAuth + 2 API calls

    @respx.mock
    async def test_rate_limit_retry(self, mock_client, mock_token_response):
        """Test rate limit (429) triggers retry."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )

        # Rate limit should eventually result in RateLimitError, not APIError
        respx.get("https://api.justifi.ai/v1/test").mock(
            return_value=Response(429, json={"error": "Rate limit exceeded"})
        )

        with pytest.raises(
            APIError
        ):  # 429 gets handled as APIError in current implementation
            await mock_client.request("GET", "/v1/test", retries=1)

        # Should have retried once
        assert len(respx.calls) == 3  # 1 OAuth + 2 API calls

    @respx.mock
    async def test_client_error_no_retry(self, mock_client, mock_token_response):
        """Test 4xx errors (except 429) don't retry."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )

        respx.get("https://api.justifi.ai/v1/test").mock(
            return_value=Response(400, json={"error": "Bad request"})
        )

        from python.core import ValidationError

        with pytest.raises(ValidationError):  # Will raise ValidationError
            await mock_client.request("GET", "/v1/test", retries=3)

        # Should NOT have retried
        assert len(respx.calls) == 2  # 1 OAuth + 1 API call

    @respx.mock
    async def test_network_error_retry(self, mock_client, mock_token_response):
        """Test network errors trigger retry."""
        import httpx

        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )

        # Simulate httpx.RequestError then success
        respx.get("https://api.justifi.ai/v1/test").mock(
            side_effect=[
                httpx.ConnectError("Connection failed"),
                Response(200, json={"data": "success"}),
            ]
        )

        result = await mock_client.request("GET", "/v1/test", retries=2)
        assert result == {"data": "success"}

    @respx.mock
    async def test_retry_disabled(self, mock_client, mock_token_response):
        """Test that retries=0 disables retry behavior."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )

        respx.get("https://api.justifi.ai/v1/test").mock(
            return_value=Response(500, json={"error": "Server error"})
        )

        with pytest.raises(APIError):
            await mock_client.request("GET", "/v1/test", retries=0)

        # Should only make one attempt
        assert len(respx.calls) == 2  # 1 OAuth + 1 API call


class TestClientErrorHandling:
    """Test specific error handling without retry delays."""

    @respx.mock
    async def test_authentication_error_401(self, mock_client):
        """Test 401 authentication error handling."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(
                200, json={"access_token": "test_token", "expires_in": 3600}
            )
        )

        respx.get("https://api.justifi.ai/v1/test").mock(
            return_value=Response(401, json={"error": "Unauthorized"})
        )

        with pytest.raises(AuthenticationError) as exc_info:
            await mock_client.request("GET", "/v1/test", retries=0)

        assert exc_info.value.error_code == "token_expired"

    @respx.mock
    async def test_validation_error_400(self, mock_client, mock_token_response):
        """Test 400 validation error handling."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )

        respx.get("https://api.justifi.ai/v1/test").mock(
            return_value=Response(400, json={"error": "Invalid request"})
        )

        with pytest.raises(Exception) as exc_info:  # ValidationError
            await mock_client.request("GET", "/v1/test", retries=0)

        assert "Invalid request" in str(exc_info.value)

    @respx.mock
    async def test_not_found_error_404(self, mock_client, mock_token_response):
        """Test 404 not found error handling."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )

        respx.get("https://api.justifi.ai/v1/test").mock(
            return_value=Response(404, json={"error": "Resource not found"})
        )

        with pytest.raises(Exception) as exc_info:  # ValidationError
            await mock_client.request("GET", "/v1/test", retries=0)

        assert "Resource not found" in str(exc_info.value)

    @respx.mock
    async def test_various_server_errors(self, mock_client, mock_token_response):
        """Test different server error codes."""
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )

        # Test 502 Bad Gateway
        respx.get("https://api.justifi.ai/v1/test502").mock(
            return_value=Response(502, json={"error": "Bad Gateway"})
        )

        with pytest.raises(APIError) as exc_info:
            await mock_client.request("GET", "/v1/test502", retries=0)

        assert exc_info.value.status_code == 502
        assert "temporarily unavailable" in str(exc_info.value)

        # Test 503 Service Unavailable
        respx.get("https://api.justifi.ai/v1/test503").mock(
            return_value=Response(503, json={"error": "Service Unavailable"})
        )

        with pytest.raises(APIError) as exc_info:
            await mock_client.request("GET", "/v1/test503", retries=0)

        assert exc_info.value.status_code == 503
        assert "under maintenance" in str(exc_info.value)


class TestHandleToolErrorsDecorator:
    """Test the @handle_tool_errors decorator functionality."""

    async def test_decorator_wraps_api_errors(self):
        """Test that @handle_tool_errors wraps APIError in ToolError."""
        from unittest.mock import AsyncMock

        from python.core import APIError
        from python.tools.base import ToolError, handle_tool_errors

        @handle_tool_errors
        async def mock_tool_function(client):
            """Mock tool function that raises APIError."""
            raise APIError("Server error", status_code=500)

        mock_client = AsyncMock()

        with pytest.raises(ToolError) as exc_info:
            await mock_tool_function(mock_client)

        assert str(exc_info.value) == "Server error"
        assert exc_info.value.error_type == "APIError"

    async def test_decorator_preserves_validation_errors(self):
        """Test that @handle_tool_errors preserves ValidationError as-is."""
        from unittest.mock import AsyncMock

        from python.tools.base import ValidationError, handle_tool_errors

        @handle_tool_errors
        async def mock_tool_function(client):
            """Mock tool function that raises ValidationError."""
            raise ValidationError(
                "Invalid input", field="test_field", value="test_value"
            )

        mock_client = AsyncMock()

        with pytest.raises(ValidationError) as exc_info:
            await mock_tool_function(mock_client)

        assert str(exc_info.value) == "Invalid input"
        assert exc_info.value.field == "test_field"
        assert exc_info.value.value == "test_value"

    async def test_decorator_wraps_generic_exceptions(self):
        """Test that @handle_tool_errors wraps generic exceptions in ToolError."""
        from unittest.mock import AsyncMock

        from python.tools.base import ToolError, handle_tool_errors

        @handle_tool_errors
        async def mock_tool_function(client):
            """Mock tool function that raises generic exception."""
            raise ValueError("Generic error")

        mock_client = AsyncMock()

        with pytest.raises(ToolError) as exc_info:
            await mock_tool_function(mock_client)

        assert str(exc_info.value) == "Generic error"
        assert exc_info.value.error_type == "ValueError"

    async def test_decorator_allows_success(self):
        """Test that @handle_tool_errors allows successful execution."""
        from unittest.mock import AsyncMock

        from python.tools.base import handle_tool_errors

        @handle_tool_errors
        async def mock_tool_function(client):
            """Mock tool function that succeeds."""
            return {"success": True, "data": "test"}

        mock_client = AsyncMock()

        result = await mock_tool_function(mock_client)

        assert result == {"success": True, "data": "test"}
