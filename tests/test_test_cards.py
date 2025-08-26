"""
Tests for JustiFi Test Card Validation

Test suite for test card validation utilities and security enforcement.
"""

import pytest

from python.tools.base import ValidationError
from python.tools.utils.security import SecurityError
from python.tools.utils.test_cards import (
    JUSTIFI_TEST_CARDS,
    get_test_card_info,
    is_test_card,
    validate_test_card,
)


class TestTestCardValidation:
    """Test test card validation functions."""

    def test_valid_test_cards(self):
        """Test that all defined test cards are recognized."""
        test_cards = [
            "4242424242424242",  # Visa
            "5555555555554444",  # Mastercard
            "378282246310005",   # American Express
            "6011000990139424",  # Discover
        ]
        
        for card in test_cards:
            assert is_test_card(card) is True
            assert card in JUSTIFI_TEST_CARDS

    def test_invalid_cards(self):
        """Test that invalid cards are not recognized."""
        invalid_cards = [
            "1234567890123456",  # Invalid card
            "4111111111111111",  # Valid Luhn but not JustiFi test card
            "5200000000000000",  # Different from test cards
        ]
        
        for card in invalid_cards:
            assert is_test_card(card) is False

    def test_card_number_formatting(self):
        """Test that card numbers with formatting are handled correctly."""
        # Test with spaces
        assert is_test_card("4242 4242 4242 4242") is True
        # Test with dashes
        assert is_test_card("4242-4242-4242-4242") is True
        # Test with mixed formatting
        assert is_test_card("4242 4242-4242 4242") is True

    def test_empty_or_invalid_input(self):
        """Test handling of empty or invalid input."""
        assert is_test_card("") is False
        assert is_test_card(None) is False
        assert is_test_card(123) is False
        assert is_test_card("abc") is False

    def test_validate_test_card_production_with_test_key(self):
        """Test validation in production with test key."""
        env_info = {
            "is_production": True,
            "is_test_key": True,
            "environment_type": "production"
        }
        
        # Should pass for test cards
        validate_test_card("4242424242424242", env_info)
        
        # Should fail for non-test cards
        with pytest.raises(SecurityError, match="Only JustiFi test cards are allowed"):
            validate_test_card("1234567890123456", env_info)

    def test_validate_test_card_production_without_test_key(self):
        """Test validation in production without test key."""
        env_info = {
            "is_production": True,
            "is_test_key": False,
            "environment_type": "production"
        }
        
        # Should fail for any card in production without test key
        with pytest.raises(SecurityError, match="Only JustiFi test cards are allowed"):
            validate_test_card("4242424242424242", env_info)

    def test_validate_test_card_custom_environment(self):
        """Test validation in custom environment."""
        env_info = {
            "is_production": False,
            "is_test_key": False,
            "environment_type": "custom"
        }
        
        # Should pass for any card in custom environment
        validate_test_card("4242424242424242", env_info)
        validate_test_card("1234567890123456", env_info)

    def test_validate_test_card_invalid_input(self):
        """Test validation with invalid input."""
        env_info = {"is_production": True, "is_test_key": True}
        
        with pytest.raises(ValidationError, match="card_number is required"):
            validate_test_card("", env_info)
        
        with pytest.raises(ValidationError, match="card_number is required"):
            validate_test_card(None, env_info)
        
        with pytest.raises(ValidationError, match="card_number must contain digits"):
            validate_test_card("abcd", env_info)


class TestGetTestCardInfo:
    """Test get_test_card_info function."""

    def test_get_visa_card_info(self):
        """Test getting info for Visa test card."""
        info = get_test_card_info("4242424242424242")
        assert info is not None
        assert info["card_type"] == "Visa"
        assert info["expected_result"] == "success"
        assert info["is_test_card"] is True

    def test_get_mastercard_info(self):
        """Test getting info for Mastercard test card."""
        info = get_test_card_info("5555555555554444")
        assert info is not None
        assert info["card_type"] == "Mastercard"
        assert info["expected_result"] == "success"

    def test_get_amex_info(self):
        """Test getting info for American Express test card."""
        info = get_test_card_info("378282246310005")
        assert info is not None
        assert info["card_type"] == "American Express"
        assert info["expected_result"] == "success"

    def test_get_declined_card_info(self):
        """Test getting info for declined test card."""
        info = get_test_card_info("4000000000000002")
        assert info is not None
        assert info["card_type"] == "Visa"
        assert info["expected_result"] == "decline"

    def test_get_non_test_card_info(self):
        """Test getting info for non-test card."""
        info = get_test_card_info("1234567890123456")
        assert info is None

    def test_card_number_masking(self):
        """Test that card numbers are properly masked in info."""
        info = get_test_card_info("4242424242424242")
        assert info is not None
        assert info["card_number"] == "4242...4242"
        
        # Test with American Express (15 digits)
        info = get_test_card_info("378282246310005")
        assert info is not None
        assert info["card_number"] == "3782...0005"


class TestTestCardConstants:
    """Test test card constants and data integrity."""

    def test_test_cards_set_not_empty(self):
        """Test that JUSTIFI_TEST_CARDS is not empty."""
        assert len(JUSTIFI_TEST_CARDS) > 0
        assert len(JUSTIFI_TEST_CARDS) >= 20  # Should have at least 20 test cards

    def test_test_cards_are_valid_format(self):
        """Test that all test cards have valid format."""
        for card in JUSTIFI_TEST_CARDS:
            # Should be string
            assert isinstance(card, str)
            # Should contain only digits
            assert card.isdigit()
            # Should be reasonable length (13-19 digits)
            assert 13 <= len(card) <= 19

    def test_no_duplicate_test_cards(self):
        """Test that there are no duplicate test cards."""
        cards_list = list(JUSTIFI_TEST_CARDS)
        cards_set = set(JUSTIFI_TEST_CARDS)
        assert len(cards_list) == len(cards_set)

    def test_specific_required_cards_present(self):
        """Test that specific required cards are present."""
        required_cards = [
            "4242424242424242",  # Visa success
            "4000056655665556",  # Visa debit
            "5555555555554444",  # Mastercard success
            "378282246310005",   # American Express
            "4000000000000002",  # Card declined
            "4242424242424241",  # Luhn check failure
        ]
        
        for card in required_cards:
            assert card in JUSTIFI_TEST_CARDS