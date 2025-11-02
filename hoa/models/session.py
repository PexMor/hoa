"""
Session and JWT key models.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hoa.database import Base

if TYPE_CHECKING:
    from hoa.models.user import User


class Session(Base):
    """
    User session model.
    
    Tracks active user sessions with cookie-based authentication.
    """
    
    __tablename__ = "sessions"
    
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
    
    # Session token (hashed)
    session_token: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    
    # Expiry
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    
    # Client information
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")
    
    def __repr__(self) -> str:
        return f"<Session(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"


class JWTKey(Base):
    """
    JWT signing key model.
    
    Stores keys for JWT token signing and validation.
    Supports both RS256 (asymmetric) and HS256 (symmetric) algorithms.
    """
    
    __tablename__ = "jwt_keys"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Algorithm (RS256 or HS256)
    algorithm: Mapped[str] = mapped_column(String(10), nullable=False)
    
    # Public key (for RS256, PEM encoded)
    public_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Private key (encrypted, PEM encoded for RS256, secret for HS256)
    private_key_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Key metadata
    key_id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    rotated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return f"<JWTKey(id={self.id}, key_id={self.key_id}, algorithm={self.algorithm}, is_active={self.is_active})>"

