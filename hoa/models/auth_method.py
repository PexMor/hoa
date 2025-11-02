"""
Authentication method models.

Supports multiple auth methods per user:
- PasskeyAuth: WebAuthn/FIDO2 credentials
- PasswordAuth: Traditional password (optional)
- OAuth2Auth: OAuth2 provider authentication
- TokenAuth: Admin/bootstrap tokens
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hoa.database import Base

if TYPE_CHECKING:
    from hoa.models.user import User


class AuthMethod(Base):
    """
    Base authentication method model.

    Uses single-table inheritance for different auth types.
    """

    __tablename__ = "auth_methods"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    # Foreign key to user
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Auth method type (discriminator)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Optional identifier (email for oauth, username, etc.)
    identifier: Mapped[str | None] = mapped_column(String(320), nullable=True, index=True)

    # Status flags
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Approval tracking
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Polymorphic configuration
    __mapper_args__ = {
        "polymorphic_identity": "base",
        "polymorphic_on": "type",
    }

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="auth_methods", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<AuthMethod(id={self.id}, type={self.type}, user_id={self.user_id})>"


class PasskeyAuth(AuthMethod):
    """
    WebAuthn/Passkey authentication method.

    Stores FIDO2 credential information.
    """

    # Credential ID (base64url encoded)
    # NOTE: nullable=True for single-table inheritance, but required in practice for passkeys
    credential_id: Mapped[str | None] = mapped_column(String(1024), nullable=True, unique=True, index=True)

    # Public key (base64 or PEM encoded)
    public_key: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Sign counter for replay protection
    sign_count: Mapped[int | None] = mapped_column(Integer, default=0, nullable=True)

    # Transport methods (usb, nfc, ble, internal)
    transports: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Relying Party ID
    rp_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    __mapper_args__ = {
        "polymorphic_identity": "passkey",
    }

    def __repr__(self) -> str:
        return f"<PasskeyAuth(id={self.id}, credential_id={self.credential_id[:20]}..., rp_id={self.rp_id})>"


class PasswordAuth(AuthMethod):
    """
    Password authentication method.

    Optional fallback auth method.
    """

    # Password hash (bcrypt)
    # NOTE: nullable=True for single-table inheritance, but required in practice for passwords
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Password change tracking
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "password",
    }

    def __repr__(self) -> str:
        return f"<PasswordAuth(id={self.id}, user_id={self.user_id})>"


class OAuth2Auth(AuthMethod):
    """
    OAuth2 authentication method.

    Links external OAuth2 provider accounts to users.
    Currently stubbed for future implementation.
    """

    # OAuth2 provider (google, github, auth0, etc.)
    # NOTE: nullable=True for single-table inheritance, but required in practice for oauth2
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)

    # Provider's user ID
    provider_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # Encrypted tokens (for API access on behalf of user)
    access_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Token expiry
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "oauth2",
    }

    def __repr__(self) -> str:
        return f"<OAuth2Auth(id={self.id}, provider={self.provider}, provider_user_id={self.provider_user_id})>"


class TokenAuth(AuthMethod):
    """
    Token authentication method.

    Used for admin tokens, API keys, and bootstrap tokens.
    """

    # Token hash (not stored in plaintext)
    # NOTE: nullable=True for single-table inheritance, but required in practice for tokens
    token_hash: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)

    # Token description
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Token expiry (optional, None = never expires)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Last used tracking
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "token",
    }

    def __repr__(self) -> str:
        return f"<TokenAuth(id={self.id}, description={self.description})>"

