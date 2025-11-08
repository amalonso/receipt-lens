"""
OCR.space API analyzer for receipt image processing.
Uses OCR.space free API to extract structured data from receipt images.
"""

import logging
import json
import aiohttp
from typing import Optional
from datetime import datetime, date
import re

from backend.config import settings
from backend.receipts.schemas import ClaudeAnalysisResponse, ItemSchema
from backend.receipts.vision_analyzer import VisionAnalyzer, VisionAnalyzerError

logger = logging.getLogger(__name__)


class OCRSpaceAnalyzer(VisionAnalyzer):
    """Service for analyzing receipt images using OCR.space API."""

    API_URL = "https://api.ocr.space/parse/image"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OCR.space analyzer.

        Args:
            api_key: OCR.space API key (defaults to settings.ocrspace_api_key)
        """
        super().__init__(api_key)
        self.api_key = api_key or getattr(settings, 'ocrspace_api_key', 'helloworld')
        logger.info("OCR.space analyzer initialized")

    def _parse_receipt_text(self, text: str) -> ClaudeAnalysisResponse:
        """
        Parse extracted text into structured receipt data.
        Uses basic heuristics to extract information.

        Args:
            text: Raw text extracted from receipt

        Returns:
            ClaudeAnalysisResponse with extracted data

        Raises:
            VisionAnalyzerError: If parsing fails
        """
        try:
            lines = [line.strip() for line in text.split('\n') if line.strip()]

            # Initialize default values
            store_name = "Unknown Store"
            purchase_date = date.today().strftime('%Y-%m-%d')
            total_amount = 0.0
            items = []

            # Try to extract store name (usually first few lines)
            if lines:
                store_name = lines[0]

            # Try to find total amount (look for common patterns)
            for line in lines:
                line_upper = line.upper()
                if any(keyword in line_upper for keyword in ['TOTAL', 'SUMA', 'IMPORTE', 'PAGAR']):
                    # Try to extract number
                    numbers = re.findall(r'\d+[.,]\d{2}', line)
                    if numbers:
                        total_str = numbers[-1].replace(',', '.')
                        total_amount = float(total_str)
                        break

            # Try to find date
            date_pattern = r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
            for line in lines:
                date_match = re.search(date_pattern, line)
                if date_match:
                    date_str = date_match.group()
                    # Try to parse date
                    try:
                        for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y']:
                            try:
                                parsed_date = datetime.strptime(date_str, fmt)
                                purchase_date = parsed_date.strftime('%Y-%m-%d')
                                break
                            except ValueError:
                                continue
                    except:
                        pass
                    break

            # Create at least one item with the total
            if total_amount > 0:
                items.append(ItemSchema(
                    product_name="Items from receipt",
                    category="otros",
                    quantity=1.0,
                    unit_price=total_amount,
                    total_price=total_amount
                ))
            else:
                # If no total found, create a placeholder
                items.append(ItemSchema(
                    product_name="Unknown items",
                    category="otros",
                    quantity=1.0,
                    unit_price=0.0,
                    total_price=0.0
                ))

            return ClaudeAnalysisResponse(
                store_name=store_name,
                purchase_date=purchase_date,
                items=items,
                total_amount=total_amount
            )

        except Exception as e:
            logger.error(f"Error parsing receipt text: {str(e)}")
            raise VisionAnalyzerError(f"Failed to parse receipt data: {str(e)}")

    async def analyze_receipt(
        self,
        image_path: str,
        max_tokens: int = 2048
    ) -> ClaudeAnalysisResponse:
        """
        Analyze a receipt image using OCR.space API.

        Args:
            image_path: Path to the receipt image file
            max_tokens: Not used for OCR.space (kept for interface compatibility)

        Returns:
            ClaudeAnalysisResponse with extracted data

        Raises:
            VisionAnalyzerError: If analysis fails
        """
        logger.info(f"Starting receipt analysis with OCR.space: {image_path}")

        try:
            # Prepare the file
            with open(image_path, 'rb') as f:
                image_data = f.read()

            # Prepare the request
            payload = {
                'apikey': self.api_key,
                'language': 'spa',  # Spanish
                'isOverlayRequired': False,
                'detectOrientation': True,
                'scale': True,
                'OCREngine': 2,  # Engine 2 is generally better
            }

            files = {
                'file': image_data
            }

            # Make async HTTP request
            logger.info("Sending request to OCR.space API...")
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.API_URL,
                    data=payload,
                    files=files if isinstance(files, dict) else None
                ) as response:
                    if response.status != 200:
                        raise VisionAnalyzerError(
                            f"OCR.space API returned status {response.status}"
                        )

                    result = await response.json()

            # Check for errors
            if result.get('IsErroredOnProcessing'):
                error_msg = result.get('ErrorMessage', ['Unknown error'])[0]
                raise VisionAnalyzerError(f"OCR.space error: {error_msg}")

            # Extract text
            parsed_results = result.get('ParsedResults', [])
            if not parsed_results:
                raise VisionAnalyzerError("No text detected in image")

            full_text = parsed_results[0].get('ParsedText', '')
            if not full_text:
                raise VisionAnalyzerError("No text extracted from image")

            logger.debug(f"Extracted text: {full_text[:200]}...")

            # Parse the text into structured data
            analysis = self._parse_receipt_text(full_text)

            logger.info(f"Receipt analysis completed successfully")
            return analysis

        except Exception as e:
            if isinstance(e, VisionAnalyzerError):
                raise
            logger.error(f"Unexpected error during analysis: {str(e)}")
            raise VisionAnalyzerError(f"Analysis failed: {str(e)}")
