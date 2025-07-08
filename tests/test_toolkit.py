"""Test JustiFi toolkit functionality."""

from unittest.mock import patch

import pytest

from python.config import JustiFiConfig
from python.toolkit import JustiFiToolkit

# Mark all tests as async
pytestmark = pytest.mark.asyncio


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

    async def test_execute_tool_disabled(self, restricted_config):
        """Test executing a disabled tool."""
        toolkit = JustiFiToolkit(config=restricted_config)

        # Test that get_payout_status is not in enabled tools
        enabled_tools = toolkit.get_enabled_tools()
        assert "get_payout_status" not in enabled_tools

        # Test that only enabled tools are available
        assert "retrieve_payout" in enabled_tools
        assert "list_payouts" in enabled_tools

    async def test_execute_tool_validation_error(self, basic_config):
        """Test tool execution with validation error."""
        toolkit = JustiFiToolkit(config=basic_config)

        # Test that trying to execute a tool with invalid input raises an error
        with pytest.raises(Exception):  # This will raise during actual tool execution
            await toolkit.execute_langchain_tool("retrieve_payout", payout_id="")
