"""Shared test configuration and fixtures."""

import pytest

from justifi_mcp.config import JustiFiConfig

# Test credentials - these are fake credentials for testing only
TEST_CLIENT_ID = "test_client_id"
TEST_CLIENT_SECRET = "test_client_secret"  # noqa: S105


@pytest.fixture
def test_config():
    """Basic test configuration with all tools enabled."""
    return JustiFiConfig(
        client_id=TEST_CLIENT_ID,
        client_secret=TEST_CLIENT_SECRET,  # noqa: S106
        enabled_tools="all",
    )


@pytest.fixture
def restricted_test_config():
    """Restricted test configuration with only some tools enabled."""
    return JustiFiConfig(
        client_id=TEST_CLIENT_ID,
        client_secret=TEST_CLIENT_SECRET,  # noqa: S106
        enabled_tools=["retrieve_payout", "list_payouts"],  # Only these tools enabled
    )
