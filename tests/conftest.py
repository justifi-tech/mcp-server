"""Shared test configuration and fixtures."""

import pytest

from justifi_mcp.config import JustiFiConfig, PayoutToolsConfig, ToolConfig

# Test credentials - these are fake credentials for testing only
TEST_CLIENT_ID = "test_client_id"
TEST_CLIENT_SECRET = "test_client_secret"  # noqa: S105


@pytest.fixture
def test_config():
    """Basic test configuration with fake credentials."""
    return JustiFiConfig(
        client_id=TEST_CLIENT_ID,
        client_secret=TEST_CLIENT_SECRET,  # noqa: S106
    )


@pytest.fixture
def restricted_test_config():
    """Restricted test configuration with some tools disabled."""
    return JustiFiConfig(
        client_id=TEST_CLIENT_ID,
        client_secret=TEST_CLIENT_SECRET,  # noqa: S106
        tools=PayoutToolsConfig(
            retrieve=ToolConfig(enabled=True),
            list=ToolConfig(enabled=True),
            status=ToolConfig(enabled=False),
            recent=ToolConfig(enabled=False),
        ),
    )
