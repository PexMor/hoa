"""
User service for user management operations.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from hoa.models.user import User
from hoa.schemas.user import UserCreate, UserUpdate


class UserService:
    """Service for user operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
        
        Returns:
            User if found, None otherwise
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email (case-insensitive).
        
        Args:
            email: Email address
        
        Returns:
            User if found, None otherwise
        """
        return self.db.query(User).filter(
            User.email.ilike(email)
        ).first()
    
    def get_by_nick(self, nick: str) -> Optional[User]:
        """
        Get user by nickname (case-insensitive).
        
        Args:
            nick: Nickname
        
        Returns:
            User if found, None otherwise
        """
        return self.db.query(User).filter(
            User.nick.ilike(nick)
        ).first()
    
    def search_users(
        self,
        query: str,
        enabled_only: bool = False,
        limit: int = 50
    ) -> list[User]:
        """
        Search users by email, nick, or name.
        
        Args:
            query: Search query
            enabled_only: Only return enabled users
            limit: Maximum number of results
        
        Returns:
            List of matching users
        """
        q = self.db.query(User)
        
        # Search in email, nick, first_name, second_name
        search_filter = or_(
            User.email.ilike(f"%{query}%"),
            User.nick.ilike(f"%{query}%"),
            User.first_name.ilike(f"%{query}%"),
            User.second_name.ilike(f"%{query}%"),
        )
        q = q.filter(search_filter)
        
        if enabled_only:
            q = q.filter(User.enabled == True)
        
        return q.limit(limit).all()
    
    def create(self, user_data: UserCreate) -> User:
        """
        Create a new user.
        
        Args:
            user_data: User creation data
        
        Returns:
            Created user
        """
        user = User(
            nick=user_data.nick,
            first_name=user_data.first_name,
            second_name=user_data.second_name,
            email=user_data.email,
            phone_number=user_data.phone_number,
            enabled=user_data.enabled,
            is_admin=user_data.is_admin,
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def update(self, user_id: UUID, user_data: UserUpdate) -> Optional[User]:
        """
        Update user information.
        
        Args:
            user_id: User ID
            user_data: User update data
        
        Returns:
            Updated user if found, None otherwise
        """
        user = self.get_by_id(user_id)
        if not user:
            return None
        
        # Update only provided fields
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def toggle_enabled(self, user_id: UUID, enabled: bool) -> Optional[User]:
        """
        Toggle user enabled status.
        
        Args:
            user_id: User ID
            enabled: New enabled status
        
        Returns:
            Updated user if found, None otherwise
        """
        user = self.get_by_id(user_id)
        if not user:
            return None
        
        user.enabled = enabled
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def disable(self, user_id: UUID) -> Optional[User]:
        """
        Disable a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Updated user if found, None otherwise
        """
        return self.toggle_enabled(user_id, enabled=False)
    
    def enable(self, user_id: UUID) -> Optional[User]:
        """
        Enable a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Updated user if found, None otherwise
        """
        return self.toggle_enabled(user_id, enabled=True)
    
    def make_admin(self, user_id: UUID) -> Optional[User]:
        """
        Make user an admin.
        
        Args:
            user_id: User ID
        
        Returns:
            Updated user if found, None otherwise
        """
        user = self.get_by_id(user_id)
        if not user:
            return None
        
        user.is_admin = True
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def remove_admin(self, user_id: UUID) -> Optional[User]:
        """
        Remove admin privileges from a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Updated user if found, None otherwise
        """
        user = self.get_by_id(user_id)
        if not user:
            return None
        
        user.is_admin = False
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def list_all(
        self,
        enabled_only: bool = False,
        admin_only: bool = False,
        offset: int = 0,
        limit: int = 100
    ) -> list[User]:
        """
        List all users with pagination.
        
        Args:
            enabled_only: Only return enabled users
            admin_only: Only return admin users
            offset: Pagination offset
            limit: Pagination limit
        
        Returns:
            List of users
        """
        q = self.db.query(User)
        
        if enabled_only:
            q = q.filter(User.enabled == True)
        
        if admin_only:
            q = q.filter(User.is_admin == True)
        
        return q.offset(offset).limit(limit).all()
    
    def count(self, enabled_only: bool = False) -> int:
        """
        Count total users.
        
        Args:
            enabled_only: Only count enabled users
        
        Returns:
            Number of users
        """
        q = self.db.query(User)
        
        if enabled_only:
            q = q.filter(User.enabled == True)
        
        return q.count()
    
    def delete(self, user_id: UUID) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: User ID
        
        Returns:
            True if deleted, False if not found
        """
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        self.db.delete(user)
        self.db.commit()
        
        return True

