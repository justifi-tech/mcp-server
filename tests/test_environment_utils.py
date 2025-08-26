"""Tests for environment detection utilities."""

from python.tools.utils.environment import detect_environment


def test_environment_detection():
    """Test basic environment detection."""
    # Production
    result = detect_environment("https://api.justifi.ai", "live_client_id")
    assert result["environment_type"] == "production"
    assert result["is_production"]

    # Custom
    result = detect_environment("https://custom-api.example.com", "test_client_id")
    assert result["environment_type"] == "custom"
    assert not result["is_production"]
