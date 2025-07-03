"""Test main MCP server functionality."""

from unittest.mock import patch

import pytest
import respx
from httpx import Response

from justifi_mcp.config import PRODUCTION_CONFIG, READ_ONLY_CONFIG, JustiFiConfig
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

    @patch.dict("os.environ", {"JUSTIFI_CONFIG_MODE": "production"})
    def test_load_configuration_production_mode(self):
        """Test loading production configuration mode."""
        config = load_configuration()
        assert config == PRODUCTION_CONFIG
        assert config.context.environment == "production"

    @patch.dict("os.environ", {"JUSTIFI_CONFIG_MODE": "readonly"})
    def test_load_configuration_readonly_mode(self):
        """Test loading readonly configuration mode."""
        config = load_configuration()
        assert config == READ_ONLY_CONFIG
        assert not config.is_tool_enabled("get_recent_payouts")

    @patch.dict(
        "os.environ",
        {"JUSTIFI_CONFIG": '{"context": {"environment": "production", "timeout": 20}}'},
    )
    def test_load_configuration_json(self):
        """Test loading configuration from JSON environment variable."""
        with patch("os.getenv") as mock_getenv:

            def getenv_side_effect(key, default=None):
                if key == "JUSTIFI_CONFIG":
                    return '{"context": {"environment": "production", "timeout": 20}}'
                if key == "JUSTIFI_CLIENT_ID":
                    return "test_id"
                if key == "JUSTIFI_CLIENT_SECRET":
                    return "test_secret"
                return default

            mock_getenv.side_effect = getenv_side_effect

            config = load_configuration()
            assert config.context.environment == "production"
            assert config.context.timeout == 20

    @patch.dict("os.environ", {"JUSTIFI_CONFIG": "invalid json"})
    def test_load_configuration_invalid_json(self, capsys):
        """Test loading configuration with invalid JSON."""
        with patch("os.getenv") as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                "JUSTIFI_CONFIG": "invalid json",
                "JUSTIFI_CLIENT_ID": "test_id",
                "JUSTIFI_CLIENT_SECRET": "test_secret",
            }.get(key, default)

            config = load_configuration()

            # Should fall back to default config
            assert config.context.environment == "sandbox"

            # Should print warning to stderr
            captured = capsys.readouterr()
            assert "Warning: Invalid JUSTIFI_CONFIG JSON" in captured.err


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

        # Mock the get_access_token method to raise an exception
        import unittest.mock

        with unittest.mock.patch.object(
            toolkit.client,
            "get_access_token",
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

        # Create a toolkit like main.py does
        config = JustiFiConfig(client_id="test_id", client_secret="test_secret")
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
        # Production config (restricted)
        prod_config = PRODUCTION_CONFIG
        prod_toolkit = JustiFiToolkit(config=prod_config)
        prod_summary = prod_toolkit.get_configuration_summary()

        # Read-only config (more restricted)
        readonly_config = READ_ONLY_CONFIG
        readonly_toolkit = JustiFiToolkit(config=readonly_config)
        readonly_summary = readonly_toolkit.get_configuration_summary()

        # Production should have all 4 tools
        assert prod_summary["total_tools"] == 4

        # Read-only should have fewer tools (recent disabled)
        assert readonly_summary["total_tools"] == 3
        assert "get_recent_payouts" not in readonly_summary["enabled_tools"]

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
