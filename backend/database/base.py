"""
SQLAlchemy Base class for all database models.
All models should inherit from this Base class.
"""

from sqlalchemy.ext.declarative import declarative_base

# Create the declarative base class
Base = declarative_base()

# Import all models here to ensure they are registered with SQLAlchemy
# This is necessary for Alembic migrations to work properly
def import_models():
    """Import all models to register them with SQLAlchemy."""
    from backend.auth.models import User  # noqa: F401
    from backend.receipts.models import Receipt, Item, Category  # noqa: F401
