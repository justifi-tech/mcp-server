"""Test main MCP server functionality."""

from unittest.mock import patch

import pytest

from modelcontextprotocol.main import health_check
from python.config import JustiFiConfig

# Mark all tests as async
pytestmark = pytest.mark.asyncio


class TestMainCriticalErrors:
    """Test main.py critical error scenarios that users will hit."""

    @patch.dict("os.environ", {}, clear=True)
    def test_justifi_config_missing_credentials(self):
        """Test configuration loading fails without credentials."""
        with pytest.raises(ValueError, match="client_id must be provided"):
            JustiFiConfig()

    async def test_health_check_authentication_failure(self):
        """Test health check failure due to bad credentials."""
        # Mock environment variables with invalid credentials
        with patch.dict(
            "os.environ",
            {
                "JUSTIFI_CLIENT_ID": "invalid_id",
                "JUSTIFI_CLIENT_SECRET": "invalid_secret",
            },
        ):
            result = await health_check()

            assert result["status"] == "unhealthy"
            assert "error" in result
