"""
FastAPI dependencies for authentication and database access.
"""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from hoa.config import get_settings
from hoa.database import get_db
from hoa.models.user import User
from hoa.services.jwt_service import JWTService
from hoa.services.user_service import UserService
from hoa.utils.crypto import verify_token


def get_current_user_id_from_session(request: Request) -> Optional[UUID]:
    """
    Get current user ID from session.
    
    Args:
        request: FastAPI request
    
    Returns:
        User ID if found in session, None otherwise
    """
    user_id_str = request.session.get("user_id")
    if not user_id_str:
        return None
    
    try:
        return UUID(user_id_str)
    except ValueError:
        return None


def get_current_user_from_token(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Get current user from JWT token in Authorization header.
    
    Args:
        request: FastAPI request
        db: Database session
    
    Returns:
        User if valid token, None otherwise
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header[7:]  # Remove "Bearer " prefix
    
    settings = get_settings()
    jwt_service = JWTService(settings, db)
    
    user_id = jwt_service.get_user_id_from_token(token)
    if not user_id:
        return None
    
    user_service = UserService(db)
    return user_service.get_by_id(user_id)


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Get current user from session or JWT token.
    
    Args:
        request: FastAPI request
        db: Database session
    
    Returns:
        User if authenticated, None otherwise
    """
    # Try session first
    user_id = get_current_user_id_from_session(request)
    if user_id:
        user_service = UserService(db)
        user = user_service.get_by_id(user_id)
        if user and user.enabled:
            return user
    
    # Try JWT token
    user = get_current_user_from_token(request, db)
    if user and user.enabled:
        return user
    
    return None


def require_user(
    current_user: Optional[User] = Depends(get_current_user),
) -> User:
    """
    Require authenticated user.
    
    Args:
        current_user: Current user from get_current_user
    
    Returns:
        User if authenticated
    
    Raises:
        HTTPException: If user is not authenticated or not enabled
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    if not current_user.enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    
    return current_user


def require_admin(
    current_user: User = Depends(require_user),
) -> User:
    """
    Require authenticated admin user.
    
    Args:
        current_user: Current user from require_user
    
    Returns:
        User if admin
    
    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    
    return current_user


def verify_admin_token(
    request: Request,
) -> bool:
    """
    Verify admin token from header.
    
    Args:
        request: FastAPI request
    
    Returns:
        True if valid admin token
    
    Raises:
        HTTPException: If admin token is missing or invalid
    """
    token = request.headers.get("X-Admin-Token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin token required",
        )
    
    settings = get_settings()
    if not verify_token(token, settings.admin_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token",
        )
    
    return True

