"""Test card validation utilities for JustiFi MCP server.

This module provides utilities to validate JustiFi test cards for PCI compliance
and secure payment creation operations.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


# JustiFi test cards from official documentation
JUSTIFI_TEST_CARDS = {
    # Successful test cards
    '4242424242424242',  # Visa
    '4000056655665556',  # Visa debit
    '5555555555554444',  # Mastercard
    '2223003122003222',  # Mastercard 2-series
    '5200828282828210',  # Mastercard debit
    '5105105105105100',  # Mastercard prepaid
    '378282246310005',   # American Express
    '371449635398431',   # American Express
    '6011000990139424',  # Discover
    '3056930009020004',  # Diners Club
    '36227206271667',    # Diners Club 14-digit
    '3566002020360505',  # JCB
    '6200000000000005',  # UnionPay
    
    # Declined test cards (for testing error handling)
    '4000000000000101',  # CVC check fails
    '4000000000000341',  # Payment fails after tokenization
    '4000000000000002',  # Card declined
    '4000000000009995',  # Insufficient funds
    '4000000000009987',  # Lost card
    '4000000000009979',  # Stolen card
    '4000000000000069',  # Expired card
    '4000000000000127',  # Invalid CVC
    '4000000000000119',  # Gateway error
    '4242424242424241',  # Luhn check failure
}

# Successful ACH test accounts
JUSTIFI_TEST_ACH = {
    '110000000': ['000123456789'],  # Valid account
}


def validate_test_card(card_number: str, env_info: dict[str, Any]) -> None:
    """Validate card based on environment configuration.
    
    Args:
        card_number: The card number to validate
        env_info: Environment information from detect_environment()
        
    Raises:
        SecurityError: If card is not a valid test card in production environment
        ValidationError: If card number format is invalid
    """
    from .security import SecurityError
    from ..base import ValidationError
    
    if not card_number or not isinstance(card_number, str):
        raise ValidationError(
            "card_number is required and must be a string",
            field="card_number",
            value=card_number
        )
    
    # Clean the card number (remove spaces, dashes, etc.)
    clean_number = ''.join(c for c in card_number if c.isdigit())
    
    if not clean_number:
        raise ValidationError(
            "card_number must contain digits",
            field="card_number", 
            value=card_number
        )
    
    # Skip validation for custom/local environments unless they have production patterns
    if env_info.get('environment_type') == 'custom':
        logger.debug(f"Allowing custom environment card validation for {clean_number[:4]}...")
        return
    
    # Production environment requires test cards only
    if env_info.get('is_production') and not env_info.get('is_test_key'):
        if clean_number not in JUSTIFI_TEST_CARDS:
            raise SecurityError(
                f"Only JustiFi test cards are allowed with production API. "
                f"Card {clean_number[:4]}... is not a recognized test card.",
                error_type="InvalidTestCard",
                details={
                    "card_preview": f"{clean_number[:4]}...{clean_number[-4:]}",
                    "environment": env_info.get('environment_type'),
                    "is_production": env_info.get('is_production'),
                    "is_test_key": env_info.get('is_test_key')
                }
            )
    
    logger.debug(f"Test card validation passed for {clean_number[:4]}...")


def is_test_card(card_number: str) -> bool:
    """Check if a card number is a recognized JustiFi test card.
    
    Args:
        card_number: The card number to check
        
    Returns:
        True if the card is a recognized test card, False otherwise
    """
    if not card_number or not isinstance(card_number, str):
        return False
        
    clean_number = ''.join(c for c in card_number if c.isdigit())
    return clean_number in JUSTIFI_TEST_CARDS


def get_test_card_info(card_number: str) -> dict[str, Any] | None:
    """Get information about a test card if it's recognized.
    
    Args:
        card_number: The card number to look up
        
    Returns:
        Dictionary with card information or None if not a test card
    """
    if not is_test_card(card_number):
        return None
        
    clean_number = ''.join(c for c in card_number if c.isdigit())
    
    # Basic card type detection
    card_type = "Unknown"
    if clean_number.startswith('4'):
        card_type = "Visa"
    elif clean_number.startswith(('51', '52', '53', '54', '55', '2223')):
        card_type = "Mastercard"
    elif clean_number.startswith(('34', '37')):
        card_type = "American Express"
    elif clean_number.startswith('6011'):
        card_type = "Discover"
    elif clean_number.startswith(('30', '36')):
        card_type = "Diners Club"
    elif clean_number.startswith('35'):
        card_type = "JCB"
    elif clean_number.startswith('62'):
        card_type = "UnionPay"
    
    # Determine if this is a success or failure test case
    success_cards = {
        '4242424242424242', '4000056655665556', '5555555555554444',
        '2223003122003222', '5200828282828210', '5105105105105100',
        '378282246310005', '371449635398431', '6011000990139424',
        '3056930009020004', '36227206271667', '3566002020360505',
        '6200000000000005'
    }
    
    expected_result = "success" if clean_number in success_cards else "decline"
    
    return {
        "card_number": f"{clean_number[:4]}...{clean_number[-4:]}",
        "card_type": card_type,
        "expected_result": expected_result,
        "is_test_card": True
    }