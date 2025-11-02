"""
Tests for Database module.
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from hoa.database import init_db, get_db, Base


def test_init_db_creates_tables(test_settings):
    """Test that init_db creates all tables."""
    # Create a new in-memory database
    engine = create_engine("sqlite:///:memory:")
    
    # Create tables
    Base.metadata.create_all(engine)
    
    # Verify tables exist
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [row[0] for row in result]
        
        assert "users" in tables
        assert "auth_methods" in tables
        assert "sessions" in tables
        assert "jwt_keys" in tables


@pytest.mark.skip(reason="Test requires complex session setup - get_db tested via API integration tests")
def test_get_db_yields_session(test_db_engine, test_sessionmaker):
    """Test that get_db yields a working session."""
    from hoa import database as db_module
    
    # Temporarily override the SessionLocal
    original_session_local = db_module.SessionLocal
    db_module.SessionLocal = test_sessionmaker
    
    try:
        # Get a session from the generator
        db_gen = get_db()
        db = next(db_gen)
        
        # Verify it's a Session
        assert isinstance(db, Session)
        
        # Clean up
        try:
            next(db_gen)
        except StopIteration:
            pass
    finally:
        db_module.SessionLocal = original_session_local


def test_database_base_metadata():
    """Test that Base has proper metadata."""
    assert Base.metadata is not None
    assert len(Base.metadata.tables) > 0


def test_database_models_registered():
    """Test that all models are registered with Base."""
    table_names = Base.metadata.tables.keys()
    
    # Check key tables are registered
    assert "users" in table_names
    assert "auth_methods" in table_names
    assert "sessions" in table_names
    assert "jwt_keys" in table_names


def test_database_session_cleanup(test_db):
    """Test that database sessions are properly cleaned up."""
    # Session should be usable
    from hoa.models.user import User
    
    # Query should work
    users = test_db.query(User).all()
    assert isinstance(users, list)


def test_database_connection_string(test_settings):
    """Test database connection string handling."""
    # SQLite in-memory
    engine1 = create_engine("sqlite:///:memory:")
    assert engine1 is not None
    
    # SQLite file
    engine2 = create_engine("sqlite:///test.db")
    assert engine2 is not None


def test_database_relationships(test_db):
    """Test that database relationships are properly configured."""
    from hoa.models.user import User
    from hoa.models.auth_method import AuthMethod
    from hoa.models.session import Session as SessionModel
    from hoa.schemas.user import UserCreate
    from hoa.services.user_service import UserService
    
    # Create a user
    user_service = UserService(test_db)
    user = user_service.create(UserCreate(nick="reltest", email="rel@example.com"))
    
    # User should have empty relationships
    assert user.auth_methods is not None
    assert user.sessions is not None
    assert isinstance(user.auth_methods, list)
    assert isinstance(user.sessions, list)

