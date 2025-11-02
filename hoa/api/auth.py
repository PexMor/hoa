"""
Authentication API endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from hoa.api.deps import get_current_user
from hoa.config import get_settings
from hoa.database import get_db
from hoa.models.user import User
from hoa.schemas.auth import (
    BeginAuthRequest,
    BeginRegisterRequest,
    CurrentUserResponse,
    FinishAuthRequest,
    FinishRegisterRequest,
    TokenAuthRequest,
)
from hoa.schemas.user import UserResponse
from hoa.services.auth_methods import AuthMethodService
from hoa.services.user_service import UserService
from hoa.services.webauthn import WebAuthnService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.get("/me", response_model=CurrentUserResponse)
def get_current_user_info(
    current_user: User | None = Depends(get_current_user),
):
    """Get current user information."""
    if not current_user:
        return {"authenticated": False, "user": None}

    return {
        "authenticated": True,
        "user": {
            "id": str(current_user.id),
            "nick": current_user.nick,
            "first_name": current_user.first_name,
            "second_name": current_user.second_name,
            "email": current_user.email,
            "phone_number": current_user.phone_number,
            "enabled": current_user.enabled,
            "is_admin": current_user.is_admin,
        }
    }


@router.post("/logout")
def logout(request: Request):
    """Logout current user."""
    request.session.clear()
    return {"ok": True, "message": "Logged out successfully"}


# WebAuthn Registration

@router.post("/webauthn/register/begin")
def begin_webauthn_registration(
    data: BeginRegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    """Begin WebAuthn registration ceremony."""
    settings = get_settings()
    webauthn_service = WebAuthnService(settings)

    # Verify RP/origin
    rp = webauthn_service.get_rp_for(data.rp_id, data.origin)
    if not rp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid RP/origin combination: {data.rp_id}/{data.origin}"
        )

    # Determine user - create new or use existing
    if current_user:
        user_id = str(current_user.id)
        username = data.username_hint or current_user.email or current_user.nick or f"user-{str(current_user.id)[:8]}"
        display_name = data.display_name or current_user.nick or current_user.first_name or "User"
    else:
        # Create ephemeral user ID for registration
        user_id = str(uuid.uuid4())
        username = data.username_hint or f"user-{user_id[:8]}"
        display_name = data.display_name or "User"

    # Get existing credentials to exclude
    auth_method_service = AuthMethodService(db, settings)
    existing_passkeys = []
    if current_user:
        passkeys = auth_method_service.get_user_passkeys(current_user.id, data.rp_id)
        existing_passkeys = [p.credential_id for p in passkeys]

    # Generate registration options
    try:
        options, challenge = webauthn_service.begin_registration(
            rp_id=data.rp_id,
            origin=data.origin,
            user_id=user_id,
            username=username,
            display_name=display_name,
            exclude_credentials=existing_passkeys,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to begin registration: {str(e)}"
        ) from e

    # Store challenge and registration data in session
    request.session["webauthn_reg_challenge"] = challenge
    request.session["webauthn_reg_rp_id"] = data.rp_id
    request.session["webauthn_reg_origin"] = data.origin
    request.session["webauthn_reg_user_id"] = user_id

    return {"options": options, "user_id": user_id}


@router.post("/webauthn/register/finish", response_model=UserResponse)
def finish_webauthn_registration(
    data: FinishRegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    """Finish WebAuthn registration ceremony."""
    settings = get_settings()
    webauthn_service = WebAuthnService(settings)

    # Verify session data
    challenge = request.session.get("webauthn_reg_challenge")
    rp_id = request.session.get("webauthn_reg_rp_id")
    origin = request.session.get("webauthn_reg_origin")
    user_id_str = request.session.get("webauthn_reg_user_id")

    if not all([challenge, rp_id, origin, user_id_str]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration session expired or invalid"
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
            detail=f"Registration verification failed: {str(e)}"
        ) from e

    # Create or get user
    user_service = UserService(db)
    auth_method_service = AuthMethodService(db, settings)

    if current_user:
        user = current_user
        # Update user info if provided
        if data.name:
            user.nick = data.name
        if data.email:
            user.email = data.email
        db.commit()
        db.refresh(user)
    else:
        # Check if user_id matches an existing session user
        try:
            user_uuid = uuid.UUID(user_id_str)
            user = user_service.get_by_id(user_uuid)
        except ValueError:
            user = None

        # Create new user if needed
        if not user:
            from hoa.schemas.user import UserCreate
            user = user_service.create(UserCreate(
                nick=data.name,
                email=data.email,
            ))

    # Add passkey to user
    auth_method_service.add_passkey(
        user_id=user.id,
        credential_id=credential_info["credential_id"],
        public_key=credential_info["public_key"],
        sign_count=credential_info["sign_count"],
        transports=credential_info["transports"],
        rp_id=rp_id,
        identifier=data.email,
    )

    # Auto-login if user is enabled
    if user.enabled:
        request.session["user_id"] = str(user.id)

    # Clear registration session data
    for key in ["webauthn_reg_challenge", "webauthn_reg_rp_id", "webauthn_reg_origin", "webauthn_reg_user_id"]:
        request.session.pop(key, None)

    return UserResponse.model_validate(user)


# WebAuthn Authentication

@router.post("/webauthn/login/begin")
def begin_webauthn_authentication(
    data: BeginAuthRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Begin WebAuthn authentication ceremony."""
    settings = get_settings()
    webauthn_service = WebAuthnService(settings)

    # Verify RP/origin
    rp = webauthn_service.get_rp_for(data.rp_id, data.origin)
    if not rp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid RP/origin combination: {data.rp_id}/{data.origin}"
        )

    # Get allowed credentials
    allowed_credentials = []
    if data.email:
        user_service = UserService(db)
        user = user_service.get_by_email(data.email)
        if user:
            auth_method_service = AuthMethodService(db, settings)
            passkeys = auth_method_service.get_user_passkeys(user.id, data.rp_id)
            # Only include enabled and approved passkeys
            allowed_credentials = [
                p.credential_id for p in passkeys
                if p.enabled and p.approved
            ]

    # Generate authentication options
    try:
        options, challenge = webauthn_service.begin_authentication(
            rp_id=data.rp_id,
            origin=data.origin,
            allow_credentials=allowed_credentials if allowed_credentials else None,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to begin authentication: {str(e)}"
        ) from e

    # Store challenge in session
    request.session["webauthn_auth_challenge"] = challenge
    request.session["webauthn_auth_rp_id"] = data.rp_id
    request.session["webauthn_auth_origin"] = data.origin

    return {"options": options}


@router.post("/webauthn/login/finish", response_model=UserResponse)
def finish_webauthn_authentication(
    data: FinishAuthRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Finish WebAuthn authentication ceremony."""
    settings = get_settings()
    webauthn_service = WebAuthnService(settings)
    auth_method_service = AuthMethodService(db, settings)

    # Verify session data
    challenge = request.session.get("webauthn_auth_challenge")
    rp_id = request.session.get("webauthn_auth_rp_id")
    origin = request.session.get("webauthn_auth_origin")

    if not all([challenge, rp_id, origin]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authentication session expired or invalid"
        )

    # Verify RP/origin match
    if data.rp_id != rp_id or data.origin != origin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="RP/origin mismatch"
        )

    # Extract credential ID to find the passkey
    credential_id = data.credential.get("id")
    if not credential_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing credential ID"
        )

    # Find passkey
    passkey = auth_method_service.get_passkey_by_credential_id(credential_id)
    if not passkey or not passkey.enabled or not passkey.approved:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credential not found or disabled"
        )

    # Get user
    user_service = UserService(db)
    user = user_service.get_by_id(passkey.user_id)
    if not user or not user.enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    # Verify authentication
    try:
        auth_result = webauthn_service.finish_authentication(
            credential=data.credential,
            expected_challenge=challenge,
            expected_rp_id=rp_id,
            expected_origin=origin,
            credential_public_key=passkey.public_key,
            credential_current_sign_count=passkey.sign_count,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication verification failed: {str(e)}"
        ) from e

    # Update sign count
    auth_method_service.update_passkey_sign_count(
        passkey.id,
        auth_result["new_sign_count"]
    )

    # Create session
    request.session["user_id"] = str(user.id)

    # Clear authentication session data
    for key in ["webauthn_auth_challenge", "webauthn_auth_rp_id", "webauthn_auth_origin"]:
        request.session.pop(key, None)

    return UserResponse.model_validate(user)


# Bootstrap Token Authentication

@router.post("/token/bootstrap", response_model=UserResponse)
def bootstrap_with_token(
    data: TokenAuthRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Bootstrap authentication using admin token.

    Creates a new admin user if needed, or logs in existing admin.
    """
    settings = get_settings()

    # Verify admin token
    if data.token != settings.admin_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token"
        )

    user_service = UserService(db)

    # Find or create admin user
    admin_users = user_service.list_all(admin_only=True, limit=1)
    if admin_users:
        user = admin_users[0]
    else:
        # Create first admin user
        from hoa.schemas.user import UserCreate
        user = user_service.create(UserCreate(
            nick="admin",
            email=None,
        ))
        user = user_service.make_admin(user.id)

    # Create session
    request.session["user_id"] = str(user.id)

    return UserResponse.model_validate(user)

