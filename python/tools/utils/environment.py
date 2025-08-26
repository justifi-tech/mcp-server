"""Environment detection and validation utilities for JustiFi MCP server.

This module provides utilities to detect and validate environment configurations
for custom environments, local development, proxy setups, and production environments.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def detect_environment(base_url: str, client_id: str) -> dict[str, Any]:
    """Detect environment configuration.

    Args:
        base_url: The JustiFi API base URL
        client_id: The JustiFi client ID

    Returns:
        Dictionary containing environment detection results:
        - is_production: True if using production API
        - is_test_key: True if client ID starts with 'test_'
        - environment_type: "production" or "custom"
    """
    # Environment detection
    is_production = "api.justifi.ai" in base_url.lower()
    is_test_key = client_id.startswith("test_")
    environment_type = "production" if is_production else "custom"

    result = {
        "is_production": is_production,
        "is_test_key": is_test_key,
        "environment_type": environment_type,
    }

    logger.debug(f"Environment detection result: {result}")
    return result


def validate_configuration(
    base_url: str, client_id: str, client_secret: str
) -> dict[str, Any]:
    """Validate configuration parameters and provide feedback.

    Args:
        base_url: The JustiFi API base URL
        client_id: The JustiFi client ID
        client_secret: The JustiFi client secret

    Returns:
        Dictionary containing validation results:
        - is_valid: True if configuration appears valid
        - warnings: List of configuration warnings
        - errors: List of configuration errors
        - environment_info: Environment detection results
    """
    warnings = []
    errors = []

    # Basic validation
    if not base_url:
        errors.append("Base URL is required")
    elif not base_url.startswith(("http://", "https://")):
        errors.append("Base URL must start with http:// or https://")

    if not client_id:
        errors.append("Client ID is required")
    elif len(client_id) < 10:
        warnings.append("Client ID seems unusually short")

    if not client_secret:
        errors.append("Client secret is required")
    elif len(client_secret) < 10:
        warnings.append("Client secret seems unusually short")

    # URL validation
    if base_url:
        if base_url.endswith("/"):
            warnings.append(
                "Base URL ends with trailing slash - this will be normalized"
            )
        if "/v1" in base_url:
            warnings.append("Base URL contains /v1 path - this will be normalized")

    # Environment-specific validation
    environment_info = (
        detect_environment(base_url, client_id) if base_url and client_id else {}
    )

    return {
        "is_valid": len(errors) == 0,
        "warnings": warnings,
        "errors": errors,
        "environment_info": environment_info,
    }


def get_configuration_examples() -> dict[str, dict[str, str]]:
    """Get configuration examples for different environments.

    Returns:
        Dictionary with configuration examples for each environment type.
    """
    return {
        "production": {
            "JUSTIFI_BASE_URL": "https://api.justifi.ai",
            "JUSTIFI_CLIENT_ID": "live_your_client_id_here",
            "JUSTIFI_CLIENT_SECRET": "live_your_client_secret_here",
            "description": "Production JustiFi API environment",
        },
        "custom": {
            "JUSTIFI_BASE_URL": "https://custom-api.example.com",
            "JUSTIFI_CLIENT_ID": "test_your_custom_client_id",
            "JUSTIFI_CLIENT_SECRET": "test_your_custom_client_secret",
            "description": "Custom environment (local, proxy, etc.)",
        },
    }
