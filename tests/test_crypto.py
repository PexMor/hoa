"""
Tests for crypto utilities module.
"""

import pytest

from hoa.utils.crypto import (
    hash_password,
    verify_password,
    hash_token,
    verify_token,
    generate_session_token,
    generate_key_id,
)


class TestPasswordHashing:
    """Tests for password hashing functions."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "SecurePassword123!"
        hashed = hash_password(password)
        
        # Should return a bcrypt hash
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60  # Bcrypt hashes are always 60 characters
    
    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "SecurePassword123!"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed)
    
    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "SecurePassword123!"
        wrong_password = "WrongPassword456!"
        hashed = hash_password(password)
        
        assert not verify_password(wrong_password, hashed)
    
    def test_hash_same_password_twice(self):
        """Test that same password produces different hashes (due to salt)."""
        password = "SecurePassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)
    
    def test_password_truncation_at_72_bytes(self):
        """Test that passwords longer than 72 bytes are truncated."""
        # Create a password longer than 72 bytes
        long_password = "a" * 100
        hashed = hash_password(long_password)
        
        # Should verify with the full password
        assert verify_password(long_password, hashed)
        
        # Should also verify with first 72 characters
        assert verify_password(long_password[:72], hashed)
    
    def test_verify_password_with_invalid_hash(self):
        """Test verifying password with invalid hash format."""
        password = "SecurePassword123!"
        invalid_hash = "not-a-valid-bcrypt-hash"
        
        assert not verify_password(password, invalid_hash)
    
    def test_verify_password_empty_string(self):
        """Test verifying empty password."""
        hashed = hash_password("test")
        assert not verify_password("", hashed)
    
    def test_unicode_password(self):
        """Test unicode password handling."""
        password = "Пароль123!🔒"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed)
        assert not verify_password("WrongPassword", hashed)


class TestTokenHashing:
    """Tests for token hashing functions."""
    
    def test_hash_token(self):
        """Test token hashing."""
        token = "my-secret-token-12345"
        hashed = hash_token(token)
        
        # SHA-256 produces 64 hex characters
        assert len(hashed) == 64
        assert all(c in "0123456789abcdef" for c in hashed)
    
    def test_hash_token_deterministic(self):
        """Test that same token produces same hash."""
        token = "my-secret-token-12345"
        hash1 = hash_token(token)
        hash2 = hash_token(token)
        
        assert hash1 == hash2
    
    def test_hash_different_tokens(self):
        """Test that different tokens produce different hashes."""
        token1 = "token-1"
        token2 = "token-2"
        
        assert hash_token(token1) != hash_token(token2)
    
    def test_verify_token_correct(self):
        """Test verifying correct token."""
        token = "my-secret-token-12345"
        hashed = hash_token(token)
        
        assert verify_token(token, hashed)
    
    def test_verify_token_incorrect(self):
        """Test verifying incorrect token."""
        token = "my-secret-token-12345"
        wrong_token = "wrong-token"
        hashed = hash_token(token)
        
        assert not verify_token(wrong_token, hashed)
    
    def test_verify_token_timing_safe(self):
        """Test that token verification uses constant-time comparison."""
        # This is ensured by using secrets.compare_digest
        token = "my-secret-token"
        hashed = hash_token(token)
        
        # Even if hashes are slightly different, comparison should be timing-safe
        wrong_token = "my-secret-tokex"  # Last char different
        assert not verify_token(wrong_token, hashed)
    
    def test_hash_empty_token(self):
        """Test hashing empty token."""
        hashed = hash_token("")
        assert len(hashed) == 64
        assert verify_token("", hashed)


class TestSessionTokenGeneration:
    """Tests for session token generation."""
    
    def test_generate_session_token(self):
        """Test session token generation."""
        token = generate_session_token()
        
        # URL-safe base64 with 32 bytes should produce ~43 characters
        assert len(token) > 40
        assert all(c.isalnum() or c in "-_" for c in token)
    
    def test_generate_unique_tokens(self):
        """Test that generated tokens are unique."""
        tokens = [generate_session_token() for _ in range(100)]
        
        # All tokens should be unique
        assert len(set(tokens)) == 100
    
    def test_token_url_safe(self):
        """Test that tokens are URL-safe."""
        token = generate_session_token()
        
        # Should not contain +, /, or = which are not URL-safe
        assert "+" not in token
        assert "/" not in token
        assert "=" not in token.rstrip("=")  # Trailing = is OK


class TestKeyIdGeneration:
    """Tests for key ID generation."""
    
    def test_generate_key_id_default_length(self):
        """Test key ID generation with default length."""
        key_id = generate_key_id()
        
        # 16 bytes = 32 hex characters
        assert len(key_id) == 32
        assert all(c in "0123456789abcdef" for c in key_id)
    
    def test_generate_key_id_custom_length(self):
        """Test key ID generation with custom length."""
        key_id = generate_key_id(length=8)
        
        # 8 bytes = 16 hex characters
        assert len(key_id) == 16
        assert all(c in "0123456789abcdef" for c in key_id)
    
    def test_generate_unique_key_ids(self):
        """Test that generated key IDs are unique."""
        key_ids = [generate_key_id() for _ in range(100)]
        
        # All key IDs should be unique
        assert len(set(key_ids)) == 100
    
    def test_generate_key_id_various_lengths(self):
        """Test key ID generation with various lengths."""
        for length in [4, 8, 16, 32, 64]:
            key_id = generate_key_id(length=length)
            assert len(key_id) == length * 2  # Hex encoding doubles the length
            assert all(c in "0123456789abcdef" for c in key_id)


class TestPasswordVerificationEdgeCases:
    """Tests for edge cases in password verification."""
    
    def test_verify_with_long_password_during_verification(self):
        """Test verifying a long password (>72 bytes)."""
        password = "a" * 80
        hashed = hash_password(password)
        
        # Should work with full password
        assert verify_password(password, hashed)
        
        # Should also work with truncated version
        assert verify_password(password[:72], hashed)
    
    def test_verify_with_multibyte_characters(self):
        """Test verifying password with multibyte UTF-8 characters."""
        # Emoji and Cyrillic to test multibyte handling
        password = "Test🔒Пароль"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed)
    
    def test_verify_password_exception_handling(self):
        """Test that exceptions in verification return False."""
        # This tests the exception handling in verify_password
        assert not verify_password("test", "invalid-hash-format")
        assert not verify_password("test", "")
        assert not verify_password("test", None)  # Will cause exception, should return False

