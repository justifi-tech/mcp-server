"""Test JustiFi toolkit functionality."""

from unittest.mock import patch

import pytest

from python.config import JustiFiConfig
from python.toolkit import JustiFiToolkit
from python.tools.base import ValidationError

# Only async tests are marked individually


@pytest.fixture
def basic_config():
    """Basic test configuration with all tools enabled."""
    return JustiFiConfig(
        client_id="test_client_id",
        client_secret="test_client_secret",
        enabled_tools="all",
    )


@pytest.fixture
def restricted_config():
    """Restricted configuration with only some tools enabled."""
    return JustiFiConfig(
        client_id="test_client_id",
        client_secret="test_client_secret",
        enabled_tools=["retrieve_payout", "list_payouts"],
    )


class TestJustiFiToolkitCriticalErrors:
    """Test toolkit critical error scenarios that users will hit."""

    @patch.dict("os.environ", {}, clear=True)
    def test_toolkit_missing_credentials(self):
        """Test toolkit initialization with missing credentials."""
        with pytest.raises(ValueError):
            JustiFiToolkit()

    def test_execute_tool_disabled(self, restricted_config):
        """Test executing a disabled tool."""
        toolkit = JustiFiToolkit(config=restricted_config)

        # Test that get_payout_status is not in enabled tools
        enabled_tools = toolkit.get_enabled_tools()
        assert "get_payout_status" not in enabled_tools

        # Test that only enabled tools are available
        assert "retrieve_payout" in enabled_tools
        assert "list_payouts" in enabled_tools

    @pytest.mark.asyncio
    async def test_execute_tool_validation_error(self, basic_config):
        """Test tool execution with validation error."""
        toolkit = JustiFiToolkit(config=basic_config)

        # Test that trying to execute a tool with invalid input raises an error
        with pytest.raises(ValidationError):
            await toolkit.execute_langchain_tool("retrieve_payout", payout_id="")


class TestJustiFiToolkitAutoDiscovery:
    """Test toolkit auto-discovery functionality from Phase 2."""

    def test_get_enabled_tools_uses_auto_discovery(self):
        """Test that get_enabled_tools uses auto-discovery instead of hardcoded list."""
        # Create toolkit with specific tools enabled
        toolkit = JustiFiToolkit(
            client_id="test_client",
            client_secret="test_secret",
            enabled_tools=["retrieve_payout", "list_payments"]
        )

        enabled = toolkit.get_enabled_tools()

        # Should have exactly the requested tools
        assert len(enabled) == 2
        assert "retrieve_payout" in enabled
        assert "list_payments" in enabled

        # Tools should be callable functions
        assert callable(enabled["retrieve_payout"])
        assert callable(enabled["list_payments"])

    def test_get_enabled_tools_with_all(self):
        """Test that 'all' enables all auto-discovered tools."""
        toolkit = JustiFiToolkit(
            client_id="test_client",
            client_secret="test_secret",
            enabled_tools="all"
        )

        enabled = toolkit.get_enabled_tools()
        available = toolkit.config.get_available_tools()

        # Should enable all available tools
        assert len(enabled) == len(available)
        assert set(enabled.keys()) == available

    def test_get_configuration_summary_uses_auto_discovery(self):
        """Test that configuration summary uses auto-discovery."""
        toolkit = JustiFiToolkit(
            client_id="test_client",
            client_secret="test_secret",
            enabled_tools=["retrieve_payout"]
        )

        summary = toolkit.get_configuration_summary()

        # Should use auto-discovered available tools
        available_tools = summary["available_tools"]
        assert len(available_tools) >= 27
        assert "retrieve_payout" in available_tools
        assert "create_payment_method_group" in available_tools

    def test_tool_validation_through_config(self):
        """Test that invalid tools are caught by config validation."""
        with pytest.raises(ValueError, match="Unknown tool 'nonexistent_tool'"):
            JustiFiToolkit(
                client_id="test_client",
                client_secret="test_secret",
                enabled_tools=["nonexistent_tool"]
            )

    def test_no_hardcoded_tool_names_remain(self):
        """Test that no hardcoded _TOOL_NAMES reference exists."""
        import python.toolkit as toolkit_module

        # Should not have _TOOL_NAMES attribute after refactor
        assert not hasattr(toolkit_module, '_TOOL_NAMES')

    def test_toolkit_tool_count_matches_config(self):
        """Test that toolkit available tools matches config auto-discovery."""
        from python.config import JustiFiConfig

        config = JustiFiConfig(client_id="test", client_secret="test")
        toolkit = JustiFiToolkit(client_id="test", client_secret="test", enabled_tools="all")

        config_tools = config.get_available_tools()
        toolkit_summary = toolkit.get_configuration_summary()
        toolkit_available = set(toolkit_summary["available_tools"])

        assert config_tools == toolkit_available
