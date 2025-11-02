"""
User management API endpoints.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from hoa.api.deps import require_user
from hoa.config import get_settings
from hoa.database import get_db
from hoa.models.user import User
from hoa.schemas.auth import AuthMethodResponse
from hoa.schemas.user import UserResponse, UserUpdate
from hoa.services.auth_methods import AuthMethodService
from hoa.services.user_service import UserService

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

