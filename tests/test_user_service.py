"""
Tests for User Service.
"""

import pytest
from uuid import uuid4

from hoa.models.user import User
from hoa.services.user_service import UserService
from hoa.schemas.user import UserCreate, UserUpdate


def test_create_user(test_db):
    """Test creating a new user."""
    service = UserService(test_db)
    
    user_data = UserCreate(
        nick="testuser",
        email="test@example.com",
        first_name="Test",
        second_name="User",
        phone_number="+1234567890",
    )
    
    user = service.create(user_data)
    
    assert user.id is not None
    assert user.nick == "testuser"
    assert user.email == "test@example.com"
    assert user.first_name == "Test"
    assert user.second_name == "User"
    assert user.phone_number == "+1234567890"
    assert user.enabled is True
    assert user.is_admin is False
    assert user.created_at is not None
    assert user.updated_at is not None


def test_create_user_minimal(test_db):
    """Test creating a user with minimal data."""
    service = UserService(test_db)
    
    user_data = UserCreate(
        email="minimal@example.com",
    )
    
    user = service.create(user_data)
    
    assert user.id is not None
    assert user.email == "minimal@example.com"
    assert user.nick is None
    assert user.enabled is True


def test_get_by_id(test_db, test_user):
    """Test getting user by ID."""
    service = UserService(test_db)
    
    user = service.get_by_id(test_user.id)
    
    assert user is not None
    assert user.id == test_user.id
    assert user.email == test_user.email


def test_get_by_id_not_found(test_db):
    """Test getting non-existent user."""
    service = UserService(test_db)
    
    user = service.get_by_id(uuid4())
    
    assert user is None


def test_get_by_email(test_db, test_user):
    """Test getting user by email."""
    service = UserService(test_db)
    
    user = service.get_by_email(test_user.email)
    
    assert user is not None
    assert user.id == test_user.id
    assert user.email == test_user.email


def test_get_by_email_case_insensitive(test_db, test_user):
    """Test email lookup is case-insensitive."""
    service = UserService(test_db)
    
    user = service.get_by_email(test_user.email.upper())
    
    assert user is not None
    assert user.id == test_user.id


def test_get_by_email_not_found(test_db):
    """Test getting user by non-existent email."""
    service = UserService(test_db)
    
    user = service.get_by_email("nonexistent@example.com")
    
    assert user is None


def test_update_user(test_db, test_user):
    """Test updating user information."""
    service = UserService(test_db)
    
    update_data = UserUpdate(
        nick="updateduser",
        first_name="Updated",
        phone_number="+9876543210",
    )
    
    updated_user = service.update(test_user.id, update_data)
    
    assert updated_user.nick == "updateduser"
    assert updated_user.first_name == "Updated"
    assert updated_user.phone_number == "+9876543210"
    # Email should remain unchanged
    assert updated_user.email == test_user.email


def test_update_user_not_found(test_db):
    """Test updating non-existent user."""
    service = UserService(test_db)
    
    update_data = UserUpdate(nick="updated")
    
    result = service.update(uuid4(), update_data)
    
    assert result is None


def test_disable_user(test_db, test_user):
    """Test disabling a user."""
    service = UserService(test_db)
    
    assert test_user.enabled is True
    
    disabled_user = service.disable(test_user.id)
    
    assert disabled_user.enabled is False


def test_enable_user(test_db):
    """Test enabling a disabled user."""
    service = UserService(test_db)
    
    # Create a disabled user
    user_data = UserCreate(
        email="disabled@example.com",
        enabled=False,
    )
    user = service.create(user_data)
    assert user.enabled is False
    
    # Enable the user
    enabled_user = service.enable(user.id)
    
    assert enabled_user.enabled is True


def test_make_admin(test_db, test_user):
    """Test making a user an admin."""
    service = UserService(test_db)
    
    assert test_user.is_admin is False
    
    admin_user = service.make_admin(test_user.id)
    
    assert admin_user.is_admin is True


def test_remove_admin(test_db):
    """Test removing admin privileges."""
    service = UserService(test_db)
    
    # Create an admin user
    user_data = UserCreate(
        email="admin@example.com",
        is_admin=True,
    )
    admin = service.create(user_data)
    assert admin.is_admin is True
    
    # Remove admin privileges
    regular_user = service.remove_admin(admin.id)
    
    assert regular_user.is_admin is False


def test_list_all_users(test_db, test_user):
    """Test listing all users."""
    service = UserService(test_db)
    
    # Create additional users
    for i in range(3):
        service.create(UserCreate(email=f"user{i}@example.com"))
    
    users = service.list_all()
    
    assert len(users) >= 4  # test_user + 3 new users


def test_list_users_with_pagination(test_db):
    """Test listing users with pagination."""
    service = UserService(test_db)
    
    # Create 10 users
    for i in range(10):
        service.create(UserCreate(email=f"user{i}@example.com"))
    
    # Get first page
    page1 = service.list_all(limit=5, offset=0)
    assert len(page1) == 5
    
    # Get second page
    page2 = service.list_all(limit=5, offset=5)
    assert len(page2) == 5
    
    # Ensure pages are different
    page1_ids = {u.id for u in page1}
    page2_ids = {u.id for u in page2}
    assert page1_ids.isdisjoint(page2_ids)


def test_list_admin_only(test_db):
    """Test listing only admin users."""
    service = UserService(test_db)
    
    # Create regular and admin users
    service.create(UserCreate(email="regular1@example.com", is_admin=False))
    service.create(UserCreate(email="admin1@example.com", is_admin=True))
    service.create(UserCreate(email="regular2@example.com", is_admin=False))
    service.create(UserCreate(email="admin2@example.com", is_admin=True))
    
    admins = service.list_all(admin_only=True)
    
    assert len(admins) == 2
    assert all(u.is_admin for u in admins)


def test_list_enabled_only(test_db):
    """Test listing only enabled users."""
    service = UserService(test_db)
    
    # Create enabled and disabled users
    service.create(UserCreate(email="enabled1@example.com", enabled=True))
    service.create(UserCreate(email="disabled1@example.com", enabled=False))
    service.create(UserCreate(email="enabled2@example.com", enabled=True))
    
    enabled_users = service.list_all(enabled_only=True)
    
    assert all(u.enabled for u in enabled_users)
    assert len([u for u in enabled_users if u.email.startswith("enabled")]) >= 2


def test_delete_user(test_db, test_user):
    """Test deleting a user."""
    service = UserService(test_db)
    
    user_id = test_user.id
    
    result = service.delete(user_id)
    
    assert result is True
    assert service.get_by_id(user_id) is None


def test_delete_user_not_found(test_db):
    """Test deleting non-existent user."""
    service = UserService(test_db)
    
    result = service.delete(uuid4())
    
    assert result is False


def test_toggle_enabled_not_found(test_db):
    """Test toggling enabled status for non-existent user."""
    service = UserService(test_db)
    
    result = service.toggle_enabled(uuid4(), True)
    
    assert result is None


def test_enable_not_found(test_db):
    """Test enabling non-existent user."""
    service = UserService(test_db)
    
    result = service.enable(uuid4())
    
    assert result is None


def test_make_admin_not_found(test_db):
    """Test making non-existent user admin."""
    service = UserService(test_db)
    
    result = service.make_admin(uuid4())
    
    assert result is None


def test_remove_admin_not_found(test_db):
    """Test removing admin from non-existent user."""
    service = UserService(test_db)
    
    result = service.remove_admin(uuid4())
    
    assert result is None


def test_get_by_nick(test_db):
    """Test getting user by nickname."""
    service = UserService(test_db)
    
    # Create user
    user_data = UserCreate(nick="testnick", email="nick@example.com")
    created_user = service.create(user_data)
    
    # Get by nick
    found_user = service.get_by_nick("testnick")
    
    assert found_user is not None
    assert found_user.id == created_user.id
    assert found_user.nick == "testnick"


def test_get_by_nick_not_found(test_db):
    """Test getting user by nick when not found."""
    service = UserService(test_db)
    
    found_user = service.get_by_nick("nonexistent")
    
    assert found_user is None

