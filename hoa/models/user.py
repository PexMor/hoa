"""
User model.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hoa.database import Base

if TYPE_CHECKING:
    from hoa.models.auth_method import AuthMethod
    from hoa.models.session import Session


class User(Base):
    """
    User model.

    Users are separate from authentication methods, allowing multiple auth methods
    per user and flexible identity management.
    """

    __tablename__ = "users"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    # User attributes
    nick: Mapped[str | None] = mapped_column(String(100), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    second_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str | None] = mapped_column(
        String(320), nullable=True, unique=True, index=True
    )
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Status flags
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    auth_methods: Mapped[list["AuthMethod"]] = relationship(
        "AuthMethod",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="[AuthMethod.user_id]",
    )
    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, nick={self.nick}, email={self.email})>"

