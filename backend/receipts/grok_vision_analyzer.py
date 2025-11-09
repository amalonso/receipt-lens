"""
xAI Grok Vision analyzer for receipt image processing.
Uses xAI's Grok Vision API to extract structured data from receipt images.
"""

import logging
import json
from typing import Optional

from openai import AsyncOpenAI

from backend.config import settings
from backend.receipts.schemas import ClaudeAnalysisResponse
from backend.receipts.vision_analyzer import VisionAnalyzer, VisionAnalyzerError

logger = logging.getLogger(__name__)


class GrokVisionAnalyzer(VisionAnalyzer):
    """Service for analyzing receipt images using xAI Grok Vision."""

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
- Si no puedes leer la fecha, usa "0000-00-00"
- Normaliza nombres de productos (ej: "CERV MAHOU" → "Cerveza Mahou")
- Asegúrate que la suma de items coincida con total_amount
- Devuelve SOLO el objeto JSON, sin texto adicional
- Si no puedes leer algún campo, usa valores por defecto razonables"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Grok Vision analyzer.

        Args:
            api_key: xAI API key (defaults to settings.xai_api_key)
        """
        super().__init__(api_key)
        self.api_key = api_key or getattr(settings, 'xai_api_key', None)
        if not self.api_key:
            raise VisionAnalyzerError("xAI API key is required")

        # xAI is OpenAI-compatible, so we use AsyncOpenAI with custom base_url
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://api.x.ai/v1"
        )
        self.model = "grok-2-vision-1212"  # Latest Grok Vision model
        logger.info(f"Grok Vision analyzer initialized with model: {self.model}")

    def _parse_grok_response(self, response_text: str) -> ClaudeAnalysisResponse:
        """
        Parse Grok's JSON response into structured data.

        Args:
            response_text: Raw text response from Grok

        Returns:
            ClaudeAnalysisResponse object

        Raises:
            VisionAnalyzerError: If response cannot be parsed
        """
        try:
            # Try to extract JSON from response (in case Grok adds extra text)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                raise VisionAnalyzerError("No JSON object found in Grok's response")

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
            raise VisionAnalyzerError(f"Invalid JSON response from Grok: {str(e)}")

        except Exception as e:
            logger.error(f"Error parsing Grok response: {str(e)}")
            raise VisionAnalyzerError(f"Failed to parse response: {str(e)}")

    async def analyze_receipt(
        self,
        image_path: str,
        max_tokens: int = 2048
    ) -> ClaudeAnalysisResponse:
        """
        Analyze a receipt image using xAI Grok Vision.

        Args:
            image_path: Path to the receipt image file
            max_tokens: Maximum tokens for Grok's response

        Returns:
            ClaudeAnalysisResponse with extracted data

        Raises:
            VisionAnalyzerError: If analysis fails
        """
        logger.info(f"Starting receipt analysis with Grok Vision: {image_path}")

        try:
            # Encode image
            image_data, media_type = self._encode_image(image_path)

            # Call Grok API (OpenAI-compatible)
            logger.info("Sending request to xAI Grok API...")
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{media_type};base64,{image_data}",
                                    "detail": "high"  # High detail for better OCR
                                }
                            },
                            {
                                "type": "text",
                                "text": self.ANALYSIS_PROMPT
                            }
                        ]
                    }
                ],
                max_tokens=max_tokens
            )

            # Extract response text
            response_text = response.choices[0].message.content
            logger.debug(f"Grok response: {response_text[:200]}...")

            # Parse response
            analysis = self._parse_grok_response(response_text)

            logger.info(f"Receipt analysis completed successfully with Grok Vision")
            return analysis

        except Exception as e:
            if isinstance(e, VisionAnalyzerError):
                raise
            logger.error(f"Grok API error: {str(e)}")
            raise VisionAnalyzerError(f"Grok API error: {str(e)}")
