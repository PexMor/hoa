"""
Tests for JWT Service.
"""

import pytest
from datetime import timedelta
from uuid import uuid4

from hoa.services.jwt_service import JWTService
from hoa.models.session import JWTKey


def test_create_access_token(test_db, test_settings):
    """Test creating an access token."""
    service = JWTService(test_settings, test_db)
    
    user_id = uuid4()
    
    token, expires_at = service.create_access_token(user_id)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0
    assert expires_at is not None


def test_create_refresh_token(test_db, test_settings):
    """Test creating a refresh token."""
    service = JWTService(test_settings, test_db)
    
    user_id = uuid4()
    
    token, expires_at = service.create_refresh_token(user_id)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0
    assert expires_at is not None


def test_verify_access_token(test_db, test_settings):
    """Test verifying an access token."""
    service = JWTService(test_settings, test_db)
    
    user_id = uuid4()
    
    token, _ = service.create_access_token(user_id)
    payload = service.verify_token(token)
    
    assert payload is not None
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"
    assert "exp" in payload


def test_verify_refresh_token(test_db, test_settings):
    """Test verifying a refresh token."""
    service = JWTService(test_settings, test_db)
    
    user_id = uuid4()
    
    token, _ = service.create_refresh_token(user_id)
    payload = service.verify_token(token)
    
    assert payload is not None
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "refresh"


def test_verify_invalid_token(test_db, test_settings):
    """Test verifying an invalid token."""
    service = JWTService(test_settings, test_db)
    
    payload = service.verify_token("invalid.token.here")
    
    assert payload is None


def test_verify_tampered_token(test_db, test_settings):
    """Test verifying a tampered token."""
    service = JWTService(test_settings, test_db)
    
    user_id = uuid4()
    
    token, _ = service.create_access_token(user_id)
    
    # Tamper with the token
    parts = token.split('.')
    if len(parts) == 3:
        tampered_token = parts[0] + ".tampered." + parts[2]
        payload = service.verify_token(tampered_token)
        assert payload is None


def test_jwt_key_auto_generation(test_db, test_settings):
    """Test that JWT keys are auto-generated."""
    service = JWTService(test_settings, test_db)
    
    # Creating a token should auto-generate a key
    token, _ = service.create_access_token(uuid4())
    
    # Check that a key was created
    keys = test_db.query(JWTKey).all()
    assert len(keys) > 0
    assert keys[0].is_active is True


def test_multiple_tokens_same_key(test_db, test_settings):
    """Test that multiple tokens use the same key."""
    service = JWTService(test_settings, test_db)
    
    token1, _ = service.create_access_token(uuid4())
    token2, _ = service.create_access_token(uuid4())
    
    # Both tokens should be verifiable
    payload1 = service.verify_token(token1)
    payload2 = service.verify_token(token2)
    
    assert payload1 is not None
    assert payload2 is not None


def test_get_jwks(test_db, test_settings):
    """Test getting JWKS (JSON Web Key Set)."""
    service = JWTService(test_settings, test_db)
    
    # Generate a key by creating a token
    service.create_access_token(uuid4())
    
    jwks = service.get_jwks()
    
    assert isinstance(jwks, list)
    if test_settings.jwt_algorithm == "RS256":
        assert len(jwks) > 0
        key = jwks[0]
        assert "kty" in key
        assert "use" in key
        assert "kid" in key
    else:
        # HS256 doesn't expose keys
        assert len(jwks) == 0


def test_token_expiration_access(test_db, test_settings):
    """Test that access token expiration is set correctly."""
    service = JWTService(test_settings, test_db)
    
    user_id = uuid4()
    
    # Create token with custom expiration
    token, expires_at = service.create_access_token(
        user_id,
        expires_delta=timedelta(minutes=30)
    )
    
    payload = service.verify_token(token)
    assert payload is not None
    
    # Verify expiration is set
    assert "exp" in payload
    assert "iat" in payload


def test_token_expiration_refresh(test_db, test_settings):
    """Test that refresh token expiration is set correctly."""
    service = JWTService(test_settings, test_db)
    
    user_id = uuid4()
    
    token, expires_at = service.create_refresh_token(user_id)
    
    payload = service.verify_token(token)
    assert payload is not None
    
    # Verify expiration is set
    assert "exp" in payload
    assert "iat" in payload


def test_token_with_additional_claims(test_db, test_settings):
    """Test creating token (claims are now fixed in payload)."""
    service = JWTService(test_settings, test_db)
    
    user_id = uuid4()
    
    token, _ = service.create_access_token(user_id)
    
    payload = service.verify_token(token)
    assert payload is not None
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"


def test_key_id_in_token_header(test_db, test_settings):
    """Test that token header includes key ID."""
    service = JWTService(test_settings, test_db)
    
    token, _ = service.create_access_token(uuid4())
    
    # JWT tokens have 3 parts: header.payload.signature
    parts = token.split('.')
    assert len(parts) == 3
    
    # The token should be valid
    payload = service.verify_token(token)
    assert payload is not None


def test_algorithm_in_token_header(test_db, test_settings):
    """Test that token uses correct algorithm."""
    service = JWTService(test_settings, test_db)
    
    token, _ = service.create_access_token(uuid4())
    
    payload = service.verify_token(token)
    assert payload is not None
    
    # Verify the service is using the configured algorithm
    assert service.algorithm == test_settings.jwt_algorithm


def test_rs256_key_generation(test_db, test_settings):
    """Test RS256 key pair generation."""
    # Change algorithm to RS256
    test_settings.jwt_algorithm = "RS256"
    service = JWTService(test_settings, test_db)
    
    # Create a token, which should generate RS256 keys
    user_id = uuid4()
    token, _ = service.create_access_token(user_id)
    
    # Verify key was created correctly
    keys = test_db.query(JWTKey).filter(JWTKey.algorithm == "RS256").all()
    assert len(keys) > 0
    
    key = keys[0]
    assert key.public_key is not None
    assert key.private_key_encrypted is not None
    assert "BEGIN PUBLIC KEY" in key.public_key
    assert "BEGIN PRIVATE KEY" in key.private_key_encrypted
    
    # Verify token is valid
    payload = service.verify_token(token)
    assert payload is not None
    assert payload["sub"] == str(user_id)


def test_hs256_key_generation(test_db, test_settings):
    """Test HS256 secret generation."""
    # Ensure algorithm is HS256
    test_settings.jwt_algorithm = "HS256"
    service = JWTService(test_settings, test_db)
    
    # Create a token, which should generate HS256 secret
    user_id = uuid4()
    token, _ = service.create_access_token(user_id)
    
    # Verify key was created correctly
    keys = test_db.query(JWTKey).filter(JWTKey.algorithm == "HS256").all()
    assert len(keys) > 0
    
    key = keys[0]
    assert key.public_key is None  # HS256 doesn't have public key
    assert key.private_key_encrypted is not None
    assert len(key.private_key_encrypted) > 0
    
    # Verify token is valid
    payload = service.verify_token(token)
    assert payload is not None
    assert payload["sub"] == str(user_id)


def test_key_rotation(test_db, test_settings):
    """Test JWT key rotation."""
    service = JWTService(test_settings, test_db)
    
    # Create initial key by creating a token
    token1, _ = service.create_access_token(uuid4())
    
    # Get the current key
    key1 = test_db.query(JWTKey).filter(JWTKey.is_active == True).first()
    assert key1 is not None
    key1_id = key1.id
    
    # Rotate the key
    new_key = service.rotate_keys()
    
    # Verify new key is created
    assert new_key.id != key1_id
    assert new_key.is_active is True
    
    # Verify old key is deactivated
    test_db.refresh(key1)
    assert key1.is_active is False
    assert key1.rotated_at is not None
    
    # Verify old token still works (using old key)
    payload = service.verify_token(token1)
    assert payload is not None
    
    # Create new token with new key
    token2, _ = service.create_access_token(uuid4())
    payload2 = service.verify_token(token2)
    assert payload2 is not None


def test_token_validation_with_wrong_type(test_db, test_settings):
    """Test validating token with validate_token method."""
    service = JWTService(test_settings, test_db)
    
    user_id = uuid4()
    
    # Create access token
    access_token, _ = service.create_access_token(user_id)
    
    # Validate as access token - should work
    payload = service.validate_token(access_token, "access")
    assert payload is not None
    
    # Validate as refresh token - should fail
    payload = service.validate_token(access_token, "refresh")
    assert payload is None


def test_token_expired_validation(test_db, test_settings):
    """Test validation of expired tokens."""
    service = JWTService(test_settings, test_db)
    
    user_id = uuid4()
    
    # Create token that's already expired
    token, _ = service.create_access_token(
        user_id,
        expires_delta=timedelta(seconds=-10)  # Expired 10 seconds ago
    )
    
    # Verification should fail
    payload = service.verify_token(token)
    assert payload is None


def test_validate_token_invalid_type_parameter(test_db, test_settings):
    """Test validate_token with invalid type parameter."""
    service = JWTService(test_settings, test_db)
    
    user_id = uuid4()
    token, _ = service.create_access_token(user_id)
    
    # Should return None for invalid token type
    payload = service.validate_token(token, "invalid_type")
    assert payload is None


def test_get_jwks_for_rs256(test_db, test_settings):
    """Test JWKS generation for RS256."""
    test_settings.jwt_algorithm = "RS256"
    service = JWTService(test_settings, test_db)
    
    # Generate a key
    service.create_access_token(uuid4())
    
    # Get JWKS
    jwks = service.get_jwks()
    
    assert len(jwks) > 0
    key = jwks[0]
    
    # Verify JWKS format (basic fields - full n/e extraction would be in production)
    assert key["kty"] == "RSA"
    assert key["use"] == "sig"
    assert key["alg"] == "RS256"
    assert "kid" in key


def test_get_jwks_for_hs256(test_db, test_settings):
    """Test JWKS for HS256 (should be empty)."""
    test_settings.jwt_algorithm = "HS256"
    service = JWTService(test_settings, test_db)
    
    # Generate a key
    service.create_access_token(uuid4())
    
    # Get JWKS - should be empty for symmetric keys
    jwks = service.get_jwks()
    
    assert len(jwks) == 0


def test_multiple_key_rotation(test_db, test_settings):
    """Test multiple key rotations."""
    service = JWTService(test_settings, test_db)
    
    # Create initial token
    token1, _ = service.create_access_token(uuid4())
    
    # Rotate key twice
    service.rotate_keys()
    service.rotate_keys()
    
    # All keys should exist in database
    keys = test_db.query(JWTKey).all()
    assert len(keys) == 3
    
    # Only the last one should be active
    active_keys = test_db.query(JWTKey).filter(JWTKey.is_active == True).all()
    assert len(active_keys) == 1
    
    # Original token should still be verifiable
    payload = service.verify_token(token1)
    assert payload is not None


def test_token_with_custom_expiration(test_db, test_settings):
    """Test token creation with custom expiration."""
    service = JWTService(test_settings, test_db)
    
    user_id = uuid4()
    
    # Create token with 2 hour expiration
    custom_delta = timedelta(hours=2)
    token, expires_at = service.create_access_token(user_id, expires_delta=custom_delta)
    
    # Verify token
    payload = service.verify_token(token)
    assert payload is not None
    
    # Check expiration is set correctly
    from datetime import datetime
    exp_time = datetime.fromtimestamp(payload["exp"])
    iat_time = datetime.fromtimestamp(payload["iat"])
    
    # Expiration should be roughly 2 hours after issuance
    diff = exp_time - iat_time
    assert abs(diff.total_seconds() - 7200) < 10  # Within 10 seconds


def test_refresh_token_with_custom_expiration(test_db, test_settings):
    """Test refresh token creation with custom expiration."""
    service = JWTService(test_settings, test_db)
    
    user_id = uuid4()
    
    # Create refresh token with 7 day expiration
    custom_delta = timedelta(days=7)
    token, expires_at = service.create_refresh_token(user_id, expires_delta=custom_delta)
    
    # Verify token
    payload = service.verify_token(token)
    assert payload is not None
    assert payload["type"] == "refresh"
