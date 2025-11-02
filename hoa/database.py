"""
Database configuration and session management.
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# Global engine and session factory
engine = None
SessionLocal = None


def init_db(database_url: str, echo: bool = False, force: bool = False) -> None:
    """
    Initialize the database engine and session factory.
    
    Args:
        database_url: Database connection URL
        echo: Whether to echo SQL statements (for debugging)
        force: Force re-initialization even if already initialized
    """
    global engine, SessionLocal
    
    # Skip if already initialized (unless force=True)
    if not force and engine is not None and SessionLocal is not None:
        return
    
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    
    engine = create_engine(
        database_url,
        echo=echo,
        connect_args=connect_args,
    )
    
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False,
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Get a database session.
    
    Yields:
        Database session
    """
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Get a database session as a context manager.
    
    Yields:
        Database session
    """
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

