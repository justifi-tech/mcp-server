"""Security validation utilities for JustiFi MCP server.

This module provides security validation functions for PCI compliance
and secure payment operations.
"""

from __future__ import annotations

import logging
from typing import Any

from ..base import ToolError
from .environment import detect_environment

logger = logging.getLogger(__name__)


class SecurityError(ToolError):
    """Raised when security validation fails."""

    def __init__(
        self,
        message: str,
        error_type: str = "SecurityError",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, error_type, details)
        # Log security events for monitoring
        logger.warning(f"Security validation failed: {message}", extra={"details": details})


class PaymentSecurityError(SecurityError):
    """Raised when payment-specific security validation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "PaymentSecurityError", details)


def validate_test_mode_for_payments(base_url: str, client_id: str) -> dict[str, Any]:
    """Validate that payment creation is allowed based on environment and credentials.
    
    Payment creation requires test mode enforcement for PCI compliance:
    - Production API must use test credentials (client_id starts with 'test_')
    - Custom environments are allowed with appropriate warnings
    
    Args:
        base_url: The JustiFi API base URL
        client_id: The JustiFi client ID
        
    Returns:
        Dictionary with validation results and environment info
        
    Raises:
        PaymentSecurityError: If payment creation is not allowed
    """
    # Get environment information
    env_info = detect_environment(base_url, client_id)
    
    # Log security check
    logger.info(
        "Validating payment creation security",
        extra={
            "environment_type": env_info.get("environment_type"),
            "is_production": env_info.get("is_production"),
            "is_test_key": env_info.get("is_test_key"),
        }
    )
    
    # Production API requires test credentials for payment creation
    if env_info.get("is_production") and not env_info.get("is_test_key"):
        raise PaymentSecurityError(
            "Payment creation requires test API credentials for PCI compliance. "
            "Use a client_id that starts with 'test_' for payment creation operations.",
            details={
                "environment_type": env_info.get("environment_type"),
                "is_production": env_info.get("is_production"),
                "is_test_key": env_info.get("is_test_key"),
                "client_id_preview": f"{client_id[:8]}..." if len(client_id) > 8 else client_id,
                "base_url": base_url,
                "required_action": "Use test API credentials (client_id starting with 'test_')",
            }
        )
    
    # Custom environments get a warning but are allowed
    if env_info.get("environment_type") == "custom":
        logger.warning(
            "Payment creation in custom environment - ensure proper security measures",
            extra={
                "base_url": base_url,
                "client_id_preview": f"{client_id[:8]}..." if len(client_id) > 8 else client_id,
            }
        )
    
    return {
        "validation_passed": True,
        "environment_info": env_info,
        "security_level": "test_mode_required" if env_info.get("is_production") else "custom_environment",
        "warnings": [] if env_info.get("environment_type") != "custom" else [
            "Custom environment detected - ensure proper security measures are in place"
        ]
    }


def validate_api_credentials(client_id: str, client_secret: str) -> None:
    """Validate API credentials format and security.
    
    Args:
        client_id: The JustiFi client ID
        client_secret: The JustiFi client secret
        
    Raises:
        SecurityError: If credentials are invalid or insecure
    """
    if not client_id or not isinstance(client_id, str):
        raise SecurityError(
            "client_id is required and must be a non-empty string",
            details={"field": "client_id", "value": client_id}
        )
    
    if not client_secret or not isinstance(client_secret, str):
        raise SecurityError(
            "client_secret is required and must be a non-empty string",
            details={"field": "client_secret"}
        )
    
    # Basic format validation
    if len(client_id) < 10:
        raise SecurityError(
            "client_id appears to be too short - ensure you're using a valid JustiFi API key",
            details={"field": "client_id", "length": len(client_id)}
        )
    
    if len(client_secret) < 10:
        raise SecurityError(
            "client_secret appears to be too short - ensure you're using a valid JustiFi API secret",
            details={"field": "client_secret"}
        )
    
    # Check for obvious test patterns
    if client_id.lower() in ["test", "demo", "example"]:
        raise SecurityError(
            "client_id appears to be a placeholder - use your actual JustiFi API credentials",
            details={"field": "client_id"}
        )


def log_security_event(event_type: str, details: dict[str, Any]) -> None:
    """Log security events for monitoring and compliance.
    
    Args:
        event_type: Type of security event (e.g., 'payment_creation', 'card_validation')
        details: Details about the security event
    """
    # Remove sensitive data before logging
    safe_details = {}
    for key, value in details.items():
        if key in ["client_secret", "card_number", "cvc"]:
            safe_details[key] = "[REDACTED]"
        elif key == "client_id" and isinstance(value, str) and len(value) > 8:
            safe_details[key] = f"{value[:8]}..."
        else:
            safe_details[key] = value
    
    logger.info(
        f"Security event: {event_type}",
        extra={"event_type": event_type, "details": safe_details}
    )


def is_production_environment(base_url: str) -> bool:
    """Check if the base URL indicates a production environment.
    
    Args:
        base_url: The API base URL to check
        
    Returns:
        True if this appears to be a production environment
    """
    return "api.justifi.ai" in base_url.lower()


def is_test_key(client_id: str) -> bool:
    """Check if a client ID is a test key.
    
    Args:
        client_id: The client ID to check
        
    Returns:
        True if this appears to be a test key
    """
    return client_id.startswith("test_") if client_id else False