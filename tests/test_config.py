"""Test configuration system functionality."""

import os
from unittest.mock import patch

import pytest

from python.config import (
    ContextConfig,
    JustiFiConfig,
)

# Only async tests are marked individually


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

    def test_auto_discovery_finds_all_tools(self):
        """Test that auto-discovery finds expected number of tools."""
        config = JustiFiConfig(client_id="test", client_secret="test")
        discovered = config._discover_available_tools()

        # Should find at least 27 tools (current count)
        assert len(discovered) >= 27

        # Should find known tools
        expected_tools = {
            "retrieve_payout",
            "list_payouts",
            "get_payout_status",
            "retrieve_payment",
            "list_payments",
            "retrieve_payment_method",
            "create_payment_method_group",
            "list_payment_method_groups",
        }
        assert expected_tools.issubset(discovered)

    def test_validation_with_auto_discovery(self):
        """Test that validation works with auto-discovered tools."""
        # Should accept all auto-discovered tools
        config = JustiFiConfig(client_id="test", client_secret="test")
        discovered = config._discover_available_tools()
        config_with_all_tools = JustiFiConfig(
            client_id="test", client_secret="test", enabled_tools=list(discovered)
        )
        assert len(config_with_all_tools.get_enabled_tools()) == len(discovered)

    def test_validation_rejects_invalid_tools(self):
        """Test that validation still rejects non-existent tools."""
        with pytest.raises(ValueError, match="Unknown tool 'nonexistent_tool'"):
            JustiFiConfig(
                client_id="test",
                client_secret="test",
                enabled_tools=["nonexistent_tool"],
            )

    def test_get_available_tools_uses_auto_discovery(self):
        """Test that get_available_tools returns auto-discovered tools."""
        config = JustiFiConfig(client_id="test", client_secret="test")
        available = config.get_available_tools()
        discovered = config._discover_available_tools()

        assert available == discovered
        assert len(available) >= 27

    def test_all_tools_enabled_with_auto_discovery(self):
        """Test that 'all' enables all auto-discovered tools."""
        config = JustiFiConfig(
            client_id="test", client_secret="test", enabled_tools="all"
        )

        enabled = config.get_enabled_tools()
        available = config.get_available_tools()

        assert enabled == available
        assert len(enabled) >= 27
