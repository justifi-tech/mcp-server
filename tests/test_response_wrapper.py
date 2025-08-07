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
    """Test standardization configuration functions (legacy compatibility)."""

    def test_default_standardization_enabled(self):
        """Test that standardization is always enabled by default."""
        assert is_standardization_enabled() is True

    def test_enable_standardization_no_effect(self):
        """Test that enabling standardization has no effect (legacy compatibility)."""
        set_standardization_enabled(True)
        assert is_standardization_enabled() is True

    def test_disable_standardization_no_effect(self):
        """Test that disabling standardization has no effect (legacy compatibility)."""
        set_standardization_enabled(False)
        assert is_standardization_enabled() is True  # Always enabled


@pytest.mark.asyncio
class TestMaybeStandardizeResponse:
    """Test response standardization (always applied)."""

    async def test_maybe_standardize_always_enabled(self, sample_api_response):
        """Test that responses are always standardized."""
        result = await maybe_standardize_response(sample_api_response, "list_payouts")

        # Should return standardized response
        assert "metadata" in result
        assert result["metadata"]["tool"] == "list_payouts"
        assert result["data"] == sample_api_response["data"]

    async def test_maybe_standardize_legacy_behavior(self, sample_api_response):
        """Test that legacy configuration calls don't affect behavior."""
        # Even if we try to disable, standardization should still occur
        set_standardization_enabled(False)
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

    async def test_wrap_tool_call_always_enabled(self, sample_api_response):
        """Test tool wrapping always standardizes responses."""
        async def mock_tool(client, limit):
            return sample_api_response

        result = await wrap_tool_call("list_payouts", mock_tool, "client", 25)

        # Should return standardized response
        assert "metadata" in result
        assert result["metadata"]["tool"] == "list_payouts"
        assert result["data"] == sample_api_response["data"]

    async def test_wrap_tool_call_legacy_config_ignored(self, sample_api_response):
        """Test tool wrapping ignores legacy configuration attempts."""
        # Try to disable standardization (should have no effect)
        set_standardization_enabled(False)

        async def mock_tool(client, limit):
            return sample_api_response

        result = await wrap_tool_call("list_payouts", mock_tool, "client", 25)

        # Should still return standardized response
        assert "metadata" in result
        assert result["metadata"]["tool"] == "list_payouts"
        assert result["data"] == sample_api_response["data"]

    async def test_wrap_tool_call_custom_format(self, sample_custom_response):
        """Test tool wrapping with custom format response."""
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

    async def test_wrap_tool_call_unknown_tool(self, sample_api_response):
        """Test tool wrapping with unknown tool name."""

        async def mock_unknown_tool():
            return sample_api_response

        result = await wrap_tool_call("unknown_tool", mock_unknown_tool)

        # Should still attempt standardization
        assert "metadata" in result
        assert result["metadata"]["tool"] == "unknown_tool"
        assert result["metadata"]["type"] == "unknown"


@pytest.mark.asyncio
class TestSpecificWrappers:
    """Test specific tool wrapper functions."""

    async def test_wrap_get_recent_payouts(self, sample_custom_response):
        """Test the get_recent_payouts specific wrapper."""
        from python.tools.response_wrapper import wrap_get_recent_payouts

        async def mock_func(client, limit):
            return sample_custom_response

        result = await wrap_get_recent_payouts(mock_func, "client", 10)

        assert result["metadata"]["tool"] == "get_recent_payouts"
        assert result["data"] == sample_custom_response["payouts"]

    async def test_wrap_get_recent_payouts_legacy_config_ignored(self, sample_custom_response):
        """Test get_recent_payouts wrapper ignores legacy configuration."""
        from python.tools.response_wrapper import wrap_get_recent_payouts

        # Try to disable (should have no effect)
        set_standardization_enabled(False)

        async def mock_func(client, limit):
            return sample_custom_response

        result = await wrap_get_recent_payouts(mock_func, "client", 10)

        # Should still return standardized format (ignoring the disable attempt)
        assert result["metadata"]["tool"] == "get_recent_payouts"
        assert result["data"] == sample_custom_response["payouts"]
