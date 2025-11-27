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
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError
import os

from backend.config import settings
from backend.database.session import engine, init_db

# Configure logging
def configure_logging():
    """Configure application logging with proper levels for all components."""
    # Set root logger level
    root_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=root_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True  # Override any existing configuration
    )

    # Configure SQLAlchemy loggers separately
    db_level = getattr(logging, settings.db_log_level.upper(), logging.WARNING)

    # SQLAlchemy engine logger (connection pool, transactions)
    logging.getLogger('sqlalchemy.engine').setLevel(db_level)

    # SQLAlchemy pool logger (connection pool events)
    logging.getLogger('sqlalchemy.pool').setLevel(db_level)

    # SQLAlchemy dialects logger (SQL dialect specific)
    logging.getLogger('sqlalchemy.dialects').setLevel(db_level)

    # SQLAlchemy orm logger (ORM operations)
    logging.getLogger('sqlalchemy.orm').setLevel(db_level)

    # If db_echo is False, ensure SQLAlchemy doesn't log queries
    if not settings.db_echo:
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

    return logging.getLogger(__name__)

logger = configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Runs on startup and shutdown.
    """
    # Startup
    logger.info("=" * 60)
    logger.info("Starting Receipt Lens application...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"Database logging: {'ENABLED' if settings.db_echo else 'DISABLED'} (level: {settings.db_log_level})")
    logger.info(f"Vision Provider: {settings.vision_provider}")
    logger.info("=" * 60)

    # Validate vision provider configuration
    _validate_vision_config()

    # Initialize database (only in development)
    if settings.environment == "development":
        try:
            logger.info("Initializing database...")
            # Note: In production, use Alembic migrations instead
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")

    # Start background scheduler for periodic tasks
    try:
        from backend.scheduler import start_scheduler
        start_scheduler()
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")

    yield

    # Shutdown
    logger.info("Shutting down Receipt Lens application...")

    # Stop scheduler
    try:
        from backend.scheduler import stop_scheduler
        stop_scheduler()
    except Exception as e:
        logger.error(f"Failed to stop scheduler: {e}")

    engine.dispose()


def _validate_vision_config():
    """Validate vision provider configuration on startup."""
    provider = settings.vision_provider.lower()
    logger.info(f"Validating vision provider configuration for: {provider}")

    if provider == "google_vision":
        credentials_path = settings.google_vision_credentials
        if not credentials_path:
            logger.error(
                "Google Vision selected but GOOGLE_VISION_CREDENTIALS not set in .env file"
            )
            logger.warning(
                "Receipt uploads will fail. Please set GOOGLE_VISION_CREDENTIALS "
                "to the path of your Google Cloud credentials JSON file."
            )
        elif not os.path.exists(credentials_path):
            logger.error(
                f"Google Vision credentials file not found at: {credentials_path}"
            )
            logger.warning(
                f"Receipt uploads will fail. Please ensure the credentials file exists "
                f"and is mounted correctly in Docker. Check docker-compose.yml volumes."
            )
        elif not os.access(credentials_path, os.R_OK):
            logger.error(
                f"Google Vision credentials file is not readable: {credentials_path}"
            )
            logger.warning("Receipt uploads will fail. Please check file permissions.")
        else:
            logger.info(f"Google Vision credentials found at: {credentials_path}")

    elif provider == "claude":
        if not settings.anthropic_api_key:
            logger.warning(
                "Claude (Anthropic) selected but ANTHROPIC_API_KEY not set. "
                "Will attempt to use PaddleOCR fallback if available."
            )
        else:
            logger.info("Anthropic API key configured")

    elif provider == "openai":
        if not settings.openai_api_key:
            logger.error("OpenAI selected but OPENAI_API_KEY not set in .env file")
            logger.warning("Receipt uploads will fail. Please set OPENAI_API_KEY.")
        else:
            logger.info("OpenAI API key configured")

    elif provider == "ocrspace":
        if not settings.ocrspace_api_key or settings.ocrspace_api_key == "helloworld":
            logger.warning(
                "OCR.space is using default 'helloworld' API key. "
                "This may have rate limits. Consider getting your own key."
            )
        else:
            logger.info("OCR.space API key configured")

    logger.info("Vision provider validation complete")


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

    # Convert errors to JSON-serializable format
    errors = []
    for error in exc.errors():
        error_dict = {
            "type": error.get("type"),
            "loc": error.get("loc"),
            "msg": error.get("msg"),
            "input": error.get("input")
        }
        # Convert ValueError context to string if present
        if "ctx" in error and "error" in error["ctx"]:
            error_dict["ctx"] = {"error": str(error["ctx"]["error"])}
        errors.append(error_dict)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "data": None,
            "error": "Validation error",
            "details": errors
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


# Include routers
from backend.auth.router import router as auth_router
from backend.receipts.router import router as receipts_router
from backend.analytics.router import router as analytics_router
from backend.admin.router import router as admin_router

app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(receipts_router, prefix="/api/receipts", tags=["Receipts"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(admin_router)  # Admin router includes its own prefix

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")


# Serve frontend HTML files
@app.get("/{path:path}")
async def serve_frontend(path: str):
    """
    Serve frontend HTML files.
    Falls back to index.html for client-side routing.
    """
    # Skip API routes
    if path.startswith("api/"):
        return JSONResponse(
            status_code=404,
            content={"success": False, "data": None, "error": "Not found"}
        )

    # Serve HTML files
    if path == "" or path == "/":
        path = "index.html"
    elif not path.endswith(".html"):
        path = f"{path}.html"

    file_path = os.path.join("frontend", path)

    if os.path.exists(file_path):
        return FileResponse(file_path)

    # Fall back to index.html for client-side routing
    return FileResponse("frontend/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
