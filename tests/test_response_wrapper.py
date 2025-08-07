"""Tests for the response wrapper utility."""

import pytest

from python.tools.response_wrapper import (is_standardization_enabled,
                                           maybe_standardize_response,
                                           set_standardization_enabled,
                                           wrap_tool_call)


@pytest.fixture
def sample_api_response():
    """Sample JustiFi API response."""
    return {
        "data": [
            {"id": "po_123", "status": "completed"},
            {"id": "po_456", "status": "pending"},
        ],
        "page_info": {"has_next": False},
    }


@pytest.fixture
def sample_custom_response():
    """Sample custom response (like get_recent_payouts)."""
    return {"payouts": [{"id": "po_123"}], "count": 1, "limit": 10}


class TestStandardizationConfiguration:
    """Test standardization configuration functions."""

    def test_default_standardization_disabled(self):
        """Test that standardization is disabled by default."""
        # Reset to ensure clean state
        set_standardization_enabled(False)
        assert is_standardization_enabled() is False

    def test_enable_standardization(self):
        """Test enabling standardization."""
        set_standardization_enabled(True)
        assert is_standardization_enabled() is True

        # Clean up
        set_standardization_enabled(False)

    def test_disable_standardization(self):
        """Test disabling standardization."""
        set_standardization_enabled(True)
        set_standardization_enabled(False)
        assert is_standardization_enabled() is False


@pytest.mark.asyncio
class TestMaybeStandardizeResponse:
    """Test conditional response standardization."""

    async def test_maybe_standardize_when_disabled(self, sample_api_response):
        """Test that responses are not standardized when disabled."""
        set_standardization_enabled(False)

        result = await maybe_standardize_response(sample_api_response, "list_payouts")

        # Should return original response unchanged
        assert result == sample_api_response
        assert "metadata" not in result

    async def test_maybe_standardize_when_enabled(self, sample_api_response):
        """Test that responses are standardized when enabled."""
        set_standardization_enabled(True)

        result = await maybe_standardize_response(sample_api_response, "list_payouts")

        # Should return standardized response
        assert "metadata" in result
        assert result["metadata"]["tool"] == "list_payouts"
        assert result["data"] == sample_api_response["data"]

        # Clean up
        set_standardization_enabled(False)


@pytest.mark.asyncio
class TestWrapToolCall:
    """Test the generic tool wrapper function."""

    async def test_wrap_tool_call_disabled(self, sample_api_response):
        """Test tool wrapping when standardization is disabled."""
        set_standardization_enabled(False)

        async def mock_tool(client, limit):
            return sample_api_response

        result = await wrap_tool_call("list_payouts", mock_tool, "client", 25)

        # Should return original response
        assert result == sample_api_response

    async def test_wrap_tool_call_enabled(self, sample_api_response):
        """Test tool wrapping when standardization is enabled."""
        set_standardization_enabled(True)

        async def mock_tool(client, limit):
            return sample_api_response

        result = await wrap_tool_call("list_payouts", mock_tool, "client", 25)

        # Should return standardized response
        assert "metadata" in result
        assert result["metadata"]["tool"] == "list_payouts"
        assert result["data"] == sample_api_response["data"]

        # Clean up
        set_standardization_enabled(False)

    async def test_wrap_tool_call_custom_format(self, sample_custom_response):
        """Test tool wrapping with custom format response."""
        set_standardization_enabled(True)

        async def mock_get_recent_payouts(client, limit):
            return sample_custom_response

        result = await wrap_tool_call(
            "get_recent_payouts", mock_get_recent_payouts, "client", 10
        )

        # Should standardize the custom format
        assert "metadata" in result
        assert result["metadata"]["tool"] == "get_recent_payouts"
        assert result["metadata"]["original_format"] == "custom"
        assert result["data"] == sample_custom_response["payouts"]

        # Clean up
        set_standardization_enabled(False)

    async def test_wrap_tool_call_unknown_tool(self, sample_api_response):
        """Test tool wrapping with unknown tool name."""
        set_standardization_enabled(True)

        async def mock_unknown_tool():
            return sample_api_response

        result = await wrap_tool_call("unknown_tool", mock_unknown_tool)

        # Should still attempt standardization
        assert "metadata" in result
        assert result["metadata"]["tool"] == "unknown_tool"
        assert result["metadata"]["type"] == "unknown"

        # Clean up
        set_standardization_enabled(False)


@pytest.mark.asyncio
class TestSpecificWrappers:
    """Test specific tool wrapper functions."""

    async def test_wrap_get_recent_payouts(self, sample_custom_response):
        """Test the get_recent_payouts specific wrapper."""
        from python.tools.response_wrapper import wrap_get_recent_payouts

        set_standardization_enabled(True)

        async def mock_func(client, limit):
            return sample_custom_response

        result = await wrap_get_recent_payouts(mock_func, "client", 10)

        assert result["metadata"]["tool"] == "get_recent_payouts"
        assert result["data"] == sample_custom_response["payouts"]

        # Clean up
        set_standardization_enabled(False)

    async def test_wrap_get_recent_payouts_disabled(self, sample_custom_response):
        """Test get_recent_payouts wrapper when disabled."""
        from python.tools.response_wrapper import wrap_get_recent_payouts

        set_standardization_enabled(False)

        async def mock_func(client, limit):
            return sample_custom_response

        result = await wrap_get_recent_payouts(mock_func, "client", 10)

        # Should return original custom format
        assert result == sample_custom_response
        assert "metadata" not in result
