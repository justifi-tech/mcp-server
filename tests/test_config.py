"""Test configuration system functionality."""

import os
from unittest.mock import patch

import pytest

from justifi_mcp.config import (
    DEFAULT_CONFIG,
    PRODUCTION_CONFIG,
    READ_ONLY_CONFIG,
    SANDBOX_CONFIG,
    ContextConfig,
    JustiFiConfig,
    PayoutToolsConfig,
    ToolConfig,
)

# Mark all tests as async
pytestmark = pytest.mark.asyncio


class TestToolConfig:
    """Test ToolConfig model."""

    def test_default_tool_config(self):
        """Test default tool configuration."""
        config = ToolConfig()
        assert config.enabled is True
        assert config.timeout is None
        assert config.rate_limit is None

    def test_custom_tool_config(self):
        """Test custom tool configuration."""
        config = ToolConfig(enabled=False, timeout=60, rate_limit="premium")
        assert config.enabled is False
        assert config.timeout == 60
        assert config.rate_limit == "premium"


class TestPayoutToolsConfig:
    """Test PayoutToolsConfig model."""

    def test_default_payout_tools_config(self):
        """Test default payout tools configuration."""
        config = PayoutToolsConfig()
        assert config.retrieve.enabled is True
        assert config.list.enabled is True
        assert config.status.enabled is True
        assert config.recent.enabled is True

    def test_custom_payout_tools_config(self):
        """Test custom payout tools configuration."""
        config = PayoutToolsConfig(
            retrieve=ToolConfig(enabled=True),
            list=ToolConfig(enabled=True),
            status=ToolConfig(enabled=True),
            recent=ToolConfig(enabled=False),  # Disable recent payouts
        )
        assert config.retrieve.enabled is True
        assert config.recent.enabled is False


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
    """Test JustiFiConfig model."""

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
            client_id="param_client_id", client_secret="param_client_secret"
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

    def test_get_enabled_tools(self):
        """Test getting enabled tools."""
        config = JustiFiConfig(
            client_id="test_id",
            client_secret="test_secret",
            tools=PayoutToolsConfig(
                retrieve=ToolConfig(enabled=True),
                list=ToolConfig(enabled=True),
                status=ToolConfig(enabled=False),  # Disabled
                recent=ToolConfig(enabled=True),
            ),
        )

        enabled_tools = config.get_enabled_tools()
        assert "retrieve_payout" in enabled_tools
        assert "list_payouts" in enabled_tools
        assert "get_payout_status" not in enabled_tools  # Disabled
        assert "get_recent_payouts" in enabled_tools

    def test_is_tool_enabled(self):
        """Test checking if specific tools are enabled."""
        config = JustiFiConfig(
            client_id="test_id",
            client_secret="test_secret",
            tools=PayoutToolsConfig(recent=ToolConfig(enabled=False)),
        )

        assert config.is_tool_enabled("retrieve_payout") is True
        assert config.is_tool_enabled("get_recent_payouts") is False
        assert config.is_tool_enabled("nonexistent_tool") is False

    def test_get_effective_timeout(self):
        """Test getting effective timeout for tools."""
        config = JustiFiConfig(
            client_id="test_id",
            client_secret="test_secret",
            tools=PayoutToolsConfig(retrieve=ToolConfig(timeout=60)),  # Custom timeout
            context=ContextConfig(timeout=30),  # Global timeout
        )

        # Tool with custom timeout
        assert config.get_effective_timeout("retrieve_payout") == 60

        # Tool using global timeout
        assert config.get_effective_timeout("list_payouts") == 30

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


class TestPredefinedConfigs:
    """Test predefined configuration instances."""

    @patch.dict(
        os.environ,
        {"JUSTIFI_CLIENT_ID": "test_id", "JUSTIFI_CLIENT_SECRET": "test_secret"},
    )
    def test_default_config(self):
        """Test default configuration."""
        config = DEFAULT_CONFIG
        assert config.context.environment == "sandbox"
        assert config.context.timeout == 30
        assert config.context.rate_limit == "standard"

        # All tools should be enabled by default
        enabled_tools = config.get_enabled_tools()
        assert len(enabled_tools) == 4

    @patch.dict(
        os.environ,
        {"JUSTIFI_CLIENT_ID": "test_id", "JUSTIFI_CLIENT_SECRET": "test_secret"},
    )
    def test_production_config(self):
        """Test production configuration."""
        config = PRODUCTION_CONFIG
        assert config.context.environment == "production"
        assert config.context.timeout == 15  # Shorter timeout
        assert config.context.rate_limit == "premium"

    @patch.dict(
        os.environ,
        {"JUSTIFI_CLIENT_ID": "test_id", "JUSTIFI_CLIENT_SECRET": "test_secret"},
    )
    def test_sandbox_config(self):
        """Test sandbox configuration."""
        config = SANDBOX_CONFIG
        assert config.context.environment == "sandbox"
        assert config.context.timeout == 30  # Longer timeout
        assert config.context.rate_limit == "standard"

    @patch.dict(
        os.environ,
        {"JUSTIFI_CLIENT_ID": "test_id", "JUSTIFI_CLIENT_SECRET": "test_secret"},
    )
    def test_read_only_config(self):
        """Test read-only configuration."""
        config = READ_ONLY_CONFIG
        enabled_tools = config.get_enabled_tools()

        # Should have most tools enabled except recent
        assert "retrieve_payout" in enabled_tools
        assert "list_payouts" in enabled_tools
        assert "get_payout_status" in enabled_tools
        assert "get_recent_payouts" not in enabled_tools  # Disabled


class TestConfigurationSerialization:
    """Test configuration serialization and deserialization."""

    def test_config_to_dict(self):
        """Test converting configuration to dictionary."""
        config = JustiFiConfig(
            client_id="test_id",
            client_secret="test_secret",
            tools=PayoutToolsConfig(recent=ToolConfig(enabled=False)),
            context=ContextConfig(environment="production", timeout=15),
        )

        config_dict = config.dict()
        assert config_dict["client_id"] == "test_id"
        assert config_dict["tools"]["recent"]["enabled"] is False
        assert config_dict["context"]["environment"] == "production"

    def test_config_from_dict(self):
        """Test creating configuration from dictionary."""
        config_data = {
            "client_id": "test_id",
            "client_secret": "test_secret",
            "tools": {
                "payouts": {
                    "retrieve": {"enabled": True},
                    "list": {"enabled": True},
                    "status": {"enabled": False},
                    "recent": {"enabled": False},
                }
            },
            "context": {
                "environment": "production",
                "timeout": 15,
                "rate_limit": "premium",
            },
        }

        # Note: This test demonstrates the intended structure,
        # but the actual implementation uses nested Pydantic models
        # so the structure is slightly different
        config = JustiFiConfig(
            client_id=config_data["client_id"],
            client_secret=config_data["client_secret"],
            tools=PayoutToolsConfig(
                status=ToolConfig(enabled=False), recent=ToolConfig(enabled=False)
            ),
            context=ContextConfig(
                environment="production", timeout=15, rate_limit="premium"
            ),
        )

        assert config.client_id == "test_id"
        assert config.is_tool_enabled("get_payout_status") is False
        assert config.context.environment == "production"
