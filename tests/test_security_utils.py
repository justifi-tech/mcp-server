"""
Tests for JustiFi Security Utilities

Test suite for security validation and enforcement utilities.
"""

import pytest

from python.tools.utils.security import (
    PaymentSecurityError,
    SecurityError,
    is_production_environment,
    is_test_key,
    log_security_event,
    validate_api_credentials,
    validate_test_mode_for_payments,
)


class TestValidateTestModeForPayments:
    """Test validate_test_mode_for_payments function."""

    def test_production_with_test_key(self):
        """Test validation in production with test key - should pass."""
        result = validate_test_mode_for_payments(
            "https://api.justifi.ai", "test_client_id"
        )
        
        assert result["validation_passed"] is True
        assert result["environment_info"]["is_production"] is True
        assert result["environment_info"]["is_test_key"] is True
        assert result["security_level"] == "test_mode_required"

    def test_production_without_test_key(self):
        """Test validation in production without test key - should fail."""
        with pytest.raises(PaymentSecurityError, match="Payment creation requires test API credentials"):
            validate_test_mode_for_payments(
                "https://api.justifi.ai", "live_client_id"
            )

    def test_custom_environment(self):
        """Test validation in custom environment - should pass with warning."""
        result = validate_test_mode_for_payments(
            "https://custom-api.example.com", "custom_client_id"
        )
        
        assert result["validation_passed"] is True
        assert result["environment_info"]["is_production"] is False
        assert result["environment_info"]["environment_type"] == "custom"
        assert result["security_level"] == "custom_environment"
        assert len(result["warnings"]) > 0

    def test_custom_environment_with_test_key(self):
        """Test validation in custom environment with test key."""
        result = validate_test_mode_for_payments(
            "https://localhost:8000", "test_client_id"
        )
        
        assert result["validation_passed"] is True
        assert result["environment_info"]["is_production"] is False
        assert result["environment_info"]["is_test_key"] is True


class TestValidateApiCredentials:
    """Test validate_api_credentials function."""

    def test_valid_credentials(self):
        """Test validation with valid credentials."""
        # Should not raise any exception
        validate_api_credentials("test_valid_client_id", "valid_client_secret_123")

    def test_empty_client_id(self):
        """Test validation with empty client_id."""
        with pytest.raises(SecurityError, match="client_id is required"):
            validate_api_credentials("", "valid_client_secret")
        
        with pytest.raises(SecurityError, match="client_id is required"):
            validate_api_credentials(None, "valid_client_secret")

    def test_empty_client_secret(self):
        """Test validation with empty client_secret."""
        with pytest.raises(SecurityError, match="client_secret is required"):
            validate_api_credentials("valid_client_id", "")
        
        with pytest.raises(SecurityError, match="client_secret is required"):
            validate_api_credentials("valid_client_id", None)

    def test_short_client_id(self):
        """Test validation with short client_id."""
        with pytest.raises(SecurityError, match="client_id appears to be too short"):
            validate_api_credentials("short", "valid_client_secret_123")

    def test_short_client_secret(self):
        """Test validation with short client_secret."""
        with pytest.raises(SecurityError, match="client_secret appears to be too short"):
            validate_api_credentials("valid_client_id_123", "short")

    def test_placeholder_client_id(self):
        """Test validation with placeholder client_id."""
        placeholders = ["test", "demo", "example"]
        
        for placeholder in placeholders:
            with pytest.raises(SecurityError, match="client_id appears to be a placeholder"):
                validate_api_credentials(placeholder, "valid_client_secret_123")

    def test_invalid_type_credentials(self):
        """Test validation with invalid credential types."""
        with pytest.raises(SecurityError, match="client_id is required"):
            validate_api_credentials(123, "valid_client_secret")
        
        with pytest.raises(SecurityError, match="client_secret is required"):
            validate_api_credentials("valid_client_id", 123)


class TestIsProductionEnvironment:
    """Test is_production_environment function."""

    def test_production_urls(self):
        """Test that production URLs are recognized."""
        production_urls = [
            "https://api.justifi.ai",
            "https://api.justifi.ai/",
            "https://api.justifi.ai/v1",
            "http://api.justifi.ai",  # Less secure but still production
        ]
        
        for url in production_urls:
            assert is_production_environment(url) is True

    def test_non_production_urls(self):
        """Test that non-production URLs are recognized."""
        non_production_urls = [
            "https://localhost:8000",
            "https://staging.example.com",
            "https://custom-api.example.com",
            "http://127.0.0.1:3000",
            "https://dev.myapp.com",
        ]
        
        for url in non_production_urls:
            assert is_production_environment(url) is False

    def test_case_insensitive(self):
        """Test that URL matching is case insensitive."""
        assert is_production_environment("https://API.JUSTIFI.AI") is True
        assert is_production_environment("https://Api.JustiFi.Ai") is True


class TestIsTestKey:
    """Test is_test_key function."""

    def test_test_keys(self):
        """Test that test keys are recognized."""
        test_keys = [
            "test_client_id",
            "test_abc123",
            "test_",
            "test_very_long_client_id_123",
        ]
        
        for key in test_keys:
            assert is_test_key(key) is True

    def test_non_test_keys(self):
        """Test that non-test keys are recognized."""
        non_test_keys = [
            "live_client_id",
            "prod_client_id",
            "client_id",
            "abc_test_def",  # test in middle, not start
            "",
            None,
        ]
        
        for key in non_test_keys:
            assert is_test_key(key) is False


class TestSecurityErrors:
    """Test security error classes."""

    def test_security_error_creation(self):
        """Test SecurityError creation."""
        error = SecurityError("Test error message")
        assert str(error) == "Test error message"
        assert error.error_type == "SecurityError"
        assert error.details == {}

    def test_security_error_with_details(self):
        """Test SecurityError with details."""
        details = {"field": "client_id", "value": "test"}
        error = SecurityError("Test error", "CustomError", details)
        
        assert error.error_type == "CustomError"
        assert error.details == details

    def test_payment_security_error(self):
        """Test PaymentSecurityError creation."""
        error = PaymentSecurityError("Payment error")
        assert str(error) == "Payment error"
        assert error.error_type == "PaymentSecurityError"

    def test_payment_security_error_with_details(self):
        """Test PaymentSecurityError with details."""
        details = {"environment": "production", "is_test_key": False}
        error = PaymentSecurityError("Payment error", details)
        
        assert error.details == details
        assert error.error_type == "PaymentSecurityError"


class TestLogSecurityEvent:
    """Test log_security_event function."""

    def test_log_security_event_basic(self):
        """Test basic security event logging."""
        # Should not raise any exception
        log_security_event("test_event", {"field": "value"})

    def test_log_security_event_with_sensitive_data(self):
        """Test logging with sensitive data redaction."""
        details = {
            "client_id": "test_very_long_client_id",
            "client_secret": "secret_value",
            "card_number": "4242424242424242",
            "cvc": "123",
            "safe_field": "safe_value",
        }
        
        # Should not raise any exception and should handle redaction
        log_security_event("payment_creation", details)

    def test_log_security_event_empty_details(self):
        """Test logging with empty details."""
        log_security_event("test_event", {})

    def test_log_security_event_none_details(self):
        """Test logging with None details."""
        # Should handle gracefully
        try:
            log_security_event("test_event", {"key": None})
        except Exception:
            pytest.fail("log_security_event should handle None values gracefully")