"""
Authentication models for SQLAlchemy ORM.
Defines the User model for database persistence.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship

from backend.database.base import Base


class User(Base):
    """
    User model for authentication and authorization.

    Attributes:
        id: Primary key
        username: Unique username for login
        email: Unique email address
        password_hash: Bcrypt hashed password
        is_admin: Whether the user has administrator privileges
        is_active: Whether the user account is active
        last_login: Timestamp of last successful login
        created_at: Timestamp of account creation
        updated_at: Timestamp of last update
        receipts: Relationship to Receipt model (one-to-many)
        api_costs: Relationship to ApiCost model (one-to-many)
        activity_logs: Relationship to ActivityLog model (one-to-many)
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    receipts = relationship(
        "Receipt",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

    def to_dict(self) -> dict:
        """
        Convert User object to dictionary (excluding password_hash).

        Returns:
            dict: User data without sensitive information
        """
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_admin": self.is_admin,
            "is_active": self.is_active,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
