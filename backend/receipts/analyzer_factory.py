"""
Factory for creating vision analyzer instances.
Provides a centralized way to instantiate the correct analyzer based on configuration.
"""

import logging
from typing import Optional
from enum import Enum

from backend.config import settings
from backend.receipts.vision_analyzer import VisionAnalyzer, VisionAnalyzerError
from backend.receipts.claude_analyzer import ClaudeReceiptAnalyzer
from backend.receipts.google_vision_analyzer import GoogleVisionAnalyzer
from backend.receipts.ocrspace_analyzer import OCRSpaceAnalyzer
from backend.receipts.openai_vision_analyzer import OpenAIVisionAnalyzer

logger = logging.getLogger(__name__)


class VisionProvider(str, Enum):
    """Supported vision API providers."""
    CLAUDE = "claude"
    GOOGLE_VISION = "google_vision"
    OCR_SPACE = "ocrspace"
    OPENAI = "openai"


class AnalyzerFactory:
    """
    Factory class for creating vision analyzer instances.
    """

    # Cache analyzer instances (singleton pattern)
    _analyzers: dict[str, VisionAnalyzer] = {}

    @staticmethod
    def create_analyzer(
        provider: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> VisionAnalyzer:
        """
        Create or retrieve a vision analyzer instance.

        Args:
            provider: Vision provider name (defaults to settings.vision_provider)
            api_key: API key for the provider (optional, uses settings if not provided)

        Returns:
            VisionAnalyzer instance

        Raises:
            VisionAnalyzerError: If provider is invalid or not configured
        """
        # Use configured provider if not specified
        provider = provider or getattr(settings, 'vision_provider', 'claude')
        provider = provider.lower()

        # Check cache
        cache_key = f"{provider}:{api_key or 'default'}"
        if cache_key in AnalyzerFactory._analyzers:
            logger.debug(f"Returning cached analyzer for provider: {provider}")
            return AnalyzerFactory._analyzers[cache_key]

        # Create new analyzer
        logger.info(f"Creating new analyzer for provider: {provider}")

        try:
            if provider == VisionProvider.CLAUDE:
                analyzer = ClaudeReceiptAnalyzer(api_key=api_key)

            elif provider == VisionProvider.GOOGLE_VISION:
                # For Google Vision, use credentials path from settings if not explicitly provided
                credentials_path = api_key or settings.google_vision_credentials
                if not credentials_path:
                    raise VisionAnalyzerError(
                        "Google Vision credentials not configured. "
                        "Set GOOGLE_VISION_CREDENTIALS in .env file."
                    )
                analyzer = GoogleVisionAnalyzer(api_key=credentials_path)

            elif provider == VisionProvider.OCR_SPACE:
                analyzer = OCRSpaceAnalyzer(api_key=api_key)

            elif provider == VisionProvider.OPENAI:
                analyzer = OpenAIVisionAnalyzer(api_key=api_key)

            else:
                raise VisionAnalyzerError(
                    f"Unknown vision provider: {provider}. "
                    f"Supported providers: {', '.join([p.value for p in VisionProvider])}"
                )

            # Cache the analyzer
            AnalyzerFactory._analyzers[cache_key] = analyzer
            logger.info(f"Successfully created analyzer for provider: {provider}")

            return analyzer

        except Exception as e:
            logger.error(f"Failed to create analyzer for provider {provider}: {str(e)}")
            raise VisionAnalyzerError(f"Failed to create analyzer: {str(e)}")

    @staticmethod
    def get_default_analyzer() -> VisionAnalyzer:
        """
        Get the default analyzer based on configuration.

        Returns:
            VisionAnalyzer instance
        """
        return AnalyzerFactory.create_analyzer()

    @staticmethod
    def clear_cache():
        """Clear the analyzer cache."""
        AnalyzerFactory._analyzers.clear()
        logger.info("Analyzer cache cleared")

    @staticmethod
    def list_providers() -> list[str]:
        """
        List all supported vision providers.

        Returns:
            List of provider names
        """
        return [provider.value for provider in VisionProvider]


# Convenience function for backward compatibility
def get_analyzer() -> VisionAnalyzer:
    """
    Get the default vision analyzer instance.

    Returns:
        VisionAnalyzer instance based on configuration
    """
    return AnalyzerFactory.get_default_analyzer()
