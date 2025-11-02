"""
Pytest configuration and fixtures for HOA tests.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from hoa.app import create_app
from hoa.config import Settings
from hoa.database import Base, get_db
from hoa.models import User
from hoa.services.auth_methods import AuthMethodService
from hoa.services.user_service import UserService


# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db_engine():
    """Create test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db(test_db_engine):
    """Create test database session."""
    TestSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine,
        expire_on_commit=False,
    )
    
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def test_settings():
    """Create test settings."""
    return Settings(
        host="127.0.0.1",
        port=8000,
        reload=False,
        database_url=TEST_DATABASE_URL,
        secret_key="test-secret-key-for-testing-only-must-be-at-least-32-chars",
        admin_token="test-admin-token",
        jwt_algorithm="HS256",  # Faster for tests
        jwt_expiration_minutes=60,
        jwt_refresh_expiration_days=30,
        allowed_rps="localhost|Test RP|http://localhost:8000",
        require_auth_method_approval=False,
        allow_self_service_auth=True,
        environment="development",
        log_level="DEBUG",
        session_max_age_days=14,
        session_cookie_secure=False,
        session_cookie_httponly=True,
        session_cookie_samesite="lax",
        cors_enabled=False,
        cors_origins=[],
    )


@pytest.fixture(scope="function")
def client(test_db, test_db_engine, test_settings):
    """Create test client."""
    # Override settings globally
    from hoa import config as config_module
    original_settings = config_module.settings
    config_module.settings = test_settings
    
    # Override database globally - DON'T call init_db() as it would create a new engine
    from hoa import database as db_module
    original_engine = db_module.engine
    original_session_local = db_module.SessionLocal
    
    db_module.engine = test_db_engine
    db_module.SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine,
        expire_on_commit=False,
    )
    
    # Create app - it will try to call init_db but we've already set engine/SessionLocal
    # We need to prevent init_db from being called in create_app for tests
    app = create_app()
    
    # Override get_db dependency to use our test session
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test client
    with TestClient(app) as test_client:
        yield test_client
    
    # Restore original settings and database
    config_module.settings = original_settings
    db_module.engine = original_engine
    db_module.SessionLocal = original_session_local


@pytest.fixture
def test_user(test_db, test_settings):
    """Create a test user."""
    from hoa.schemas.user import UserCreate
    
    user_service = UserService(test_db)
    user = user_service.create(UserCreate(
        nick="testuser",
        email="test@example.com",
        first_name="Test",
        second_name="User",
    ))
    test_db.commit()  # Ensure user is committed
    test_db.refresh(user)  # Refresh to get committed state
    
    return user


@pytest.fixture
def test_admin_user(test_db, test_settings):
    """Create a test admin user."""
    from hoa.schemas.user import UserCreate
    
    user_service = UserService(test_db)
    user = user_service.create(UserCreate(
        nick="admin",
        email="admin@example.com",
    ))
    user = user_service.make_admin(user.id)
    test_db.commit()  # Ensure user is committed
    test_db.refresh(user)  # Refresh to get committed state
    
    return user


@pytest.fixture
def authenticated_client(client, test_user):
    """Create authenticated test client with dependency override."""
    from hoa.api.deps import get_current_user
    
    # Override get_current_user to return our test user
    def override_get_current_user():
        return test_user
    
    client.app.dependency_overrides[get_current_user] = override_get_current_user
    
    yield client
    
    # Clean up override
    client.app.dependency_overrides.clear()


@pytest.fixture
def admin_client(client, test_admin_user):
    """Create authenticated admin test client."""
    from hoa.api.deps import get_current_user
    
    # Override get_current_user to return our test admin
    def override_get_current_user():
        return test_admin_user
    
    client.app.dependency_overrides[get_current_user] = override_get_current_user
    
    yield client
    
    # Clean up override
    client.app.dependency_overrides.clear()

