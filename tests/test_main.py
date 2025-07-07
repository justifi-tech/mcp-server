"""Test main MCP server functionality."""

from unittest.mock import patch

import pytest

from justifi_mcp.config import JustiFiConfig
from justifi_mcp.toolkit import JustiFiToolkit
from main import health_check, load_configuration

# Mark all tests as async
pytestmark = pytest.mark.asyncio


class TestMainCriticalErrors:
    """Test main.py critical error scenarios that users will hit."""

    @patch.dict("os.environ", {}, clear=True)
    def test_load_configuration_missing_credentials(self):
        """Test configuration loading fails without credentials."""
        with pytest.raises(ValueError, match="client_id must be provided"):
            load_configuration()

    async def test_health_check_authentication_failure(self):
        """Test health check failure due to bad credentials."""
        config = JustiFiConfig(client_id="invalid_id", client_secret="invalid_secret")
        toolkit = JustiFiToolkit(config=config)

        result = await health_check(toolkit)

        assert result["status"] == "unhealthy"
        assert "error" in result
