"""Test JustiFi toolkit functionality."""

from unittest.mock import patch

import pytest

from justifi_mcp.config import JustiFiConfig
from justifi_mcp.toolkit import JustiFiToolkit

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

    async def test_call_tool_disabled(self, restricted_config):
        """Test calling a disabled tool."""
        toolkit = JustiFiToolkit(config=restricted_config)
        result = await toolkit.call_tool(
            "get_payout_status", {"payout_id": "po_test123"}
        )

        assert len(result) == 1
        assert "not enabled" in result[0].text

    async def test_call_tool_validation_error(self, basic_config):
        """Test tool execution with validation error."""
        toolkit = JustiFiToolkit(config=basic_config)
        result = await toolkit.call_tool("retrieve_payout", {"payout_id": ""})

        assert len(result) == 1
        assert "ValidationError" in result[0].text
