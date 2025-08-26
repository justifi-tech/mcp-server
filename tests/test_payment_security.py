"""
Tests for simplified payment security validation
"""

import pytest

from python.tools.base import ValidationError
from python.tools.utils.payment_security import (
    PaymentSecurityError,
    is_test_card,
    validate_payment_creation,
)


class TestValidatePaymentCreation:
    """Test validate_payment_creation function."""

    def test_production_with_test_key_passes(self):
        """Test validation passes in production with test key."""
        # Should not raise any exception
        validate_payment_creation("https://api.justifi.ai", "test_client_id")

    def test_production_without_test_key_fails(self):
        """Test validation fails in production without test key."""
        with pytest.raises(
            PaymentSecurityError, match="Payment creation requires test API credentials"
        ):
            validate_payment_creation("https://api.justifi.ai", "live_client_id")

    def test_custom_environment_passes(self):
        """Test validation passes in custom environment."""
        # Should not raise any exception
        validate_payment_creation("https://custom-api.example.com", "custom_client_id")

    def test_production_with_test_card_passes(self):
        """Test validation passes with test card in production."""
        # Should not raise any exception
        validate_payment_creation(
            "https://api.justifi.ai", "test_client_id", "4242424242424242"
        )

    def test_production_with_invalid_card_fails(self):
        """Test validation fails with invalid card in production."""
        with pytest.raises(
            PaymentSecurityError, match="Only JustiFi test cards are allowed"
        ):
            validate_payment_creation(
                "https://api.justifi.ai", "test_client_id", "1234567890123456"
            )

    def test_custom_environment_with_any_card_passes(self):
        """Test validation passes with any card in custom environment."""
        # Should not raise any exception
        validate_payment_creation(
            "https://custom-api.example.com", "custom_client_id", "1234567890123456"
        )

    def test_invalid_inputs(self):
        """Test validation with invalid inputs."""
        with pytest.raises(ValidationError):
            validate_payment_creation("", "test_client_id")

        with pytest.raises(ValidationError):
            validate_payment_creation("https://api.justifi.ai", "")


class TestIsTestCard:
    """Test is_test_card function."""

    def test_valid_test_cards(self):
        """Test recognition of valid test cards."""
        test_cards = [
            "4242424242424242",  # Visa
            "5555555555554444",  # Mastercard
            "378282246310005",  # American Express
        ]

        for card in test_cards:
            assert is_test_card(card) is True

    def test_invalid_cards(self):
        """Test recognition of invalid cards."""
        invalid_cards = [
            "1234567890123456",  # Random number
            "4111111111111111",  # Valid format but not test card
            "",  # Empty string
            None,  # None value
        ]

        for card in invalid_cards:
            assert is_test_card(card) is False
