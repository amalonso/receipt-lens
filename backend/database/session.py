"""
Database session configuration for SQLAlchemy.
Creates engine and session factory for database connections.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from backend.config import settings


# Create database engine
# For production, consider using a connection pool
# For testing, use NullPool to avoid connection issues
engine = create_engine(
    settings.database_url,
    echo=settings.db_echo,  # Log SQL queries (controlled by DB_ECHO setting)
    pool_pre_ping=True,     # Verify connections before using them
    # poolclass=NullPool    # Uncomment for testing environments
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def init_db() -> None:
    """
    Initialize database by creating all tables.
    This should only be used in development or testing.
    For production, use Alembic migrations.
    """
    from backend.database.base import Base, import_models

    # Import all models to register them
    import_models()

    # Create all tables
    Base.metadata.create_all(bind=engine)


def get_db_session():
    """
    Get a database session.
    Use this function when you need a session outside of FastAPI dependency injection.

    Returns:
        Session: SQLAlchemy database session
    """
    return SessionLocal()
