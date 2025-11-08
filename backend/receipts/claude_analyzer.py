"""
Claude AI analyzer for receipt image processing.
Uses Anthropic's Claude API to extract structured data from receipt images.
"""

import logging
import json
import base64
from typing import Optional, Tuple
from pathlib import Path

from anthropic import Anthropic, APIError
from PIL import Image

from backend.config import settings
from backend.receipts.schemas import ClaudeAnalysisResponse, ItemSchema

logger = logging.getLogger(__name__)


class ClaudeAnalyzerError(Exception):
    """Custom exception for Claude analyzer errors."""
    pass


class ClaudeReceiptAnalyzer:
    """Service for analyzing receipt images using Claude AI."""

    # Prompt template for receipt analysis
    ANALYSIS_PROMPT = """Analiza esta imagen de factura de supermercado y extrae la siguiente información en formato JSON estricto:

{
  "store_name": "nombre del supermercado",
  "purchase_date": "YYYY-MM-DD",
  "items": [
    {
      "product_name": "nombre exacto del producto",
      "category": "una de: bebidas|carne|verduras|lácteos|panadería|limpieza|ocio|otros",
      "quantity": número,
      "unit_price": número con 2 decimales (o null si no disponible),
      "total_price": número con 2 decimales
    }
  ],
  "total_amount": número con 2 decimales
}

Reglas importantes:
- Si no puedes determinar la categoría, usa "otros"
- Si no hay cantidad explícita, usa 1.0
- Normaliza nombres de productos (ej: "CERV MAHOU" → "Cerveza Mahou")
- Asegúrate que la suma de items coincida con total_amount
- Devuelve SOLO el objeto JSON, sin texto adicional
- Si no puedes leer algún campo, usa valores por defecto razonables"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude analyzer.

        Args:
            api_key: Anthropic API key (defaults to settings.anthropic_api_key)
        """
        self.api_key = api_key or settings.anthropic_api_key
        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"  # Claude Sonnet 4
        logger.info(f"Claude analyzer initialized with model: {self.model}")

    def _encode_image(self, image_path: str) -> Tuple[str, str]:
        """
        Encode image to base64 and determine media type.

        Args:
            image_path: Path to the image file

        Returns:
            Tuple of (base64_data, media_type)

        Raises:
            ClaudeAnalyzerError: If image cannot be read or encoded
        """
        try:
            path = Path(image_path)
            if not path.exists():
                raise ClaudeAnalyzerError(f"Image file not found: {image_path}")

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
                raise ClaudeAnalyzerError(f"Unsupported image format: {extension}")

            # Read and encode image
            with open(image_path, 'rb') as image_file:
                image_data = base64.standard_b64encode(image_file.read()).decode('utf-8')

            logger.info(f"Encoded image: {path.name} ({media_type})")
            return image_data, media_type

        except Exception as e:
            logger.error(f"Error encoding image: {str(e)}")
            raise ClaudeAnalyzerError(f"Failed to encode image: {str(e)}")

    def _parse_claude_response(self, response_text: str) -> ClaudeAnalysisResponse:
        """
        Parse Claude's JSON response into structured data.

        Args:
            response_text: Raw text response from Claude

        Returns:
            ClaudeAnalysisResponse object

        Raises:
            ClaudeAnalyzerError: If response cannot be parsed
        """
        try:
            # Try to extract JSON from response (in case Claude adds extra text)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                raise ClaudeAnalyzerError("No JSON object found in Claude's response")

            json_str = response_text[json_start:json_end]
            data = json.loads(json_str)

            # Validate and parse using Pydantic
            analysis = ClaudeAnalysisResponse(**data)

            logger.info(
                f"Parsed receipt: {analysis.store_name}, "
                f"{len(analysis.items)} items, "
                f"total: €{analysis.total_amount}"
            )

            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            logger.debug(f"Response text: {response_text}")
            raise ClaudeAnalyzerError(f"Invalid JSON response from Claude: {str(e)}")

        except Exception as e:
            logger.error(f"Error parsing Claude response: {str(e)}")
            raise ClaudeAnalyzerError(f"Failed to parse response: {str(e)}")

    async def analyze_receipt(
        self,
        image_path: str,
        max_tokens: int = 2048
    ) -> ClaudeAnalysisResponse:
        """
        Analyze a receipt image using Claude AI.

        Args:
            image_path: Path to the receipt image file
            max_tokens: Maximum tokens for Claude's response

        Returns:
            ClaudeAnalysisResponse with extracted data

        Raises:
            ClaudeAnalyzerError: If analysis fails
        """
        logger.info(f"Starting receipt analysis: {image_path}")

        try:
            # Encode image
            image_data, media_type = self._encode_image(image_path)

            # Call Claude API
            logger.info("Sending request to Claude API...")
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": self.ANALYSIS_PROMPT
                            }
                        ],
                    }
                ],
            )

            # Extract response text
            response_text = message.content[0].text
            logger.debug(f"Claude response: {response_text[:200]}...")

            # Parse response
            analysis = self._parse_claude_response(response_text)

            logger.info(f"Receipt analysis completed successfully")
            return analysis

        except APIError as e:
            logger.error(f"Claude API error: {str(e)}")
            raise ClaudeAnalyzerError(f"Claude API error: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error during analysis: {str(e)}")
            raise ClaudeAnalyzerError(f"Analysis failed: {str(e)}")

    def validate_analysis(self, analysis: ClaudeAnalysisResponse) -> bool:
        """
        Validate that the analysis results are consistent.

        Args:
            analysis: Parsed analysis response

        Returns:
            True if validation passes

        Raises:
            ClaudeAnalyzerError: If validation fails
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
            raise ClaudeAnalyzerError("Store name is required")

        if not analysis.items:
            raise ClaudeAnalyzerError("At least one item is required")

        if analysis.total_amount <= 0:
            raise ClaudeAnalyzerError("Total amount must be positive")

        logger.info("Analysis validation passed")
        return True


# Global analyzer instance (lazy initialization)
_analyzer: Optional[ClaudeReceiptAnalyzer] = None


def get_analyzer() -> ClaudeReceiptAnalyzer:
    """
    Get or create the global Claude analyzer instance.

    Returns:
        ClaudeReceiptAnalyzer instance
    """
    global _analyzer
    if _analyzer is None:
        _analyzer = ClaudeReceiptAnalyzer()
    return _analyzer
