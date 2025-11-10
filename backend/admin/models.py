"""
Admin-related models for SQLAlchemy ORM.
Defines ApiCost, ActivityLog, and SystemConfig models.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Numeric, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from backend.database.base import Base


class ApiCost(Base):
    """
    API cost tracking model for monitoring AI processing expenses.

    Attributes:
        id: Primary key
        user_id: Foreign key to users table
        receipt_id: Foreign key to receipts table (optional)
        provider: AI provider name (claude, google_vision, openai, etc.)
        model: Specific model used
        input_tokens: Number of input tokens processed
        output_tokens: Number of output tokens generated
        cost_usd: Cost in USD
        processing_time_ms: Processing time in milliseconds
        success: Whether the API call succeeded
        error_message: Error message if failed
        created_at: Timestamp of the API call
    """

    __tablename__ = "api_costs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    receipt_id = Column(Integer, ForeignKey("receipts.id", ondelete="SET NULL"), nullable=True, index=True)
    provider = Column(String(50), nullable=False, index=True)
    model = Column(String(100), nullable=True)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    cost_usd = Column(Numeric(10, 6), nullable=False)
    processing_time_ms = Column(Integer, nullable=True)
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", backref="api_costs")
    receipt = relationship("Receipt", backref="api_costs")

    def __repr__(self) -> str:
        """String representation of ApiCost."""
        return f"<ApiCost(id={self.id}, provider='{self.provider}', cost={self.cost_usd})>"

    def to_dict(self) -> dict:
        """Convert ApiCost object to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "receipt_id": self.receipt_id,
            "provider": self.provider,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": float(self.cost_usd) if self.cost_usd else 0.0,
            "processing_time_ms": self.processing_time_ms,
            "success": self.success,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ActivityLog(Base):
    """
    Activity log model for audit trail.

    Attributes:
        id: Primary key
        user_id: Foreign key to users table (nullable for system actions)
        action: Action type (login, upload, delete, update_config, etc.)
        entity_type: Type of entity affected (user, receipt, config, etc.)
        entity_id: ID of affected entity
        details: Additional context as JSON
        ip_address: IP address of the request
        user_agent: User agent string
        created_at: Timestamp of the action
    """

    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=True, index=True)
    entity_id = Column(Integer, nullable=True, index=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", backref="activity_logs")

    def __repr__(self) -> str:
        """String representation of ActivityLog."""
        return f"<ActivityLog(id={self.id}, action='{self.action}', user_id={self.user_id})>"

    def to_dict(self) -> dict:
        """Convert ActivityLog object to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class SystemConfig(Base):
    """
    System configuration model for storing application settings.

    Attributes:
        id: Primary key
        config_key: Unique configuration key
        config_value: Configuration value as string
        value_type: Type of value (string, integer, boolean, json)
        category: Configuration category (vision, security, upload, general)
        description: Human-readable description
        is_sensitive: Whether to hide from frontend
        updated_by: Foreign key to users table (admin who updated)
        updated_at: Timestamp of last update
        created_at: Timestamp of creation
    """

    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), unique=True, nullable=False, index=True)
    config_value = Column(Text, nullable=False)
    value_type = Column(String(20), default="string", nullable=False)
    category = Column(String(50), nullable=True, index=True)
    description = Column(Text, nullable=True)
    is_sensitive = Column(Boolean, default=False, nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    updater = relationship("User", backref="config_updates", foreign_keys=[updated_by])

    def __repr__(self) -> str:
        """String representation of SystemConfig."""
        return f"<SystemConfig(key='{self.config_key}', value='{self.config_value}')>"

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convert SystemConfig object to dictionary.

        Args:
            include_sensitive: Whether to include sensitive values

        Returns:
            dict: Configuration data
        """
        value = self.config_value if (include_sensitive or not self.is_sensitive) else "***HIDDEN***"

        return {
            "id": self.id,
            "config_key": self.config_key,
            "config_value": value,
            "value_type": self.value_type,
            "category": self.category,
            "description": self.description,
            "is_sensitive": self.is_sensitive,
            "updated_by": self.updated_by,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def get_typed_value(self):
        """
        Get the configuration value converted to its proper type.

        Returns:
            Typed value based on value_type
        """
        if self.value_type == "integer":
            return int(self.config_value)
        elif self.value_type == "boolean":
            return self.config_value.lower() in ("true", "1", "yes", "on")
        elif self.value_type == "json":
            import json
            return json.loads(self.config_value)
        else:
            return self.config_value
