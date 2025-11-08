"""
Receipt Lens - Main FastAPI Application
Self-hosted web system for analyzing grocery receipts using Claude AI.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from backend.config import settings
from backend.database.session import engine, init_db

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Runs on startup and shutdown.
    """
    # Startup
    logger.info("Starting Receipt Lens application...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")

    # Initialize database (only in development)
    if settings.environment == "development":
        try:
            logger.info("Initializing database...")
            # Note: In production, use Alembic migrations instead
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")

    yield

    # Shutdown
    logger.info("Shutting down Receipt Lens application...")
    engine.dispose()


# Create FastAPI application
app = FastAPI(
    title="Receipt Lens API",
    description="Self-hosted system for analyzing grocery receipts using Claude AI",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with a consistent format."""
    logger.warning(f"Validation error on {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "data": None,
            "error": "Validation error",
            "details": exc.errors()
        }
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors."""
    logger.error(f"Database error on {request.url}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "data": None,
            "error": "Database error occurred. Please try again later."
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    logger.error(f"Unexpected error on {request.url}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "data": None,
            "error": "An unexpected error occurred. Please try again later."
        }
    )


# Health check endpoint
@app.get("/api/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify the API is running.

    Returns:
        dict: Health status and timestamp
    """
    logger.info("Health check requested")
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "environment": settings.environment,
            "version": "1.0.0"
        },
        "error": None
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.

    Returns:
        dict: API information
    """
    return {
        "success": True,
        "data": {
            "name": "Receipt Lens API",
            "version": "1.0.0",
            "description": "Self-hosted system for analyzing grocery receipts",
            "docs": "/api/docs" if settings.debug else "disabled in production"
        },
        "error": None
    }


# Mount static files (will be used for frontend)
# app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Include routers
from backend.auth.router import router as auth_router
# from backend.receipts.router import router as receipts_router
# from backend.analytics.router import router as analytics_router

app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
# app.include_router(receipts_router, prefix="/api/receipts", tags=["Receipts"])
# app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
