"""
User management API endpoints.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from hoa.api.deps import require_user
from hoa.config import get_settings
from hoa.database import get_db
from hoa.models.user import User
from hoa.schemas.auth import AuthMethodResponse
from hoa.schemas.user import UserResponse, UserUpdate
from hoa.services.auth_methods import AuthMethodService
from hoa.services.jwt_service import JWTService
from hoa.services.user_service import UserService
from hoa.services.webauthn import WebAuthnService
from hoa.utils.crypto import generate_key_id

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(require_user)):
    """Get current user's profile."""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
def update_my_profile(
    data: UserUpdate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Update current user's profile."""
    user_service = UserService(db)
    updated_user = user_service.update(current_user.id, data)

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse.model_validate(updated_user)


@router.get("/me/auth-methods", response_model=list[AuthMethodResponse])
def get_my_auth_methods(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Get current user's authentication methods."""
    settings = get_settings()
    auth_method_service = AuthMethodService(db, settings)
    auth_methods = auth_method_service.get_user_auth_methods(current_user.id)

    return [AuthMethodResponse.model_validate(am) for am in auth_methods]


@router.delete("/me/auth-methods/{auth_method_id}")
def delete_my_auth_method(
    auth_method_id: UUID,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Delete one of current user's authentication methods."""
    settings = get_settings()
    auth_method_service = AuthMethodService(db, settings)

    # Verify auth method belongs to current user
    auth_method = auth_method_service.get_by_id(auth_method_id)
    if not auth_method or auth_method.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authentication method not found",
        )

    # Prevent deletion if it's the last auth method
    remaining_count = auth_method_service.count_user_auth_methods(current_user.id)
    if remaining_count <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete last authentication method",
        )

    auth_method_service.delete(auth_method_id)

    return {"ok": True, "message": "Authentication method deleted"}


# ===== Add Authentication Methods =====

class AddPasswordRequest(BaseModel):
    """Request to add password authentication."""
    password: str
    identifier: str | None = None


@router.post("/me/auth-methods/password", response_model=AuthMethodResponse)
def add_password_auth_method(
    data: AddPasswordRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Add password authentication method to current user."""
    settings = get_settings()
    auth_method_service = AuthMethodService(db, settings)

    # Validate password strength
    if len(data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long",
        )

    # Check if user already has a password
    existing_methods = auth_method_service.get_user_auth_methods(current_user.id)
    for method in existing_methods:
        if method.type == "password":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has a password authentication method",
            )

    # Add password
    password_auth = auth_method_service.add_password(
        user_id=current_user.id,
        password=data.password,
        identifier=data.identifier,
    )

    return AuthMethodResponse.model_validate(password_auth)


class BeginAddPasskeyRequest(BaseModel):
    """Request to begin adding a passkey."""
    rp_id: str
    origin: str
    display_name: str | None = None


@router.post("/me/auth-methods/passkey/begin")
def begin_add_passkey(
    data: BeginAddPasskeyRequest,
    request: Request,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Begin adding a new passkey to current user."""
    settings = get_settings()
    webauthn_service = WebAuthnService(settings)
    auth_method_service = AuthMethodService(db, settings)

    # Verify RP/origin
    rp = webauthn_service.get_rp_for(data.rp_id, data.origin)
    if not rp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid RP/origin combination: {data.rp_id}/{data.origin}"
        )

    # Get existing passkeys to exclude
    existing_passkeys = auth_method_service.get_user_passkeys(current_user.id, data.rp_id)
    exclude_credentials = [p.credential_id for p in existing_passkeys]

    # Generate registration options
    try:
        options, challenge = webauthn_service.begin_registration(
            rp_id=data.rp_id,
            origin=data.origin,
            user_id=str(current_user.id),
            username=current_user.email or current_user.nick,
            display_name=data.display_name or current_user.nick or current_user.first_name or "User",
            exclude_credentials=exclude_credentials,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to begin passkey registration: {str(e)}"
        ) from e

    # Store challenge in session
    request.session["webauthn_add_passkey_challenge"] = challenge
    request.session["webauthn_add_passkey_rp_id"] = data.rp_id
    request.session["webauthn_add_passkey_origin"] = data.origin

    return {"options": options}


class FinishAddPasskeyRequest(BaseModel):
    """Request to finish adding a passkey."""
    rp_id: str
    origin: str
    credential: dict


@router.post("/me/auth-methods/passkey/finish", response_model=AuthMethodResponse)
def finish_add_passkey(
    data: FinishAddPasskeyRequest,
    request: Request,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Finish adding a new passkey to current user."""
    settings = get_settings()
    webauthn_service = WebAuthnService(settings)
    auth_method_service = AuthMethodService(db, settings)

    # Verify session data
    challenge = request.session.get("webauthn_add_passkey_challenge")
    rp_id = request.session.get("webauthn_add_passkey_rp_id")
    origin = request.session.get("webauthn_add_passkey_origin")

    if not all([challenge, rp_id, origin]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passkey registration session expired or invalid"
        )

    # Verify RP/origin match
    if data.rp_id != rp_id or data.origin != origin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="RP/origin mismatch"
        )

    # Verify registration
    try:
        credential_info = webauthn_service.finish_registration(
            credential=data.credential,
            expected_challenge=challenge,
            expected_rp_id=rp_id,
            expected_origin=origin,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Passkey verification failed: {str(e)}"
        ) from e

    # Clear session
    request.session.pop("webauthn_add_passkey_challenge", None)
    request.session.pop("webauthn_add_passkey_rp_id", None)
    request.session.pop("webauthn_add_passkey_origin", None)

    # Add passkey to user
    passkey_auth = auth_method_service.add_passkey(
        user_id=current_user.id,
        credential_id=credential_info["credential_id"],
        public_key=credential_info["public_key"],
        rp_id=rp_id,
        sign_count=credential_info["sign_count"],
        transports=credential_info.get("transports", []),
    )

    return AuthMethodResponse.model_validate(passkey_auth)


class CreateTokenRequest(BaseModel):
    """Request to create an API token."""
    description: str
    expires_in_days: int | None = None  # None = use default (30 days)


class TokenCreatedResponse(BaseModel):
    """Response after creating a token."""
    auth_method: AuthMethodResponse
    access_token: str
    refresh_token: str
    expires_at: datetime


@router.post("/me/auth-methods/token/create")
def create_api_token(
    data: CreateTokenRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Create an API token for current user."""
    settings = get_settings()
    auth_method_service = AuthMethodService(db, settings)
    jwt_service = JWTService(settings, db)

    # Validate description
    if not data.description or len(data.description.strip()) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Description must be at least 3 characters long",
        )

    # Calculate expiration
    if data.expires_in_days:
        if data.expires_in_days < 1 or data.expires_in_days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Expiration must be between 1 and 365 days",
            )
        expires_at = datetime.now(UTC) + timedelta(days=data.expires_in_days)
        expires_delta = timedelta(days=data.expires_in_days)
    else:
        # Default: 30 days
        expires_at = datetime.now(UTC) + timedelta(days=30)
        expires_delta = timedelta(days=30)

    # Generate a unique token identifier
    token_id = generate_key_id(16)  # Short ID for the auth method

    # Create JWT tokens
    access_token, access_expires_at = jwt_service.create_access_token(
        current_user.id,
        expires_delta
    )
    refresh_token, _ = jwt_service.create_refresh_token(current_user.id)

    # Store token reference in auth methods
    token_auth = auth_method_service.add_m2m_token(
        user_id=current_user.id,
        token=token_id,  # Store the token ID, not the JWT
        description=data.description,
        expires_at=expires_at,
    )

    return TokenCreatedResponse(
        auth_method=AuthMethodResponse.model_validate(token_auth),
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=access_expires_at,
    )

