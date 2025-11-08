"""
Application configuration using Pydantic Settings.
Loads environment variables from .env file.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = Field(
        default="postgresql://admin:changeme@localhost:5432/receipt_lens",
        description="PostgreSQL connection URL"
    )

    # Vision API Configuration
    vision_provider: str = Field(
        default="claude",
        description="Vision API provider: claude|google_vision|ocrspace|openai"
    )

    # API Keys
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key for Claude AI (optional - will use PaddleOCR fallback if not provided)"
    )
    google_vision_credentials: str = Field(
        default="",
        description="Path to Google Cloud Vision credentials JSON file"
    )
    ocrspace_api_key: str = Field(
        default="helloworld",
        description="OCR.space API key (default: helloworld for testing)"
    )
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key for GPT-4o Vision"
    )

    # Security
    jwt_secret_key: str = Field(
        ...,
        description="Secret key for JWT token generation"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="Algorithm for JWT encoding"
    )
    jwt_expiration_hours: int = Field(
        default=24,
        description="JWT token expiration time in hours"
    )

    # Application
    environment: str = Field(
        default="development",
        description="Application environment (development, production)"
    )
    debug: bool = Field(
        default=True,
        description="Debug mode"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )

    # Upload Settings
    max_upload_size_mb: int = Field(
        default=10,
        description="Maximum upload file size in MB"
    )
    upload_dir: str = Field(
        default="/app/uploads",
        description="Directory for uploaded files"
    )
    allowed_extensions: str = Field(
        default="jpg,jpeg,png,pdf",
        description="Comma-separated list of allowed file extensions"
    )

    # Rate Limiting
    upload_rate_limit_per_hour: int = Field(
        default=10,
        description="Maximum number of uploads per user per hour"
    )

    # CORS
    cors_origins: str = Field(
        default="http://localhost:8000",
        description="Comma-separated list of allowed CORS origins"
    )

    @validator('cors_origins')
    def parse_cors_origins(cls, v: str) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in v.split(',')]

    @validator('allowed_extensions')
    def parse_allowed_extensions(cls, v: str) -> List[str]:
        """Parse comma-separated extensions into a list."""
        return [ext.strip().lower() for ext in v.split(',')]

    @validator('vision_provider')
    def validate_vision_provider(cls, v: str) -> str:
        """Validate vision provider value."""
        valid_providers = ['claude', 'google_vision', 'ocrspace', 'openai']
        v = v.lower()
        if v not in valid_providers:
            raise ValueError(
                f"Invalid vision provider: {v}. "
                f"Must be one of: {', '.join(valid_providers)}"
            )
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
