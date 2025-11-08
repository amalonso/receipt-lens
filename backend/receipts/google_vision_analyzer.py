"""
Google Cloud Vision API analyzer for receipt image processing.
Uses Google Cloud Vision API to extract structured data from receipt images.
"""

import logging
import json
import os
from typing import Optional
from datetime import datetime, date

from google.cloud import vision
from google.cloud.vision_v1 import types

from backend.config import settings
from backend.receipts.schemas import ClaudeAnalysisResponse, ItemSchema
from backend.receipts.vision_analyzer import VisionAnalyzer, VisionAnalyzerError

logger = logging.getLogger(__name__)


class GoogleVisionAnalyzer(VisionAnalyzer):
    """Service for analyzing receipt images using Google Cloud Vision API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Google Vision analyzer.

        Args:
            api_key: Google Cloud API key or credentials path
        """
        super().__init__(api_key)
        # If api_key is provided, it should be path to credentials JSON
        if api_key:
            # Validate credentials file exists
            if not os.path.exists(api_key):
                raise VisionAnalyzerError(
                    f"Google Vision credentials file not found at: {api_key}. "
                    f"Please ensure the file exists and is mounted correctly in Docker. "
                    f"Check your .env file and docker-compose.yml volumes configuration."
                )

            # Check if file is readable
            if not os.access(api_key, os.R_OK):
                raise VisionAnalyzerError(
                    f"Google Vision credentials file is not readable: {api_key}. "
                    f"Please check file permissions."
                )

            # Set environment variable for Google Cloud SDK to find credentials
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = api_key
            logger.info(f"Set GOOGLE_APPLICATION_CREDENTIALS to: {api_key}")

            try:
                self.client = vision.ImageAnnotatorClient.from_service_account_json(api_key)
                logger.info("Google Vision client initialized successfully")
            except Exception as e:
                raise VisionAnalyzerError(
                    f"Failed to initialize Google Vision client with credentials at {api_key}: {str(e)}. "
                    f"Please verify the credentials file is valid JSON and contains proper service account credentials."
                )
        else:
            # Use default credentials from environment
            try:
                self.client = vision.ImageAnnotatorClient()
                logger.info("Google Vision client initialized with default credentials")
            except Exception as e:
                raise VisionAnalyzerError(
                    f"Failed to initialize Google Vision client with default credentials: {str(e)}. "
                    f"Please set GOOGLE_VISION_CREDENTIALS in your .env file."
                )
        logger.info("Google Vision analyzer initialized")

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

            logger.debug(f"Parsing receipt text with {len(lines)} lines")
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"First 10 lines: {lines[:10]}")

            # Initialize default values
            store_name = "Unknown Store"
            purchase_date = date.today().strftime('%Y-%m-%d')
            total_amount = 0.0
            items = []

            # Try to extract store name (usually first few lines)
            if lines:
                store_name = lines[0]
                logger.debug(f"Extracted store name: {store_name}")

            # Try to find total amount (look for common patterns)
            import re
            for line in lines:
                line_upper = line.upper()
                # Look for common total keywords in multiple languages
                if any(keyword in line_upper for keyword in [
                    'TOTAL', 'SUMA', 'IMPORTE', 'AMOUNT', 'SUM',
                    'BALANCE', 'GRAND TOTAL', 'SUBTOTAL'
                ]):
                    # Try to extract number - improved regex to handle more formats
                    # Matches: 123.45, 123,45, 1.234,56, 1,234.56, etc.
                    numbers = re.findall(r'\d+[.,]\d+', line)
                    if numbers:
                        # Take the last number on the line (usually the total)
                        total_str = numbers[-1].replace(',', '.')
                        try:
                            total_amount = float(total_str)
                            logger.debug(f"Found total amount {total_amount} from line: {line}")
                            break
                        except ValueError:
                            logger.debug(f"Could not parse number '{total_str}' from line: {line}")
                            continue

            # Try to find date
            import re
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
            # Always create an item even if total is 0 to pass validation
            if total_amount > 0:
                items.append(ItemSchema(
                    product_name="Items from receipt",
                    category="otros",
                    quantity=1.0,
                    unit_price=total_amount,
                    total_price=total_amount
                ))
            else:
                # If we couldn't parse the total, create a placeholder item
                # This allows the receipt to be stored and manually edited later
                logger.warning(
                    f"Could not parse total amount from receipt text. "
                    f"Creating placeholder item. Store: {store_name}"
                )
                items.append(ItemSchema(
                    product_name="Unable to parse receipt details",
                    category="otros",
                    quantity=1.0,
                    unit_price=0.01,  # Small non-zero amount to pass validation
                    total_price=0.01
                ))
                total_amount = 0.01

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
        Analyze a receipt image using Google Cloud Vision API.

        Args:
            image_path: Path to the receipt image file
            max_tokens: Not used for Google Vision (kept for interface compatibility)

        Returns:
            ClaudeAnalysisResponse with extracted data

        Raises:
            VisionAnalyzerError: If analysis fails
        """
        logger.info(f"Starting receipt analysis with Google Vision: {image_path}")

        try:
            # Read image file
            image_bytes = self._read_image_bytes(image_path)

            # Create Image object
            image = types.Image(content=image_bytes)

            # Perform text detection
            logger.info("Sending request to Google Cloud Vision API...")
            response = self.client.text_detection(image=image)

            if response.error.message:
                raise VisionAnalyzerError(
                    f"Google Vision API error: {response.error.message}"
                )

            # Extract text from response
            texts = response.text_annotations
            if not texts:
                raise VisionAnalyzerError("No text detected in image")

            # First annotation contains all text
            full_text = texts[0].description
            logger.info(f"Google Vision extracted {len(full_text)} characters of text")
            logger.debug(f"Extracted text preview: {full_text[:200]}...")

            # Log full text at debug level for troubleshooting
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Full extracted text:\n{full_text}")

            # Parse the text into structured data
            analysis = self._parse_receipt_text(full_text)

            logger.info(f"Receipt analysis completed successfully")
            return analysis

        except Exception as e:
            if isinstance(e, VisionAnalyzerError):
                raise
            logger.error(f"Unexpected error during analysis: {str(e)}")
            raise VisionAnalyzerError(f"Analysis failed: {str(e)}")
