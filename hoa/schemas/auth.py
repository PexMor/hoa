"""
Authentication schemas for API validation.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuthMethodBase(BaseModel):
    """Base auth method schema."""

    type: str
    identifier: str | None = None
    enabled: bool = True


class AuthMethodCreate(AuthMethodBase):
    """Schema for creating an auth method."""
    pass


class AuthMethodResponse(AuthMethodBase):
    """Schema for auth method response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    requires_approval: bool
    approved: bool
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class PasskeyAuthResponse(AuthMethodResponse):
    """Schema for passkey auth method response."""

    model_config = ConfigDict(from_attributes=True)

    credential_id: str
    sign_count: int
    transports: str | None = None
    rp_id: str


# WebAuthn Ceremony Schemas

class BeginRegisterRequest(BaseModel):
    """Request schema for beginning WebAuthn registration."""

    rp_id: str
    origin: str
    display_name: str | None = None
    username_hint: str | None = None


class FinishRegisterRequest(BaseModel):
    """Request schema for finishing WebAuthn registration."""

    rp_id: str
    origin: str
    name: str | None = None
    email: str | None = None
    credential: dict[str, Any]  # WebAuthn credential response


class BeginAuthRequest(BaseModel):
    """Request schema for beginning WebAuthn authentication."""

    rp_id: str
    origin: str
    email: str | None = None


class FinishAuthRequest(BaseModel):
    """Request schema for finishing WebAuthn authentication."""

    rp_id: str
    origin: str
    credential: dict[str, Any]  # WebAuthn credential response


# Token Authentication

class TokenAuthRequest(BaseModel):
    """Request schema for token authentication."""

    token: str = Field(..., min_length=10)


# Current User Response

class CurrentUserResponse(BaseModel):
    """Schema for current user response."""

    authenticated: bool
    user: dict[str, Any] | None = None


# Approval Requests

class ApproveAuthMethodRequest(BaseModel):
    """Request schema for approving an auth method."""

    approved: bool = True


class ToggleAuthMethodRequest(BaseModel):
    """Request schema for toggling auth method enabled status."""

    enabled: bool


class ToggleUserRequest(BaseModel):
    """Request schema for toggling user enabled status."""

    enabled: bool

