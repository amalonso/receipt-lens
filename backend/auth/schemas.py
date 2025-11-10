"""
Pydantic schemas for authentication request/response validation.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
import re


class UserRegisterRequest(BaseModel):
    """Schema for user registration request."""

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username for login (3-50 characters)"
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password (minimum 8 characters)"
    )

    @validator('username')
    def validate_username(cls, v: str) -> str:
        """
        Validate username format.
        Must contain only alphanumeric characters, underscores, and hyphens.
        """
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError(
                'Username must contain only alphanumeric characters, '
                'underscores, and hyphens'
            )
        return v.lower()

    @validator('password')
    def validate_password(cls, v: str) -> str:
        """
        Validate password strength.
        Must contain at least one uppercase, one lowercase, and one digit.
        """
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserLoginRequest(BaseModel):
    """Schema for user login request."""

    username: str = Field(
        ...,
        description="Username or email"
    )
    password: str = Field(
        ...,
        description="User password"
    )


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str = Field(
        ...,
        description="JWT access token"
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer')"
    )
    expires_in: int = Field(
        ...,
        description="Token expiration time in seconds"
    )


class UserResponse(BaseModel):
    """Schema for user data response."""

    id: int
    username: str
    email: str
    is_admin: bool = False
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Pydantic v2 (was orm_mode in v1)


class AuthResponse(BaseModel):
    """Standard authentication response wrapper."""

    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


class RegisterResponse(AuthResponse):
    """Response for successful registration."""

    data: Optional[dict] = Field(
        default=None,
        description="Contains 'user' and 'token' objects"
    )


class LoginResponse(AuthResponse):
    """Response for successful login."""

    data: Optional[dict] = Field(
        default=None,
        description="Contains 'user' and 'token' objects"
    )


class CurrentUserResponse(AuthResponse):
    """Response for current user information."""

    data: Optional[UserResponse] = None
