"""Test main MCP server functionality."""

from unittest.mock import patch

import pytest

from modelcontextprotocol.main import health_check
from python.config import JustiFiConfig

# Only async tests are marked individually


class TestMainCriticalErrors:
    """Test main.py critical error scenarios that users will hit."""

    @patch.dict("os.environ", {}, clear=True)
    def test_justifi_config_allows_missing_credentials(self):
        """Test configuration allows missing credentials (validated at server level).

        Credentials are optional in JustiFiConfig for HTTP mode with OAuth.
        Validation happens at server level for stdio mode.
        """
        config = JustiFiConfig()
        assert config.client_id is None
        assert config.client_secret is None

    @pytest.mark.asyncio
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
