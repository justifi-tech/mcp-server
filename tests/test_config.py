"""Test configuration system functionality."""

import os
from unittest.mock import patch

import pytest

from justifi_mcp.config import (
    ContextConfig,
    JustiFiConfig,
)

# Mark all tests as async
pytestmark = pytest.mark.asyncio


class TestContextConfig:
    """Test ContextConfig model."""

    def test_default_context_config(self):
        """Test default context configuration."""
        config = ContextConfig()
        assert config.environment == "sandbox"
        assert config.account_id is None
        assert config.timeout == 30
        assert config.rate_limit == "standard"
        assert config.base_url is None

    def test_custom_context_config(self):
        """Test custom context configuration."""
        config = ContextConfig(
            environment="production",
            account_id="acct_123",
            timeout=15,
            rate_limit="premium",
            base_url="https://custom.api.justifi.ai/v1",
        )
        assert config.environment == "production"
        assert config.account_id == "acct_123"
        assert config.timeout == 15
        assert config.rate_limit == "premium"
        assert config.base_url == "https://custom.api.justifi.ai/v1"

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
    """Test JustiFiConfig model with whitelist-based tool selection."""

    @patch.dict(
        os.environ,
        {
            "JUSTIFI_CLIENT_ID": "test_client_id",
            "JUSTIFI_CLIENT_SECRET": "test_client_secret",
            "JUSTIFI_BASE_URL": "https://test.api.justifi.ai/v1",
        },
    )
    def test_config_from_environment(self):
        """Test configuration loading from environment variables."""
        config = JustiFiConfig()
        assert config.client_id == "test_client_id"
        assert config.client_secret == "test_client_secret"
        assert config.context.base_url == "https://test.api.justifi.ai/v1"

    def test_config_from_parameters(self):
        """Test configuration from direct parameters."""
        config = JustiFiConfig(
            client_id="param_client_id",
            client_secret="param_client_secret",
            enabled_tools="all",
        )
        assert config.client_id == "param_client_id"
        assert config.client_secret == "param_client_secret"

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

    def test_enabled_tools_all(self):
        """Test enabled_tools with 'all' value."""
        config = JustiFiConfig(
            client_id="test_id", client_secret="test_secret", enabled_tools="all"
        )

        enabled_tools = config.get_enabled_tools()
        expected_tools = {
            "retrieve_payout",
            "list_payouts",
            "get_payout_status",
            "get_recent_payouts",
        }
        assert enabled_tools == expected_tools

        # All tools should be enabled
        for tool in expected_tools:
            assert config.is_tool_enabled(tool) is True

    def test_enabled_tools_empty_list(self):
        """Test enabled_tools with empty list (no tools enabled)."""
        config = JustiFiConfig(
            client_id="test_id", client_secret="test_secret", enabled_tools=[]
        )

        enabled_tools = config.get_enabled_tools()
        assert enabled_tools == set()

        # No tools should be enabled
        assert config.is_tool_enabled("retrieve_payout") is False
        assert config.is_tool_enabled("list_payouts") is False
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

    def test_get_available_tools(self):
        """Test getting all available tool names."""
        config = JustiFiConfig(client_id="test_id", client_secret="test_secret")

        available_tools = config.get_available_tools()
        expected_tools = {
            "retrieve_payout",
            "list_payouts",
            "get_payout_status",
            "get_recent_payouts",
        }
        assert available_tools == expected_tools

    def test_is_tool_enabled_nonexistent(self):
        """Test checking if nonexistent tool is enabled."""
        config = JustiFiConfig(
            client_id="test_id", client_secret="test_secret", enabled_tools="all"
        )

        assert config.is_tool_enabled("nonexistent_tool") is False

    def test_get_effective_timeout(self):
        """Test getting effective timeout for tools."""
        config = JustiFiConfig(
            client_id="test_id",
            client_secret="test_secret",
            context=ContextConfig(timeout=45),
        )

        # All tools use global timeout in new system
        assert config.get_effective_timeout("retrieve_payout") == 45
        assert config.get_effective_timeout("list_payouts") == 45

    def test_get_effective_base_url(self):
        """Test getting effective base URL."""
        # With custom base URL
        config = JustiFiConfig(
            client_id="test_id",
            client_secret="test_secret",
            context=ContextConfig(base_url="https://custom.api.justifi.ai/v1"),
        )
        assert config.get_effective_base_url() == "https://custom.api.justifi.ai/v1"

        # With default base URL
        config = JustiFiConfig(client_id="test_id", client_secret="test_secret")
        assert config.get_effective_base_url() == "https://api.justifi.ai/v1"


class TestConfigurationUsability:
    """Test configuration usability and user experience."""

    def test_simple_configuration_examples(self):
        """Test that simple configuration examples work as expected."""
        # Example 1: Enable all tools
        config1 = JustiFiConfig(
            client_id="test_id", client_secret="test_secret", enabled_tools="all"
        )
        assert len(config1.get_enabled_tools()) == 4

        # Example 2: Enable only specific tools
        config2 = JustiFiConfig(
            client_id="test_id",
            client_secret="test_secret",
            enabled_tools=["retrieve_payout", "list_payouts"],
        )
        enabled = config2.get_enabled_tools()
        assert len(enabled) == 2
        assert "retrieve_payout" in enabled
        assert "list_payouts" in enabled

        # Example 3: No tools enabled (secure default)
        config3 = JustiFiConfig(
            client_id="test_id", client_secret="test_secret", enabled_tools=[]
        )
        assert len(config3.get_enabled_tools()) == 0

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
