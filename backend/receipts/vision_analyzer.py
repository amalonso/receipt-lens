"""
Base abstract class for vision analyzers.
Defines the interface that all vision API providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple
from pathlib import Path
import base64
import logging

from backend.receipts.schemas import ClaudeAnalysisResponse

logger = logging.getLogger(__name__)


class VisionAnalyzerError(Exception):
    """Custom exception for vision analyzer errors."""
    pass


class VisionAnalyzer(ABC):
    """
    Abstract base class for receipt image analyzers.
    All vision API providers must implement this interface.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the vision analyzer.

        Args:
            api_key: API key for the vision service
        """
        self.api_key = api_key
        logger.info(f"Initialized {self.__class__.__name__}")

    @abstractmethod
    async def analyze_receipt(
        self,
        image_path: str,
        max_tokens: int = 2048
    ) -> ClaudeAnalysisResponse:
        """
        Analyze a receipt image and extract structured data.

        Args:
            image_path: Path to the receipt image file
            max_tokens: Maximum tokens for response (provider-specific)

        Returns:
            ClaudeAnalysisResponse with extracted data

        Raises:
            VisionAnalyzerError: If analysis fails
        """
        pass

    def _encode_image(self, image_path: str) -> Tuple[str, str]:
        """
        Encode image to base64 and determine media type.

        Args:
            image_path: Path to the image file

        Returns:
            Tuple of (base64_data, media_type)

        Raises:
            VisionAnalyzerError: If image cannot be read or encoded
        """
        try:
            path = Path(image_path)
            if not path.exists():
                raise VisionAnalyzerError(f"Image file not found: {image_path}")

            # Determine media type from extension
            extension = path.suffix.lower()
            media_type_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.webp': 'image/webp',
                '.gif': 'image/gif'
            }

            media_type = media_type_map.get(extension)
            if not media_type:
                raise VisionAnalyzerError(f"Unsupported image format: {extension}")

            # Read and encode image
            with open(image_path, 'rb') as image_file:
                image_data = base64.standard_b64encode(image_file.read()).decode('utf-8')

            logger.debug(f"Encoded image: {path.name} ({media_type})")
            return image_data, media_type

        except Exception as e:
            logger.error(f"Error encoding image: {str(e)}")
            raise VisionAnalyzerError(f"Failed to encode image: {str(e)}")

    def _read_image_bytes(self, image_path: str) -> bytes:
        """
        Read image file as bytes.

        Args:
            image_path: Path to the image file

        Returns:
            Image data as bytes

        Raises:
            VisionAnalyzerError: If image cannot be read
        """
        try:
            path = Path(image_path)
            if not path.exists():
                raise VisionAnalyzerError(f"Image file not found: {image_path}")

            with open(image_path, 'rb') as image_file:
                return image_file.read()

        except Exception as e:
            logger.error(f"Error reading image: {str(e)}")
            raise VisionAnalyzerError(f"Failed to read image: {str(e)}")

    def validate_analysis(self, analysis: ClaudeAnalysisResponse) -> bool:
        """
        Validate that the analysis results are consistent.

        Args:
            analysis: Parsed analysis response

        Returns:
            True if validation passes

        Raises:
            VisionAnalyzerError: If validation fails
        """
        # Calculate sum of item totals
        items_total = sum(item.total_price for item in analysis.items)

        # Allow for small rounding differences (±0.10)
        difference = abs(items_total - analysis.total_amount)

        if difference > 0.10:
            logger.warning(
                f"Total amount mismatch: items={items_total:.2f}, "
                f"total={analysis.total_amount:.2f}, "
                f"difference={difference:.2f}"
            )
            # Don't raise error, just log warning
            # Some receipts may have discounts or taxes not itemized

        # Validate required fields
        if not analysis.store_name:
            raise VisionAnalyzerError("Store name is required")

        if not analysis.items:
            raise VisionAnalyzerError("At least one item is required")

        if analysis.total_amount <= 0:
            raise VisionAnalyzerError("Total amount must be positive")

        logger.info("Analysis validation passed")
        return True
