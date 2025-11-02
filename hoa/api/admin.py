"""
Admin API endpoints for user and auth method management.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from hoa.api.deps import require_admin
from hoa.config import get_settings
from hoa.database import get_db
from hoa.models.user import User
from hoa.schemas.auth import (
    ApproveAuthMethodRequest,
    AuthMethodResponse,
    ToggleAuthMethodRequest,
    ToggleUserRequest,
)
from hoa.schemas.user import UserResponse
from hoa.services.auth_methods import AuthMethodService
from hoa.services.user_service import UserService

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/users", response_model=list[UserResponse])
def list_users(
    enabled_only: bool = False,
    offset: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all users (admin only)."""
    user_service = UserService(db)
    users = user_service.list_all(enabled_only=enabled_only, offset=offset, limit=limit)
    
    return [UserResponse.model_validate(u) for u in users]


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get user by ID (admin only)."""
    user_service = UserService(db)
    user = user_service.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return UserResponse.model_validate(user)


@router.post("/users/{user_id}/toggle")
def toggle_user(
    user_id: UUID,
    data: ToggleUserRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Toggle user enabled status (admin only)."""
    user_service = UserService(db)
    user = user_service.toggle_enabled(user_id, data.enabled)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return {"ok": True, "message": f"User {'enabled' if data.enabled else 'disabled'}"}


@router.get("/users/{user_id}/auth-methods", response_model=list[AuthMethodResponse])
def get_user_auth_methods(
    user_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get user's authentication methods (admin only)."""
    settings = get_settings()
    auth_method_service = AuthMethodService(db, settings)
    
    auth_methods = auth_method_service.get_user_auth_methods(user_id)
    
    return [AuthMethodResponse.model_validate(am) for am in auth_methods]


@router.post("/auth-methods/{auth_method_id}/approve")
def approve_auth_method(
    auth_method_id: UUID,
    data: ApproveAuthMethodRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Approve or reject an authentication method (admin only)."""
    settings = get_settings()
    auth_method_service = AuthMethodService(db, settings)
    
    auth_method = auth_method_service.approve(
        auth_method_id,
        current_user.id,
        data.approved
    )
    
    if not auth_method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authentication method not found",
        )
    
    return {
        "ok": True,
        "message": f"Authentication method {'approved' if data.approved else 'rejected'}"
    }


@router.post("/auth-methods/{auth_method_id}/toggle")
def toggle_auth_method(
    auth_method_id: UUID,
    data: ToggleAuthMethodRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Toggle authentication method enabled status (admin only)."""
    settings = get_settings()
    auth_method_service = AuthMethodService(db, settings)
    
    auth_method = auth_method_service.toggle_enabled(auth_method_id, data.enabled)
    
    if not auth_method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authentication method not found",
        )
    
    return {
        "ok": True,
        "message": f"Authentication method {'enabled' if data.enabled else 'disabled'}"
    }


@router.get("/auth-methods/pending", response_model=list[AuthMethodResponse])
def get_pending_approvals(
    limit: int = 50,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get authentication methods pending approval (admin only)."""
    settings = get_settings()
    auth_method_service = AuthMethodService(db, settings)
    
    pending = auth_method_service.get_pending_approvals(limit=limit)
    
    return [AuthMethodResponse.model_validate(am) for am in pending]

