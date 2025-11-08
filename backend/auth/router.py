"""
Authentication router with FastAPI endpoints.
Handles user registration, login, and current user retrieval.
"""

import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.dependencies import get_db, get_current_user
from backend.auth.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    RegisterResponse,
    LoginResponse,
    CurrentUserResponse,
    UserResponse
)
from backend.auth.service import AuthService
from backend.auth.models import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with username, email, and password"
)
async def register(
    user_data: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.

    - **username**: Unique username (3-50 chars, alphanumeric, _, -)
    - **email**: Valid email address
    - **password**: Strong password (min 8 chars, uppercase, lowercase, digit)

    Returns user information and JWT access token.
    """
    logger.info(f"POST /api/auth/register - username: {user_data.username}")

    try:
        user, token = AuthService.register_user(db, user_data)

        return {
            "success": True,
            "data": {
                "user": UserResponse.from_orm(user).dict(),
                "token": token.dict()
            },
            "error": None
        }

    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login user",
    description="Authenticate user with username/email and password"
)
async def login(
    login_data: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate a user and return JWT token.

    - **username**: Username or email address
    - **password**: User password

    Returns user information and JWT access token with 24-hour expiration.
    """
    logger.info(f"POST /api/auth/login - username: {login_data.username}")

    try:
        user, token = AuthService.login_user(db, login_data)

        return {
            "success": True,
            "data": {
                "user": UserResponse.from_orm(user).dict(),
                "token": token.dict()
            },
            "error": None
        }

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Retrieve information about the currently authenticated user"
)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information.

    Requires valid JWT token in Authorization header:
    `Authorization: Bearer <token>`

    Returns user profile information (excluding password).
    """
    logger.info(f"GET /api/auth/me - user_id: {current_user.id}")

    return {
        "success": True,
        "data": UserResponse.from_orm(current_user),
        "error": None
    }
