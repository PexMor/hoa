"""
Tests for Auth Methods Service.
"""

import pytest
from uuid import uuid4

from hoa.models.auth_method import AuthMethod
from hoa.services.auth_methods import AuthMethodService
from hoa.utils.crypto import hash_password


def test_add_passkey_auth(test_db, test_settings, test_user):
    """Test adding a passkey authentication method."""
    service = AuthMethodService(test_db, test_settings)
    
    auth_method = service.add_passkey(
        user_id=test_user.id,
        credential_id="test_credential_123",
        public_key="test_public_key",
        rp_id="localhost",
        sign_count=0,
        transports=["usb", "nfc"]
    )
    
    assert auth_method is not None
    assert auth_method.type == "passkey"
    assert auth_method.user_id == test_user.id
    assert auth_method.credential_id == "test_credential_123"
    assert auth_method.public_key == "test_public_key"
    assert auth_method.rp_id == "localhost"
    assert auth_method.sign_count == 0
    assert auth_method.transports == "usb,nfc"
    assert auth_method.enabled is True


def test_add_password_auth(test_db, test_settings, test_user):
    """Test adding a password authentication method."""
    service = AuthMethodService(test_db, test_settings)
    
    auth_method = service.add_password(
        user_id=test_user.id,
        password="SecurePassword123!",
        identifier=test_user.email
    )
    
    assert auth_method is not None
    assert auth_method.type == "password"
    assert auth_method.user_id == test_user.id
    assert auth_method.identifier == test_user.email
    assert auth_method.password_hash is not None
    assert auth_method.password_hash != "SecurePassword123!"
    assert auth_method.enabled is True


def test_add_oauth2_auth(test_db, test_settings, test_user):
    """Test adding an OAuth2 authentication method."""
    service = AuthMethodService(test_db, test_settings)
    
    auth_method = service.add_oauth2(
        user_id=test_user.id,
        provider="google",
        provider_user_id="google_user_123",
        identifier="user@gmail.com",
        access_token="access_token_123",
        refresh_token="refresh_token_456"
    )
    
    assert auth_method is not None
    assert auth_method.type == "oauth2"
    assert auth_method.user_id == test_user.id
    assert auth_method.provider == "google"
    assert auth_method.provider_user_id == "google_user_123"
    assert auth_method.identifier == "user@gmail.com"
    assert auth_method.enabled is True


def test_add_m2m_token_auth(test_db, test_settings, test_user):
    """Test adding an M2M token authentication method."""
    service = AuthMethodService(test_db, test_settings)
    
    auth_method = service.add_m2m_token(
        user_id=test_user.id,
        token="test_token_123",
        description="API token for testing"
    )
    
    assert auth_method is not None
    assert auth_method.type == "token"
    assert auth_method.user_id == test_user.id
    assert auth_method.description == "API token for testing"
    assert auth_method.token_hash is not None
    assert auth_method.token_hash != "test_token_123"
    assert auth_method.enabled is True


def test_get_by_id(test_db, test_settings, test_user):
    """Test getting auth method by ID."""
    service = AuthMethodService(test_db, test_settings)
    
    # Create an auth method
    created = service.add_password(
        user_id=test_user.id,
        password="password123",
        identifier=test_user.email
    )
    
    # Get it by ID
    retrieved = service.get_by_id(created.id)
    
    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.type == "password"


def test_get_by_id_not_found(test_db, test_settings):
    """Test getting non-existent auth method."""
    service = AuthMethodService(test_db, test_settings)
    
    result = service.get_by_id(uuid4())
    
    assert result is None


def test_get_by_credential_id(test_db, test_settings, test_user):
    """Test getting passkey by credential ID."""
    service = AuthMethodService(test_db, test_settings)
    
    # Create a passkey
    service.add_passkey(
        user_id=test_user.id,
        credential_id="unique_credential_123",
        public_key="public_key",
        rp_id="localhost"
    )
    
    # Get it by credential ID
    retrieved = service.get_by_credential_id("unique_credential_123")
    
    assert retrieved is not None
    assert retrieved.credential_id == "unique_credential_123"
    assert retrieved.type == "passkey"


def test_get_user_auth_methods(test_db, test_settings, test_user):
    """Test getting all auth methods for a user."""
    service = AuthMethodService(test_db, test_settings)
    
    # Add multiple auth methods
    service.add_passkey(
        user_id=test_user.id,
        credential_id="cred1",
        public_key="key1",
        rp_id="localhost"
    )
    service.add_password(
        user_id=test_user.id,
        password="pass123",
        identifier=test_user.email
    )
    service.add_oauth2(
        user_id=test_user.id,
        provider="google",
        provider_user_id="google123",
        identifier="test@gmail.com"
    )
    
    # Get all auth methods
    methods = service.get_user_auth_methods(test_user.id)
    
    assert len(methods) == 3
    types = {m.type for m in methods}
    assert types == {"passkey", "password", "oauth2"}


def test_get_user_auth_methods_enabled_only(test_db, test_settings, test_user):
    """Test getting only enabled auth methods."""
    service = AuthMethodService(test_db, test_settings)
    
    # Add auth methods
    enabled = service.add_passkey(
        user_id=test_user.id,
        credential_id="enabled_cred",
        public_key="key",
        rp_id="localhost"
    )
    disabled = service.add_password(
        user_id=test_user.id,
        password="pass",
        identifier=test_user.email
    )
    
    # Disable one
    service.disable(disabled.id)
    
    # Get enabled only
    methods = service.get_user_auth_methods(test_user.id, enabled_only=True)
    
    assert len(methods) == 1
    assert methods[0].id == enabled.id


def test_get_user_passkeys(test_db, test_settings, test_user):
    """Test getting user's passkeys only."""
    service = AuthMethodService(test_db, test_settings)
    
    # Add various auth methods
    service.add_passkey(
        user_id=test_user.id,
        credential_id="cred1",
        public_key="key1",
        rp_id="localhost"
    )
    service.add_passkey(
        user_id=test_user.id,
        credential_id="cred2",
        public_key="key2",
        rp_id="localhost"
    )
    service.add_password(
        user_id=test_user.id,
        password="pass",
        identifier=test_user.email
    )
    
    # Get only passkeys
    passkeys = service.get_user_passkeys(test_user.id)
    
    assert len(passkeys) == 2
    assert all(p.type == "passkey" for p in passkeys)


def test_verify_password(test_db, test_settings, test_user):
    """Test verifying password."""
    service = AuthMethodService(test_db, test_settings)
    
    password = "SecurePassword123!"
    auth_method = service.add_password(
        user_id=test_user.id,
        password=password,
        identifier=test_user.email
    )
    
    # Correct password
    assert service.verify_password(auth_method.id, password) is True
    
    # Wrong password
    assert service.verify_password(auth_method.id, "WrongPassword") is False


def test_verify_m2m_token(test_db, test_settings, test_user):
    """Test verifying M2M token."""
    service = AuthMethodService(test_db, test_settings)
    
    token = "test_token_secret"
    auth_method = service.add_m2m_token(
        user_id=test_user.id,
        token=token,
        description="Test token"
    )
    
    # Correct token
    assert service.verify_m2m_token(auth_method.id, token) is True
    
    # Wrong token
    assert service.verify_m2m_token(auth_method.id, "wrong_token") is False


def test_update_sign_count(test_db, test_settings, test_user):
    """Test updating passkey sign count."""
    service = AuthMethodService(test_db, test_settings)
    
    passkey = service.add_passkey(
        user_id=test_user.id,
        credential_id="cred",
        public_key="key",
        rp_id="localhost",
        sign_count=0
    )
    
    # Update sign count
    updated = service.update_sign_count(passkey.id, 5)
    
    assert updated is not None
    assert updated.sign_count == 5


def test_enable_auth_method(test_db, test_settings, test_user):
    """Test enabling an auth method."""
    service = AuthMethodService(test_db, test_settings)
    
    auth_method = service.add_password(
        user_id=test_user.id,
        password="pass",
        identifier=test_user.email
    )
    
    # Disable it first
    service.disable(auth_method.id)
    assert service.get_by_id(auth_method.id).enabled is False
    
    # Enable it
    enabled = service.enable(auth_method.id)
    
    assert enabled is not None
    assert enabled.enabled is True


def test_disable_auth_method(test_db, test_settings, test_user):
    """Test disabling an auth method."""
    service = AuthMethodService(test_db, test_settings)
    
    auth_method = service.add_password(
        user_id=test_user.id,
        password="pass",
        identifier=test_user.email
    )
    
    # Disable it
    disabled = service.disable(auth_method.id)
    
    assert disabled is not None
    assert disabled.enabled is False


def test_delete_auth_method(test_db, test_settings, test_user):
    """Test deleting an auth method."""
    service = AuthMethodService(test_db, test_settings)
    
    auth_method = service.add_password(
        user_id=test_user.id,
        password="pass",
        identifier=test_user.email
    )
    
    auth_id = auth_method.id
    
    # Delete it
    result = service.delete(auth_id)
    
    assert result is True
    assert service.get_by_id(auth_id) is None


def test_delete_auth_method_not_found(test_db, test_settings):
    """Test deleting non-existent auth method."""
    service = AuthMethodService(test_db, test_settings)
    
    result = service.delete(uuid4())
    
    assert result is False


def test_approval_workflow(test_db, test_user, test_settings):
    """Test auth method approval workflow."""
    service = AuthMethodService(test_db, test_settings)
    
    # Create auth method requiring approval
    auth_method = service.add_passkey(
        user_id=test_user.id,
        credential_id="cred",
        public_key="key",
        rp_id="localhost",
        requires_approval=True
    )
    
    assert auth_method.requires_approval is True
    assert auth_method.approved is False
    assert auth_method.approved_by is None
    
    # Approve it (admin would do this)
    admin_id = uuid4()
    approved = service.approve(auth_method.id, admin_id)
    
    assert approved is not None
    assert approved.approved is True
    assert approved.approved_by == admin_id
    assert approved.approved_at is not None


def test_multiple_passkeys_same_user(test_db, test_settings, test_user):
    """Test user can have multiple passkeys."""
    service = AuthMethodService(test_db, test_settings)
    
    # Add multiple passkeys
    passkey1 = service.add_passkey(
        user_id=test_user.id,
        credential_id="cred1",
        public_key="key1",
        rp_id="localhost"
    )
    passkey2 = service.add_passkey(
        user_id=test_user.id,
        credential_id="cred2",
        public_key="key2",
        rp_id="localhost"
    )
    
    passkeys = service.get_user_passkeys(test_user.id)
    
    assert len(passkeys) == 2
    assert {p.credential_id for p in passkeys} == {"cred1", "cred2"}


def test_count_user_auth_methods(test_db, test_settings, test_user):
    """Test counting user's auth methods."""
    service = AuthMethodService(test_db, test_settings)
    
    # Initially zero
    assert service.count_user_auth_methods(test_user.id) == 0
    
    # Add some methods
    service.add_passkey(
        user_id=test_user.id,
        credential_id="cred",
        public_key="key",
        rp_id="localhost"
    )
    service.add_password(
        user_id=test_user.id,
        password="pass",
        identifier=test_user.email
    )
    
    assert service.count_user_auth_methods(test_user.id) == 2


def test_has_password_auth(test_db, test_settings, test_user):
    """Test checking if user has password auth."""
    service = AuthMethodService(test_db, test_settings)
    
    # Initially no password
    assert service.has_password_auth(test_user.id) is False
    
    # Add password
    service.add_password(
        user_id=test_user.id,
        password="pass",
        identifier=test_user.email
    )
    
    assert service.has_password_auth(test_user.id) is True

