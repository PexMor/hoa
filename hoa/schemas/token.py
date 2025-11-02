"""
JWT token schemas for API validation.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class TokenCreateRequest(BaseModel):
    """Request schema for creating a JWT token."""

    expires_in_minutes: int | None = Field(None, ge=1, le=43200)  # Max 30 days


class TokenRefreshRequest(BaseModel):
    """Request schema for refreshing a JWT token."""

    refresh_token: str = Field(..., min_length=10)


class JWTTokenResponse(BaseModel):
    """Response schema for JWT token."""

    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int  # seconds
    expires_at: datetime


class TokenValidateRequest(BaseModel):
    """Request schema for validating a JWT token."""

    token: str = Field(..., min_length=10)


class TokenValidateResponse(BaseModel):
    """Response schema for token validation."""

    valid: bool
    user_id: str | None = None
    expires_at: datetime | None = None
    error: str | None = None

