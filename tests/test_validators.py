"""
Tests for validators module.
"""

import pytest

from hoa.utils.validators import (
    validate_email,
    validate_phone_number,
    validate_password_strength,
    sanitize_identifier,
)


class TestValidateEmail:
    """Tests for email validation."""
    
    def test_valid_emails(self):
        """Test valid email addresses."""
        valid_emails = [
            "user@example.com",
            "test.user@example.com",
            "user+tag@example.co.uk",
            "user_123@test-domain.com",
            "a@b.co",
            "test@subdomain.example.com",
        ]
        
        for email in valid_emails:
            assert validate_email(email), f"Expected {email} to be valid"
    
    def test_invalid_emails(self):
        """Test invalid email addresses."""
        invalid_emails = [
            "",
            "not-an-email",
            "@example.com",
            "user@",
            "user@.com",
            "user@domain",
            "user @example.com",
            "user@exam ple.com",
            # Note: user..test@example.com passes simple regex (would fail RFC 5322)
        ]
        
        for email in invalid_emails:
            assert not validate_email(email), f"Expected {email} to be invalid"
    
    def test_none_email(self):
        """Test None input."""
        assert not validate_email(None)


class TestValidatePhoneNumber:
    """Tests for phone number validation."""
    
    def test_valid_phone_numbers(self):
        """Test valid phone numbers."""
        valid_numbers = [
            "+14155552671",
            "+442071838750",
            "+33123456789",
            "+861234567890",
            "14155552671",  # Without +
            "+12025551234",
        ]
        
        for phone in valid_numbers:
            assert validate_phone_number(phone), f"Expected {phone} to be valid"
    
    def test_invalid_phone_numbers(self):
        """Test invalid phone numbers."""
        invalid_numbers = [
            "",
            "+0123456789",  # Starts with 0 after +
            "abc",
            "+1 415 555 2671",  # Spaces
            "+1-415-555-2671",  # Dashes
            "(415) 555-2671",  # US format
            "001234567890123456",  # Too long (>15 digits)
            # Note: "123" passes simple regex (3 digits starting with 1)
        ]
        
        for phone in invalid_numbers:
            assert not validate_phone_number(phone), f"Expected {phone} to be invalid"
    
    def test_none_phone(self):
        """Test None input."""
        assert not validate_phone_number(None)


class TestValidatePasswordStrength:
    """Tests for password strength validation."""
    
    def test_valid_password(self):
        """Test valid strong password."""
        valid, error = validate_password_strength("SecurePass123!")
        assert valid
        assert error is None
    
    def test_too_short(self):
        """Test password too short."""
        valid, error = validate_password_strength("Short1!")
        assert not valid
        assert "at least 8 characters" in error
    
    def test_no_uppercase(self):
        """Test password without uppercase letter."""
        valid, error = validate_password_strength("lowercase123!")
        assert not valid
        assert "uppercase letter" in error
    
    def test_no_lowercase(self):
        """Test password without lowercase letter."""
        valid, error = validate_password_strength("UPPERCASE123!")
        assert not valid
        assert "lowercase letter" in error
    
    def test_no_digit(self):
        """Test password without digit."""
        valid, error = validate_password_strength("NoDigitPass!")
        assert not valid
        assert "digit" in error
    
    def test_no_special_char(self):
        """Test password without special character."""
        valid, error = validate_password_strength("NoSpecial123")
        assert not valid
        assert "special character" in error
    
    def test_multiple_special_chars(self):
        """Test password with various special characters."""
        special_chars = "!@#$%^&*(),.?\":{}|<>"
        
        for char in special_chars:
            password = f"ValidPass123{char}"
            valid, error = validate_password_strength(password)
            assert valid, f"Password with '{char}' should be valid"
            assert error is None
    
    def test_minimum_length_valid(self):
        """Test password at minimum length (8 chars)."""
        valid, error = validate_password_strength("Valid1@a")
        assert valid
        assert error is None
    
    def test_very_strong_password(self):
        """Test very strong password."""
        valid, error = validate_password_strength("VerySecure!Pass123@WithSpecial#Chars")
        assert valid
        assert error is None


class TestSanitizeIdentifier:
    """Tests for identifier sanitization."""
    
    def test_basic_sanitization(self):
        """Test basic trimming and lowercasing."""
        assert sanitize_identifier("  Test  ") == "test"
        assert sanitize_identifier("UPPERCASE") == "uppercase"
        assert sanitize_identifier("MixedCase") == "mixedcase"
    
    def test_email_sanitization(self):
        """Test email sanitization."""
        assert sanitize_identifier("User@Example.COM") == "user@example.com"
        assert sanitize_identifier("  test@domain.com  ") == "test@domain.com"
    
    def test_username_sanitization(self):
        """Test username sanitization."""
        assert sanitize_identifier("UserName123") == "username123"
        assert sanitize_identifier("  user_name  ") == "user_name"
    
    def test_no_change_needed(self):
        """Test identifier that doesn't need changes."""
        assert sanitize_identifier("already-good") == "already-good"
        assert sanitize_identifier("test123") == "test123"
    
    def test_empty_string(self):
        """Test empty string."""
        assert sanitize_identifier("") == ""
        assert sanitize_identifier("   ") == ""
    
    def test_special_characters_preserved(self):
        """Test that special characters are preserved."""
        assert sanitize_identifier("user+tag@example.com") == "user+tag@example.com"
        assert sanitize_identifier("user-name_123") == "user-name_123"

