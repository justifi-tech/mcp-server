"""Simplified security validation for JustiFi payment operations.

This module provides consolidated security validation for payment creation
with PCI compliance and test-mode enforcement.
"""

from __future__ import annotations

import logging
from typing import Any

from ..base import ToolError, ValidationError
from .environment import detect_environment

logger = logging.getLogger(__name__)

# JustiFi test cards from official documentation
JUSTIFI_TEST_CARDS = {
    # Successful test cards
    "4242424242424242",  # Visa
    "4000056655665556",  # Visa debit
    "5555555555554444",  # Mastercard
    "2223003122003222",  # Mastercard 2-series
    "5200828282828210",  # Mastercard debit
    "5105105105105100",  # Mastercard prepaid
    "378282246310005",  # American Express
    "371449635398431",  # American Express
    "6011000990139424",  # Discover
    "3056930009020004",  # Diners Club
    "36227206271667",  # Diners Club 14-digit
    "3566002020360505",  # JCB
    "6200000000000005",  # UnionPay
    # Declined test cards (for testing error handling)
    "4000000000000101",  # CVC check fails
    "4000000000000341",  # Payment fails after tokenization
    "4000000000000002",  # Card declined
    "4000000000009995",  # Insufficient funds
    "4000000000009987",  # Lost card
    "4000000000009979",  # Stolen card
    "4000000000000069",  # Expired card
    "4000000000000127",  # Invalid CVC
    "4000000000000119",  # Gateway error
    "4242424242424241",  # Luhn check failure
}


class PaymentSecurityError(ToolError):
    """Raised when payment security validation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "PaymentSecurityError", details)
        logger.warning(f"Payment security validation failed: {message}")


def validate_payment_creation(
    base_url: str, client_id: str, card_number: str | None = None
) -> dict[str, Any]:
    """Validate that payment creation is allowed with current configuration.

    PCI compliant validation that checks:
    1. Production environment requires test API keys (client_id starts with 'test_')
    2. If card_number provided, must be JustiFi test card in production
    3. Provides detailed security context for MCP client monitoring

    Args:
        base_url: JustiFi API base URL
        client_id: JustiFi client ID
        card_number: Optional card number to validate

    Returns:
        Dictionary with validation results and environment info

    Raises:
        PaymentSecurityError: If payment creation is not allowed
        ValidationError: If inputs are invalid
    """
    # Input validation
    if not base_url or not isinstance(base_url, str):
        raise ValidationError("base_url is required", field="base_url", value=base_url)

    if not client_id or not isinstance(client_id, str):
        raise ValidationError(
            "client_id is required", field="client_id", value="[REDACTED]"
        )

    # Use proper environment detection from issue #104
    env_info = detect_environment(base_url, client_id)
    is_production = env_info["is_production"]
    is_test_key = env_info["is_test_key"]

    # Log for debugging/monitoring (MCP server logs)
    logger.debug(
        f"Payment validation: env={env_info['environment_type']}, "
        f"prod={is_production}, test_key={is_test_key}, has_card={card_number is not None}"
    )

    # Production requires test credentials for payment creation
    if is_production and not is_test_key:
        logger.warning(
            f"Payment security violation: production environment requires test credentials. "
            f"Client: {client_id[:8] if client_id else 'unknown'}..."
        )
        raise PaymentSecurityError(
            "Payment creation requires test API credentials in production. "
            "Use a client_id that starts with 'test_' for payment operations.",
            details={
                "environment_info": env_info,
                "required_action": "Use test API credentials (client_id starting with 'test_')",
            },
        )

    # Validate card number if provided
    if card_number:
        _validate_test_card(card_number, env_info)

    logger.debug(
        f"Payment validation passed for environment: {env_info['environment_type']}"
    )

    return {
        "validation_passed": True,
        "environment_info": env_info,
        "security_level": "test_mode_required"
        if is_production
        else "custom_environment",
        "warnings": []
        if env_info.get("environment_type") != "custom"
        else [
            "Custom environment detected - ensure proper security measures are in place"
        ],
    }


def _validate_test_card(card_number: str, env_info: dict) -> None:
    """Internal function to validate test card numbers with PCI compliance."""
    if not isinstance(card_number, str):
        raise ValidationError(
            "card_number must be a string", field="card_number", value="[REDACTED]"
        )

    # Clean card number
    clean_number = "".join(c for c in card_number if c.isdigit())
    if not clean_number:
        raise ValidationError(
            "card_number must contain digits", field="card_number", value="[REDACTED]"
        )

    card_preview = f"{clean_number[:4]}...{clean_number[-4:]}"

    # Log for PCI monitoring
    logger.debug(
        f"Validating card {card_preview} in {env_info['environment_type']} environment"
    )

    # Skip validation for custom/local environments unless they have production patterns
    if env_info.get("environment_type") == "custom":
        logger.debug(f"Allowing custom environment card validation for {card_preview}")
        return

    # Production environment requires test cards only (PCI compliance)
    # This applies regardless of API key type for maximum security
    if env_info["is_production"] and clean_number not in JUSTIFI_TEST_CARDS:
        logger.warning(
            f"PCI violation: Invalid test card {card_preview} attempted in production environment"
        )
        raise PaymentSecurityError(
            f"Only JustiFi test cards are allowed in production environment. "
            f"Card {card_preview} is not a recognized test card.",
            details={
                "card_preview": card_preview,
                "environment_info": env_info,
                "available_test_cards": list(JUSTIFI_TEST_CARDS)[
                    :5
                ],  # First 5 for reference
            },
        )

    logger.debug(f"Test card validation passed for {card_preview}")


def is_test_card(card_number: str) -> bool:
    """Check if a card number is a recognized JustiFi test card."""
    if not card_number or not isinstance(card_number, str):
        return False

    clean_number = "".join(c for c in card_number if c.isdigit())
    return clean_number in JUSTIFI_TEST_CARDS
