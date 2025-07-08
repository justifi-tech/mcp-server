"""Test configuration system functionality."""

import os
from unittest.mock import patch

import pytest

from python.config import (
    ContextConfig,
    JustiFiConfig,
)

# Mark all tests as async
pytestmark = pytest.mark.asyncio


class TestContextConfig:
    """Test ContextConfig validation."""

    def test_invalid_environment(self):
        """Test validation of environment field."""
        with pytest.raises(ValueError, match="environment must be"):
            ContextConfig(environment="invalid")

    def test_invalid_rate_limit(self):
        """Test validation of rate_limit field."""
        with pytest.raises(ValueError, match="rate_limit must be"):
            ContextConfig(rate_limit="invalid")

    def test_timeout_bounds(self):
        """Test timeout bounds validation."""
        with pytest.raises(ValueError):
            ContextConfig(timeout=1)  # Too low

        with pytest.raises(ValueError):
            ContextConfig(timeout=500)  # Too high


class TestJustiFiConfig:
    """Test JustiFiConfig critical functionality."""

    def test_missing_credentials(self):
        """Test validation of required credentials."""
        with (
            patch.dict(os.environ, {}, clear=True),
            pytest.raises(ValueError, match="client_id must be provided"),
        ):
            JustiFiConfig()

    def test_enabled_tools_list(self):
        """Test enabled_tools with list of tool names."""
        config = JustiFiConfig(
            client_id="test_id",
            client_secret="test_secret",
            enabled_tools=["retrieve_payout", "list_payouts"],
        )

        enabled_tools = config.get_enabled_tools()
        assert enabled_tools == {"retrieve_payout", "list_payouts"}
        assert config.is_tool_enabled("retrieve_payout") is True
        assert config.is_tool_enabled("list_payouts") is True
        assert config.is_tool_enabled("get_payout_status") is False
        assert config.is_tool_enabled("get_recent_payouts") is False

    def test_enabled_tools_validation_invalid_string(self):
        """Test validation of enabled_tools with invalid string."""
        with pytest.raises(
            ValueError, match="enabled_tools string value must be 'all'"
        ):
            JustiFiConfig(
                client_id="test_id",
                client_secret="test_secret",
                enabled_tools="invalid",
            )

    def test_enabled_tools_validation_invalid_tool(self):
        """Test validation of enabled_tools with invalid tool name."""
        with pytest.raises(ValueError, match="Unknown tool 'invalid_tool'"):
            JustiFiConfig(
                client_id="test_id",
                client_secret="test_secret",
                enabled_tools=["retrieve_payout", "invalid_tool"],
            )

    def test_enabled_tools_validation_invalid_type(self):
        """Test validation of enabled_tools with invalid type."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            JustiFiConfig(
                client_id="test_id",
                client_secret="test_secret",
                enabled_tools=123,  # Invalid type
            )

        # Check that the error mentions the field and type issues
        error_str = str(exc_info.value)
        assert "enabled_tools" in error_str
        assert "Input should be a valid" in error_str

    def test_configuration_error_messages(self):
        """Test that configuration errors provide helpful messages."""
        # Test invalid tool name
        try:
            JustiFiConfig(
                client_id="test_id",
                client_secret="test_secret",
                enabled_tools=["invalid_tool"],
            )
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert "Unknown tool 'invalid_tool'" in str(e)
            assert "Valid tools:" in str(e)
            # Should list all valid tools
            assert "retrieve_payout" in str(e)
            assert "list_payouts" in str(e)
