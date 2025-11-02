"""
User schemas for API validation.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema."""

    nick: str | None = Field(None, max_length=100)
    first_name: str | None = Field(None, max_length=100)
    second_name: str | None = Field(None, max_length=100)
    email: EmailStr | None = None
    phone_number: str | None = Field(None, max_length=20)


class UserCreate(UserBase):
    """Schema for creating a user."""

    enabled: bool = True
    is_admin: bool = False


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    nick: str | None = Field(None, max_length=100)
    first_name: str | None = Field(None, max_length=100)
    second_name: str | None = Field(None, max_length=100)
    email: EmailStr | None = None
    phone_number: str | None = Field(None, max_length=20)


class UserResponse(UserBase):
    """Schema for user response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    enabled: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime


class UserWithAuthMethods(UserResponse):
    """Schema for user response with auth methods."""

    model_config = ConfigDict(from_attributes=True)

    auth_method_count: int = 0
    passkey_count: int = 0
    has_password: bool = False

