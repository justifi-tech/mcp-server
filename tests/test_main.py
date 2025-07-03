"""Test main MCP server functionality."""

from unittest.mock import patch

import pytest
import respx
from httpx import Response

from justifi_mcp.config import JustiFiConfig
from justifi_mcp.toolkit import JustiFiToolkit
from main import health_check, load_configuration

# Mark all tests as async
pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_token_response():
    """Mock OAuth token response."""
    return {"access_token": "test_token", "expires_in": 3600}


class TestMainConfiguration:
    """Test main.py configuration loading."""

    @patch.dict("os.environ", {}, clear=True)
    def test_load_configuration_default(self):
        """Test loading default configuration."""
        with patch("os.getenv") as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                "JUSTIFI_CLIENT_ID": "test_id",
                "JUSTIFI_CLIENT_SECRET": "test_secret",
            }.get(key, default)

            config = load_configuration()
            assert isinstance(config, JustiFiConfig)
            assert config.context.environment == "sandbox"
            assert len(config.get_enabled_tools()) == 0  # No tools enabled by default

    @patch.dict(
        "os.environ",
        {"JUSTIFI_ENABLED_TOOLS": "retrieve_payout,list_payouts"},
    )
    def test_load_configuration_custom_tools(self):
        """Test loading configuration with custom tool selection."""
        with patch("os.getenv") as mock_getenv:

            def getenv_side_effect(key, default=None):
                if key == "JUSTIFI_ENABLED_TOOLS":
                    return "retrieve_payout,list_payouts"
                if key == "JUSTIFI_CLIENT_ID":
                    return "test_id"
                if key == "JUSTIFI_CLIENT_SECRET":
                    return "test_secret"
                return default

            mock_getenv.side_effect = getenv_side_effect

            config = load_configuration()
            assert config.enabled_tools == ["retrieve_payout", "list_payouts"]
            assert len(config.get_enabled_tools()) == 2

    @patch.dict("os.environ", {"JUSTIFI_ENABLED_TOOLS": "all"})
    def test_load_configuration_all_tools(self, capsys):
        """Test loading configuration with 'all' tools enabled."""
        with patch("os.getenv") as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                "JUSTIFI_ENABLED_TOOLS": "all",
                "JUSTIFI_CLIENT_ID": "test_id",
                "JUSTIFI_CLIENT_SECRET": "test_secret",
            }.get(key, default)

            config = load_configuration()

            # Should enable all tools
            assert config.enabled_tools == "all"
            assert len(config.get_enabled_tools()) == 4


class TestHealthCheck:
    """Test health check functionality."""

    @respx.mock
    async def test_health_check_success(self, mock_token_response):
        """Test successful health check."""
        # Mock OAuth token request
        respx.post("https://api.justifi.ai/v1/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )

        config = JustiFiConfig(client_id="test_id", client_secret="test_secret")
        toolkit = JustiFiToolkit(config=config)

        result = await health_check(toolkit)

        assert result["status"] == "healthy"
        assert result["token_acquired"] is True
        assert "configuration" in result
        assert result["configuration"]["environment"] == "sandbox"

    async def test_health_check_failure(self):
        """Test health check failure."""
        # Create a toolkit that will definitely fail
        config = JustiFiConfig(client_id="invalid_id", client_secret="invalid_secret")
        toolkit = JustiFiToolkit(config=config)

        # Mock the MCPAdapter's client get_access_token method to raise an exception
        import unittest.mock

        from justifi_mcp.adapters.mcp import MCPAdapter

        with unittest.mock.patch.object(
            MCPAdapter,
            "__init__",
            side_effect=Exception("Authentication failed"),
        ):
            result = await health_check(toolkit)

        assert result["status"] == "unhealthy"
        assert "error" in result
        assert "Authentication failed" in str(result["error"])


class TestMainIntegration:
    """Test main.py integration scenarios."""

    @respx.mock
    async def test_toolkit_integration(self, mock_token_response):
        """Test that main.py properly integrates with the toolkit system."""
        # Mock OAuth token request
        respx.post("https://api.justifi.ai/v1/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )

        # Create a toolkit like main.py does (with tools enabled)
        config = JustiFiConfig(
            client_id="test_id", client_secret="test_secret", enabled_tools="all"
        )
        toolkit = JustiFiToolkit(config=config)

        # Verify toolkit is properly configured
        summary = toolkit.get_configuration_summary()
        assert summary["total_tools"] == 4
        assert "retrieve_payout" in summary["enabled_tools"]

        # Verify MCP server can be created
        server = toolkit.get_mcp_server("test-server")
        assert server is not None
        assert server.name == "test-server"

    def test_configuration_driven_tool_selection(self):
        """Test that different configurations enable different tools."""
        # All tools enabled config
        all_config = JustiFiConfig(
            client_id="test_id", client_secret="test_secret", enabled_tools="all"
        )
        all_toolkit = JustiFiToolkit(config=all_config)
        all_summary = all_toolkit.get_configuration_summary()

        # Restricted config (only some tools)
        restricted_config = JustiFiConfig(
            client_id="test_id",
            client_secret="test_secret",
            enabled_tools=["retrieve_payout", "list_payouts", "get_payout_status"],
        )
        restricted_toolkit = JustiFiToolkit(config=restricted_config)
        restricted_summary = restricted_toolkit.get_configuration_summary()

        # All tools config should have all 4 tools
        assert all_summary["total_tools"] == 4

        # Restricted should have fewer tools (recent disabled)
        assert restricted_summary["total_tools"] == 3
        assert "get_recent_payouts" not in restricted_summary["enabled_tools"]

    @patch.dict(
        "os.environ",
        {
            "JUSTIFI_CLIENT_ID": "env_test_id",
            "JUSTIFI_CLIENT_SECRET": "env_test_secret",
        },
    )
    def test_environment_variable_integration(self):
        """Test that main.py properly loads environment variables."""
        config = load_configuration()
        toolkit = JustiFiToolkit(config=config)

        assert toolkit.config.client_id == "env_test_id"
        assert toolkit.config.client_secret == "env_test_secret"
