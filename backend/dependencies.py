"""
FastAPI dependencies for dependency injection.
Provides common dependencies like database sessions and authentication.
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database.session import SessionLocal


# HTTP Bearer token security scheme
security = HTTPBearer()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.
    Automatically closes the session after the request.

    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> int:
    """
    Dependency that extracts and validates the current user from JWT token.

    Args:
        credentials: HTTP Bearer credentials containing JWT token
        db: Database session

    Returns:
        int: User ID from the JWT token

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode JWT token
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )

        # Extract user_id from token
        user_id: Optional[int] = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        return int(user_id)

    except JWTError:
        raise credentials_exception
    except ValueError:
        raise credentials_exception


async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Dependency that retrieves the full user object from the database.

    Args:
        user_id: Current user ID from JWT token
        db: Database session

    Returns:
        User: User object from database

    Raises:
        HTTPException: If user not found in database
    """
    from backend.auth.models import User

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user
