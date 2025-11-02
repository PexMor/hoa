"""
Machine-to-Machine (M2M) API endpoints for JWT token management.
"""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from hoa.api.deps import require_user
from hoa.config import get_settings
from hoa.database import get_db
from hoa.models.user import User
from hoa.schemas.token import (
    JWTTokenResponse,
    TokenCreateRequest,
    TokenRefreshRequest,
    TokenValidateRequest,
    TokenValidateResponse,
)
from hoa.services.jwt_service import JWTService

router = APIRouter(prefix="/api/m2m", tags=["M2M / JWT Tokens"])


@router.post("/token/create", response_model=JWTTokenResponse)
def create_jwt_token(
    data: TokenCreateRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Create JWT access and refresh tokens for current user."""
    settings = get_settings()
    jwt_service = JWTService(settings, db)

    # Custom expiration if provided
    expires_delta = None
    if data.expires_in_minutes:
        expires_delta = timedelta(minutes=data.expires_in_minutes)

    # Create tokens
    access_token, access_expires_at = jwt_service.create_access_token(
        current_user.id, expires_delta
    )
    refresh_token, refresh_expires_at = jwt_service.create_refresh_token(current_user.id)

    # Calculate expires_in (seconds)
    expires_in = int(
        (access_expires_at - datetime.now(UTC)).total_seconds()
        if expires_delta
        else settings.jwt_expiration_minutes * 60
    )

    return JWTTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_in,
        expires_at=access_expires_at,
    )


@router.post("/token/refresh", response_model=JWTTokenResponse)
def refresh_jwt_token(
    data: TokenRefreshRequest,
    db: Session = Depends(get_db),
):
    """Refresh JWT tokens using a refresh token."""
    settings = get_settings()
    jwt_service = JWTService(settings, db)

    # Validate refresh token
    user_id = jwt_service.get_user_id_from_token(data.refresh_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Create new tokens
    access_token, access_expires_at = jwt_service.create_access_token(user_id)
    refresh_token, refresh_expires_at = jwt_service.create_refresh_token(user_id)

    expires_in = settings.jwt_expiration_minutes * 60

    return JWTTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_in,
        expires_at=access_expires_at,
    )


@router.post("/token/validate", response_model=TokenValidateResponse)
def validate_jwt_token(
    data: TokenValidateRequest,
    db: Session = Depends(get_db),
):
    """Validate a JWT token and return information about it."""
    settings = get_settings()
    jwt_service = JWTService(settings, db)

    payload = jwt_service.validate_token(data.token, token_type="access")

    if not payload:
        return TokenValidateResponse(
            valid=False,
            error="Invalid or expired token",
        )

    return TokenValidateResponse(
        valid=True,
        user_id=payload.get("sub"),
        expires_at=payload.get("exp"),
    )

