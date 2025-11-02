"""
Authentication schemas for API validation.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AuthMethodBase(BaseModel):
    """Base auth method schema."""
    
    type: str
    identifier: Optional[str] = None
    enabled: bool = True


class AuthMethodCreate(AuthMethodBase):
    """Schema for creating an auth method."""
    pass


class AuthMethodResponse(AuthMethodBase):
    """Schema for auth method response."""
    
    id: UUID
    user_id: UUID
    requires_approval: bool
    approved: bool
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PasskeyAuthResponse(AuthMethodResponse):
    """Schema for passkey auth method response."""
    
    credential_id: str
    sign_count: int
    transports: Optional[str] = None
    rp_id: str
    
    class Config:
        from_attributes = True


# WebAuthn Ceremony Schemas

class BeginRegisterRequest(BaseModel):
    """Request schema for beginning WebAuthn registration."""
    
    rp_id: str
    origin: str
    display_name: Optional[str] = None
    username_hint: Optional[str] = None


class FinishRegisterRequest(BaseModel):
    """Request schema for finishing WebAuthn registration."""
    
    rp_id: str
    origin: str
    name: Optional[str] = None
    email: Optional[str] = None
    credential: dict[str, Any]  # WebAuthn credential response


class BeginAuthRequest(BaseModel):
    """Request schema for beginning WebAuthn authentication."""
    
    rp_id: str
    origin: str
    email: Optional[str] = None


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
    user: Optional[dict[str, Any]] = None


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

