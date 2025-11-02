"""
Authentication methods service for managing user auth methods.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from hoa.config import Settings
from hoa.models.auth_method import AuthMethod, PasskeyAuth, PasswordAuth, TokenAuth, OAuth2Auth
from hoa.models.user import User
from hoa.utils.crypto import hash_password, hash_token, verify_password, verify_token


class AuthMethodService:
    """Service for authentication method operations."""
    
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
    
    def get_by_id(self, auth_method_id: UUID) -> Optional[AuthMethod]:
        """
        Get auth method by ID.
        
        Args:
            auth_method_id: Auth method ID
        
        Returns:
            Auth method if found, None otherwise
        """
        return self.db.query(AuthMethod).filter(AuthMethod.id == auth_method_id).first()
    
    def get_user_auth_methods(self, user_id: UUID, enabled_only: bool = False) -> list[AuthMethod]:
        """
        Get all auth methods for a user.
        
        Args:
            user_id: User ID
            enabled_only: If True, only return enabled auth methods
        
        Returns:
            List of auth methods
        """
        q = self.db.query(AuthMethod).filter(AuthMethod.user_id == user_id)
        
        if enabled_only:
            q = q.filter(AuthMethod.enabled == True)
        
        return q.all()
    
    def get_passkey_by_credential_id(self, credential_id: str) -> Optional[PasskeyAuth]:
        """
        Get passkey auth method by credential ID.
        
        Args:
            credential_id: WebAuthn credential ID
        
        Returns:
            Passkey auth method if found, None otherwise
        """
        return self.db.query(PasskeyAuth).filter(
            PasskeyAuth.credential_id == credential_id
        ).first()
    
    def get_user_passkeys(self, user_id: UUID, rp_id: Optional[str] = None) -> list[PasskeyAuth]:
        """
        Get user's passkey auth methods.
        
        Args:
            user_id: User ID
            rp_id: Optional RP ID filter
        
        Returns:
            List of passkey auth methods
        """
        q = self.db.query(PasskeyAuth).filter(
            PasskeyAuth.user_id == user_id
        )
        
        if rp_id:
            q = q.filter(PasskeyAuth.rp_id == rp_id)
        
        return q.all()
    
    def add_passkey(
        self,
        user_id: UUID,
        credential_id: str,
        public_key: str,
        rp_id: str,
        sign_count: int = 0,
        transports: Optional[list[str]] = None,
        identifier: Optional[str] = None,
        requires_approval: Optional[bool] = None,
    ) -> PasskeyAuth:
        """
        Add a passkey auth method to a user.
        
        Args:
            user_id: User ID
            credential_id: WebAuthn credential ID
            public_key: Public key
            rp_id: Relying Party ID
            sign_count: Initial sign count (default: 0)
            transports: Transport methods (default: None)
            identifier: Optional identifier (email, etc.)
            requires_approval: Override default approval requirement
        
        Returns:
            Created passkey auth method
        """
        if requires_approval is None:
            requires_approval = self.settings.require_auth_method_approval
        
        passkey = PasskeyAuth(
            user_id=user_id,
            credential_id=credential_id,
            public_key=public_key,
            sign_count=sign_count,
            transports=",".join(transports) if transports else None,
            rp_id=rp_id,
            identifier=identifier,
            enabled=True,
            requires_approval=requires_approval,
            approved=not requires_approval,  # Auto-approve if not required
        )
        
        self.db.add(passkey)
        self.db.commit()
        self.db.refresh(passkey)
        
        return passkey
    
    def add_password(
        self,
        user_id: UUID,
        password: str,
        identifier: Optional[str] = None,
    ) -> PasswordAuth:
        """
        Add a password auth method to a user.
        
        Args:
            user_id: User ID
            password: Plain text password (will be hashed)
            identifier: Optional identifier (email, username)
        
        Returns:
            Created password auth method
        """
        requires_approval = self.settings.require_auth_method_approval
        
        password_auth = PasswordAuth(
            user_id=user_id,
            password_hash=hash_password(password),
            password_changed_at=datetime.utcnow(),
            identifier=identifier,
            enabled=True,
            requires_approval=requires_approval,
            approved=not requires_approval,
        )
        
        self.db.add(password_auth)
        self.db.commit()
        self.db.refresh(password_auth)
        
        return password_auth
    
    def add_token(
        self,
        user_id: UUID,
        token: str,
        description: str,
        expires_at: Optional[datetime] = None,
    ) -> TokenAuth:
        """
        Add a token auth method to a user.
        
        Args:
            user_id: User ID
            token: Plain text token (will be hashed)
            description: Token description
            expires_at: Optional expiration date
        
        Returns:
            Created token auth method
        """
        token_auth = TokenAuth(
            user_id=user_id,
            token_hash=hash_token(token),
            description=description,
            expires_at=expires_at,
            enabled=True,
            requires_approval=False,  # Tokens don't require approval
            approved=True,
        )
        
        self.db.add(token_auth)
        self.db.commit()
        self.db.refresh(token_auth)
        
        return token_auth
    
    def approve(
        self,
        auth_method_id: UUID,
        approved_by: UUID,
        approved: bool = True
    ) -> Optional[AuthMethod]:
        """
        Approve or reject an auth method.
        
        Args:
            auth_method_id: Auth method ID
            approved_by: User ID of approver
            approved: Whether to approve or reject
        
        Returns:
            Updated auth method if found, None otherwise
        """
        auth_method = self.get_by_id(auth_method_id)
        if not auth_method:
            return None
        
        auth_method.approved = approved
        auth_method.approved_by = approved_by if approved else None
        auth_method.approved_at = datetime.utcnow() if approved else None
        
        self.db.commit()
        self.db.refresh(auth_method)
        
        return auth_method
    
    def toggle_enabled(
        self,
        auth_method_id: UUID,
        enabled: bool
    ) -> Optional[AuthMethod]:
        """
        Toggle auth method enabled status.
        
        Args:
            auth_method_id: Auth method ID
            enabled: New enabled status
        
        Returns:
            Updated auth method if found, None otherwise
        """
        auth_method = self.get_by_id(auth_method_id)
        if not auth_method:
            return None
        
        auth_method.enabled = enabled
        self.db.commit()
        self.db.refresh(auth_method)
        
        return auth_method
    
    def update_passkey_sign_count(
        self,
        auth_method_id: UUID,
        new_sign_count: int
    ) -> Optional[PasskeyAuth]:
        """
        Update passkey sign count.
        
        Args:
            auth_method_id: Passkey auth method ID
            new_sign_count: New sign count
        
        Returns:
            Updated passkey auth method if found, None otherwise
        """
        passkey = self.db.query(PasskeyAuth).filter(
            PasskeyAuth.id == auth_method_id
        ).first()
        
        if not passkey:
            return None
        
        passkey.sign_count = max(passkey.sign_count, new_sign_count)
        self.db.commit()
        self.db.refresh(passkey)
        
        return passkey
    
    def delete(self, auth_method_id: UUID) -> bool:
        """
        Delete an auth method.
        
        Args:
            auth_method_id: Auth method ID
        
        Returns:
            True if deleted, False if not found
        """
        auth_method = self.get_by_id(auth_method_id)
        if not auth_method:
            return False
        
        self.db.delete(auth_method)
        self.db.commit()
        
        return True
    
    def get_pending_approvals(self, limit: int = 50) -> list[AuthMethod]:
        """
        Get auth methods pending approval.
        
        Args:
            limit: Maximum number of results
        
        Returns:
            List of auth methods pending approval
        """
        return self.db.query(AuthMethod).filter(
            AuthMethod.requires_approval == True,
            AuthMethod.approved == False,
        ).limit(limit).all()
    
    def count_user_auth_methods(
        self,
        user_id: UUID,
        auth_type: Optional[str] = None
    ) -> int:
        """
        Count user's auth methods.
        
        Args:
            user_id: User ID
            auth_type: Optional auth type filter
        
        Returns:
            Number of auth methods
        """
        q = self.db.query(AuthMethod).filter(
            AuthMethod.user_id == user_id,
            AuthMethod.enabled == True,
            AuthMethod.approved == True,
        )
        
        if auth_type:
            q = q.filter(AuthMethod.type == auth_type)
        
        return q.count()
    
    # Convenience methods
    
    def enable(self, auth_method_id: UUID) -> Optional[AuthMethod]:
        """Enable an auth method."""
        return self.toggle_enabled(auth_method_id, True)
    
    def disable(self, auth_method_id: UUID) -> Optional[AuthMethod]:
        """Disable an auth method."""
        return self.toggle_enabled(auth_method_id, False)
    
    def get_by_credential_id(self, credential_id: str) -> Optional[PasskeyAuth]:
        """Alias for get_passkey_by_credential_id."""
        return self.get_passkey_by_credential_id(credential_id)
    
    def update_sign_count(self, auth_method_id: UUID, new_sign_count: int) -> Optional[PasskeyAuth]:
        """Alias for update_passkey_sign_count."""
        return self.update_passkey_sign_count(auth_method_id, new_sign_count)
    
    # OAuth2 methods
    
    def add_oauth2(
        self,
        user_id: UUID,
        provider: str,
        provider_user_id: str,
        identifier: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ) -> OAuth2Auth:
        """
        Add an OAuth2 auth method to a user.
        
        Args:
            user_id: User ID
            provider: OAuth2 provider (google, github, etc.)
            provider_user_id: Provider's user ID
            identifier: Optional identifier (email, etc.)
            access_token: Optional access token (encrypted)
            refresh_token: Optional refresh token (encrypted)
        
        Returns:
            Created OAuth2 auth method
        """
        requires_approval = self.settings.require_auth_method_approval
        
        oauth2_auth = OAuth2Auth(
            user_id=user_id,
            provider=provider,
            provider_user_id=provider_user_id,
            identifier=identifier,
            access_token_encrypted=access_token,  # TODO: Encrypt
            refresh_token_encrypted=refresh_token,  # TODO: Encrypt
            enabled=True,
            requires_approval=requires_approval,
            approved=not requires_approval,
        )
        
        self.db.add(oauth2_auth)
        self.db.commit()
        self.db.refresh(oauth2_auth)
        
        return oauth2_auth
    
    # M2M Token methods (alias for add_token with clearer name)
    
    def add_m2m_token(
        self,
        user_id: UUID,
        token: str,
        description: str,
        expires_at: Optional[datetime] = None,
    ) -> TokenAuth:
        """
        Add an M2M token auth method to a user.
        Alias for add_token with clearer name.
        
        Args:
            user_id: User ID
            token: Plain text token (will be hashed)
            description: Token description
            expires_at: Optional expiration date
        
        Returns:
            Created token auth method
        """
        return self.add_token(user_id, token, description, expires_at)
    
    # Verification methods
    
    def verify_password(self, auth_method_id: UUID, password: str) -> bool:
        """
        Verify a password against a password auth method.
        
        Args:
            auth_method_id: Password auth method ID
            password: Plain text password to verify
        
        Returns:
            True if password matches, False otherwise
        """
        password_auth = self.db.query(PasswordAuth).filter(
            PasswordAuth.id == auth_method_id
        ).first()
        
        if not password_auth or not password_auth.password_hash:
            return False
        
        return verify_password(password, password_auth.password_hash)
    
    def verify_m2m_token(self, auth_method_id: UUID, token: str) -> bool:
        """
        Verify a token against a token auth method.
        
        Args:
            auth_method_id: Token auth method ID
            token: Plain text token to verify
        
        Returns:
            True if token matches, False otherwise
        """
        token_auth = self.db.query(TokenAuth).filter(
            TokenAuth.id == auth_method_id
        ).first()
        
        if not token_auth or not token_auth.token_hash:
            return False
        
        return verify_token(token, token_auth.token_hash)
    
    # Check methods
    
    def has_password_auth(self, user_id: UUID) -> bool:
        """
        Check if user has a password auth method.
        
        Args:
            user_id: User ID
        
        Returns:
            True if user has password auth, False otherwise
        """
        return self.db.query(PasswordAuth).filter(
            PasswordAuth.user_id == user_id,
            PasswordAuth.enabled == True,
        ).count() > 0

