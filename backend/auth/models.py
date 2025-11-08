"""
Authentication models for SQLAlchemy ORM.
Defines the User model for database persistence.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
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
        created_at: Timestamp of account creation
        receipts: Relationship to Receipt model (one-to-many)
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

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
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
