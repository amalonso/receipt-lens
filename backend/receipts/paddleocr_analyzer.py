"""
PaddleOCR analyzer for receipt image processing.
Fallback OCR solution when no external API keys are configured.
Uses PaddleOCR for text extraction and structured parsing.
"""

import logging
import re
from typing import Optional, List, Dict, Tuple
from pathlib import Path
from datetime import datetime, date

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False

from backend.receipts.schemas import ClaudeAnalysisResponse, ItemSchema

logger = logging.getLogger(__name__)


class PaddleOCRAnalyzerError(Exception):
    """Custom exception for PaddleOCR analyzer errors."""
    pass


class PaddleOCRReceiptAnalyzer:
    """Service for analyzing receipt images using PaddleOCR."""

    # Category keywords for classification
    CATEGORY_KEYWORDS = {
        'bebidas': [
            'cerveza', 'cerv', 'vino', 'agua', 'zumo', 'refresco', 'coca cola',
            'pepsi', 'fanta', 'sprite', 'nestea', 'aquarius', 'bebida', 'drink'
        ],
        'carne': [
            'carne', 'pollo', 'cerdo', 'ternera', 'cordero', 'pavo', 'jamon',
            'jamón', 'chorizo', 'salchicha', 'hamburguesa', 'filete', 'bacon'
        ],
        'verduras': [
            'verdura', 'lechuga', 'tomate', 'cebolla', 'patata', 'zanahoria',
            'pepino', 'pimiento', 'calabacin', 'berenjena', 'espinaca', 'fruta',
            'manzana', 'platano', 'naranja', 'pera', 'uva'
        ],
        'lácteos': [
            'leche', 'yogur', 'queso', 'mantequilla', 'nata', 'lacteo'
        ],
        'panadería': [
            'pan', 'barra', 'bollo', 'croissant', 'magdalena', 'galleta',
            'pastel', 'tarta', 'bizcocho'
        ],
        'limpieza': [
            'detergente', 'lavavajillas', 'lejia', 'limpiador', 'papel',
            'servilleta', 'fregona', 'estropajo', 'jabon', 'jabón'
        ],
        'ocio': [
            'revista', 'libro', 'periodico', 'periódico', 'juguete', 'juego'
        ]
    }

    def __init__(self):
        """Initialize PaddleOCR analyzer."""
        if not PADDLEOCR_AVAILABLE:
            raise PaddleOCRAnalyzerError(
                "PaddleOCR is not installed. Install with: pip install paddlepaddle paddleocr"
            )

        try:
            # Initialize PaddleOCR with Spanish and English support
            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang='es',  # Spanish
                show_log=False,
                use_gpu=False  # Force CPU for compatibility
            )
            logger.info("PaddleOCR analyzer initialized (CPU mode)")
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {str(e)}")
            raise PaddleOCRAnalyzerError(f"Initialization failed: {str(e)}")

    def _extract_text_from_image(self, image_path: str) -> List[Tuple[str, float]]:
        """
        Extract text from image using PaddleOCR.

        Args:
            image_path: Path to the image file

        Returns:
            List of tuples (text, confidence)

        Raises:
            PaddleOCRAnalyzerError: If OCR fails
        """
        try:
            path = Path(image_path)
            if not path.exists():
                raise PaddleOCRAnalyzerError(f"Image file not found: {image_path}")

            logger.info(f"Extracting text from: {path.name}")

            # Perform OCR
            result = self.ocr.ocr(str(path), cls=True)

            if not result or not result[0]:
                raise PaddleOCRAnalyzerError("No text detected in image")

            # Extract text and confidence scores
            extracted_texts = []
            for line in result[0]:
                text = line[1][0]  # Text content
                confidence = line[1][1]  # Confidence score
                extracted_texts.append((text, confidence))

            logger.info(f"Extracted {len(extracted_texts)} text segments")
            return extracted_texts

        except Exception as e:
            logger.error(f"OCR extraction error: {str(e)}")
            raise PaddleOCRAnalyzerError(f"Text extraction failed: {str(e)}")

    def _extract_store_name(self, texts: List[Tuple[str, float]]) -> str:
        """
        Extract store name from OCR text (usually first line).

        Args:
            texts: List of (text, confidence) tuples

        Returns:
            Store name or default
        """
        if not texts:
            return "Supermercado Desconocido"

        # Take first line with good confidence as store name
        for text, confidence in texts[:3]:  # Check first 3 lines
            if confidence > 0.7 and len(text) > 3:
                # Clean and normalize
                store_name = text.strip().title()
                logger.info(f"Detected store name: {store_name}")
                return store_name

        return "Supermercado Desconocido"

    def _extract_date(self, texts: List[Tuple[str, float]]) -> date:
        """
        Extract purchase date from OCR text.

        Args:
            texts: List of (text, confidence) tuples

        Returns:
            Purchase date or today's date
        """
        # Common date patterns
        date_patterns = [
            r'(\d{2})[/-](\d{2})[/-](\d{4})',  # DD/MM/YYYY or DD-MM-YYYY
            r'(\d{2})[/-](\d{2})[/-](\d{2})',  # DD/MM/YY or DD-MM-YY
            r'(\d{4})[/-](\d{2})[/-](\d{2})',  # YYYY/MM/DD
        ]

        for text, confidence in texts:
            for pattern in date_patterns:
                match = re.search(pattern, text)
                if match:
                    try:
                        groups = match.groups()
                        if len(groups[0]) == 4:  # YYYY-MM-DD format
                            year, month, day = groups
                        elif len(groups[2]) == 4:  # DD-MM-YYYY format
                            day, month, year = groups
                        else:  # DD-MM-YY format
                            day, month, year = groups
                            year = f"20{year}" if int(year) < 50 else f"19{year}"

                        purchase_date = date(int(year), int(month), int(day))
                        logger.info(f"Detected date: {purchase_date}")
                        return purchase_date
                    except ValueError:
                        continue

        logger.warning("No valid date found, using today")
        return date.today()

    def _classify_product(self, product_name: str) -> str:
        """
        Classify product into category based on keywords.

        Args:
            product_name: Product name

        Returns:
            Category name
        """
        product_lower = product_name.lower()

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in product_lower:
                    return category

        return 'otros'

    def _extract_items_and_total(
        self,
        texts: List[Tuple[str, float]]
    ) -> Tuple[List[ItemSchema], float]:
        """
        Extract line items and total amount from OCR text.

        Args:
            texts: List of (text, confidence) tuples

        Returns:
            Tuple of (items list, total amount)
        """
        items = []
        total_amount = 0.0

        # Patterns for item lines: product name followed by price
        # Examples: "CERVEZA MAHOU 2.50" or "PAN BARRA    1,20"
        price_pattern = r'(\d+[,\.]\d{2})\s*€?$'
        total_patterns = [
            r'total[:\s]*€?\s*(\d+[,\.]\d{2})',
            r'importe[:\s]*€?\s*(\d+[,\.]\d{2})',
            r'suma[:\s]*€?\s*(\d+[,\.]\d{2})'
        ]

        # First pass: find total amount
        for text, confidence in texts:
            text_lower = text.lower()
            for pattern in total_patterns:
                match = re.search(pattern, text_lower)
                if match:
                    total_str = match.group(1).replace(',', '.')
                    total_amount = float(total_str)
                    logger.info(f"Found total amount: €{total_amount}")
                    break

        # Second pass: extract items
        for text, confidence in texts:
            # Skip lines that look like totals or headers
            text_lower = text.lower()
            if any(word in text_lower for word in ['total', 'suma', 'importe', 'ticket', 'factura']):
                continue

            # Look for price at end of line
            price_match = re.search(price_pattern, text)
            if price_match and confidence > 0.6:
                price_str = price_match.group(1).replace(',', '.')
                total_price = float(price_str)

                # Extract product name (everything before the price)
                product_name = text[:price_match.start()].strip()

                # Skip if product name is too short or looks like metadata
                if len(product_name) < 3 or product_name.isdigit():
                    continue

                # Normalize product name
                product_name = ' '.join(product_name.split()).title()

                # Try to extract quantity (default to 1.0)
                quantity = 1.0
                quantity_match = re.match(r'^(\d+)\s+', product_name)
                if quantity_match:
                    quantity = float(quantity_match.group(1))
                    product_name = product_name[quantity_match.end():].strip()

                # Calculate unit price
                unit_price = total_price / quantity if quantity > 0 else total_price

                # Classify category
                category = self._classify_product(product_name)

                item = ItemSchema(
                    product_name=product_name,
                    category=category,
                    quantity=quantity,
                    unit_price=round(unit_price, 2),
                    total_price=round(total_price, 2)
                )
                items.append(item)

        # If no total found, calculate from items
        if total_amount == 0.0 and items:
            total_amount = sum(item.total_price for item in items)
            logger.info(f"Calculated total from items: €{total_amount}")

        # If no items found, create a generic item
        if not items and total_amount > 0:
            items.append(ItemSchema(
                product_name="Compra general",
                category="otros",
                quantity=1.0,
                unit_price=total_amount,
                total_price=total_amount
            ))

        logger.info(f"Extracted {len(items)} items, total: €{total_amount}")
        return items, total_amount

    async def analyze_receipt(self, image_path: str) -> ClaudeAnalysisResponse:
        """
        Analyze a receipt image using PaddleOCR.

        Args:
            image_path: Path to the receipt image file

        Returns:
            ClaudeAnalysisResponse with extracted data

        Raises:
            PaddleOCRAnalyzerError: If analysis fails
        """
        logger.info(f"Starting PaddleOCR receipt analysis: {image_path}")

        try:
            # Extract text from image
            texts = self._extract_text_from_image(image_path)

            # Extract structured data
            store_name = self._extract_store_name(texts)
            purchase_date = self._extract_date(texts)
            items, total_amount = self._extract_items_and_total(texts)

            # Ensure we have at least some data
            if not items:
                raise PaddleOCRAnalyzerError("Could not extract any items from receipt")

            if total_amount <= 0:
                total_amount = sum(item.total_price for item in items)

            # Create response
            analysis = ClaudeAnalysisResponse(
                store_name=store_name,
                purchase_date=purchase_date.strftime('%Y-%m-%d'),
                items=items,
                total_amount=round(total_amount, 2)
            )

            logger.info(f"PaddleOCR analysis completed: {store_name}, {len(items)} items, €{total_amount}")
            return analysis

        except Exception as e:
            logger.error(f"PaddleOCR analysis error: {str(e)}")
            raise PaddleOCRAnalyzerError(f"Analysis failed: {str(e)}")


# Global analyzer instance (lazy initialization)
_paddleocr_analyzer: Optional[PaddleOCRReceiptAnalyzer] = None


def get_paddleocr_analyzer() -> PaddleOCRReceiptAnalyzer:
    """
    Get or create the global PaddleOCR analyzer instance.

    Returns:
        PaddleOCRReceiptAnalyzer instance

    Raises:
        PaddleOCRAnalyzerError: If initialization fails
    """
    global _paddleocr_analyzer
    if _paddleocr_analyzer is None:
        _paddleocr_analyzer = PaddleOCRReceiptAnalyzer()
    return _paddleocr_analyzer


def is_paddleocr_available() -> bool:
    """
    Check if PaddleOCR is available.

    Returns:
        True if PaddleOCR can be used
    """
    return PADDLEOCR_AVAILABLE
