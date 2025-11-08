"""
Authentication service with business logic for user management.
Handles password hashing, JWT generation, and user authentication.
"""

import logging
import hashlib
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from backend.config import settings
from backend.auth.models import User
from backend.auth.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse
)

logger = logging.getLogger(__name__)

# Password hashing context with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    pass


class AuthService:
    """Service class for authentication operations."""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.
        For passwords longer than 72 bytes, pre-hash with SHA256.

        Args:
            password: Plain text password

        Returns:
            str: Hashed password
        """
        # If password is too long for bcrypt (>72 bytes), pre-hash with SHA256
        if len(password.encode('utf-8')) > 72:
            password = hashlib.sha256(password.encode('utf-8')).hexdigest()

        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        For passwords longer than 72 bytes, pre-hash with SHA256.

        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password from database

        Returns:
            bool: True if password matches, False otherwise
        """
        # If password is too long for bcrypt (>72 bytes), pre-hash with SHA256
        if len(plain_password.encode('utf-8')) > 72:
            plain_password = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()

        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(user_id: int) -> tuple[str, int]:
        """
        Create a JWT access token for a user.

        Args:
            user_id: User ID to encode in token

        Returns:
            tuple: (access_token, expires_in_seconds)
        """
        expires_delta = timedelta(hours=settings.jwt_expiration_hours)
        expire = datetime.utcnow() + expires_delta

        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow()
        }

        access_token = jwt.encode(
            to_encode,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )

        expires_in = int(expires_delta.total_seconds())

        return access_token, expires_in

    @staticmethod
    def register_user(
        db: Session,
        user_data: UserRegisterRequest
    ) -> tuple[User, TokenResponse]:
        """
        Register a new user.

        Args:
            db: Database session
            user_data: User registration data

        Returns:
            tuple: (User object, TokenResponse)

        Raises:
            HTTPException: If username or email already exists
        """
        logger.info(f"Attempting to register user: {user_data.username}")

        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.username == user_data.username) |
            (User.email == user_data.email)
        ).first()

        if existing_user:
            if existing_user.username == user_data.username:
                logger.warning(f"Registration failed: username '{user_data.username}' already exists")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already registered"
                )
            else:
                logger.warning(f"Registration failed: email '{user_data.email}' already exists")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

        # Create new user
        try:
            hashed_password = AuthService.hash_password(user_data.password)

            new_user = User(
                username=user_data.username,
                email=user_data.email,
                password_hash=hashed_password
            )

            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            logger.info(f"User registered successfully: {new_user.username} (ID: {new_user.id})")

            # Generate JWT token
            access_token, expires_in = AuthService.create_access_token(new_user.id)

            token_response = TokenResponse(
                access_token=access_token,
                token_type="bearer",
                expires_in=expires_in
            )

            return new_user, token_response

        except IntegrityError as e:
            db.rollback()
            logger.error(f"Database integrity error during registration: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User registration failed due to database constraint"
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error during registration: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred during registration"
            )

    @staticmethod
    def login_user(
        db: Session,
        login_data: UserLoginRequest
    ) -> tuple[User, TokenResponse]:
        """
        Authenticate a user and generate JWT token.

        Args:
            db: Database session
            login_data: User login credentials

        Returns:
            tuple: (User object, TokenResponse)

        Raises:
            HTTPException: If credentials are invalid
        """
        logger.info(f"Login attempt for: {login_data.username}")

        # Find user by username or email
        user = db.query(User).filter(
            (User.username == login_data.username.lower()) |
            (User.email == login_data.username.lower())
        ).first()

        if not user:
            logger.warning(f"Login failed: user '{login_data.username}' not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )

        # Verify password
        if not AuthService.verify_password(login_data.password, user.password_hash):
            logger.warning(f"Login failed: invalid password for user '{login_data.username}'")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )

        logger.info(f"User logged in successfully: {user.username} (ID: {user.id})")

        # Generate JWT token
        access_token, expires_in = AuthService.create_access_token(user.id)

        token_response = TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in
        )

        return user, token_response

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """
        Retrieve a user by ID.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            User object or None if not found
        """
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """
        Retrieve a user by username.

        Args:
            db: Database session
            username: Username

        Returns:
            User object or None if not found
        """
        return db.query(User).filter(User.username == username.lower()).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """
        Retrieve a user by email.

        Args:
            db: Database session
            email: Email address

        Returns:
            User object or None if not found
        """
        return db.query(User).filter(User.email == email.lower()).first()
