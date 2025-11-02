"""
User schemas for API validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema."""
    
    nick: Optional[str] = Field(None, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    second_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=20)


class UserCreate(UserBase):
    """Schema for creating a user."""
    
    enabled: bool = True
    is_admin: bool = False


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    
    nick: Optional[str] = Field(None, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    second_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=20)


class UserResponse(UserBase):
    """Schema for user response."""
    
    id: UUID
    enabled: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserWithAuthMethods(UserResponse):
    """Schema for user response with auth methods."""
    
    auth_method_count: int = 0
    passkey_count: int = 0
    has_password: bool = False
    
    class Config:
        from_attributes = True

