"""
Pydantic schemas for receipt request/response validation.
"""

from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from decimal import Decimal


class ItemSchema(BaseModel):
    """Schema for a single item from a receipt."""

    product_name: str = Field(..., description="Name of the product")
    category: str = Field(..., description="Product category")
    quantity: float = Field(default=1.0, description="Quantity purchased")
    unit_price: Optional[float] = Field(None, description="Price per unit")
    total_price: float = Field(..., description="Total price for this item")

    @validator('category')
    def validate_category(cls, v: str) -> str:
        """Validate category is one of the allowed values."""
        allowed_categories = [
            'bebidas', 'carne', 'verduras', 'lácteos',
            'panadería', 'limpieza', 'ocio', 'otros'
        ]
        if v.lower() not in allowed_categories:
            return 'otros'
        return v.lower()

    class Config:
        from_attributes = True


class ReceiptUploadResponse(BaseModel):
    """Response schema after uploading a receipt."""

    id: int
    store_name: str
    purchase_date: date
    total_amount: float
    image_path: str
    processed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ReceiptDetailResponse(BaseModel):
    """Detailed receipt response including items."""

    id: int
    user_id: int
    store_name: str
    purchase_date: date
    total_amount: float
    image_path: str
    processed: bool
    created_at: datetime
    items: List[ItemSchema] = []

    class Config:
        from_attributes = True


class ReceiptListItem(BaseModel):
    """Schema for receipt in list view."""

    id: int
    store_name: str
    purchase_date: date
    total_amount: float
    processed: bool
    item_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class ReceiptListResponse(BaseModel):
    """Paginated list of receipts."""

    receipts: List[ReceiptListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class ClaudeAnalysisRequest(BaseModel):
    """Schema for Claude AI analysis request."""

    store_name: str
    purchase_date: str  # YYYY-MM-DD format
    items: List[ItemSchema]
    total_amount: float


class ClaudeAnalysisResponse(BaseModel):
    """Schema for Claude AI analysis response."""

    store_name: str
    purchase_date: str
    items: List[ItemSchema]
    total_amount: float

    @validator('purchase_date')
    def validate_date_format(cls, v: str) -> str:
        """
        Validate date is in YYYY-MM-DD format.

        Accepts invalid dates like '0000-00-00' which will be handled by
        the service layer with fallback to today's date.
        """
        if not v:
            raise ValueError('Date cannot be empty')

        # Check basic format (YYYY-MM-DD pattern)
        parts = v.split('-')
        if len(parts) != 3:
            raise ValueError('Date must be in YYYY-MM-DD format')

        try:
            # Validate each part is numeric
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])

            # Check basic ranges (allow 0000-00-00 as placeholder for missing date)
            if not (0 <= year <= 9999):
                raise ValueError('Year must be between 0000 and 9999')
            if not (0 <= month <= 12):
                raise ValueError('Month must be between 00 and 12')
            if not (0 <= day <= 31):
                raise ValueError('Day must be between 00 and 31')

            # Format back to ensure consistent YYYY-MM-DD format
            return f"{year:04d}-{month:02d}-{day:02d}"

        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError('Date must be in YYYY-MM-DD format with numeric values')
            raise


class ReceiptResponse(BaseModel):
    """Standard receipt response wrapper."""

    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


class UploadStats(BaseModel):
    """Statistics about uploaded receipts."""

    total_receipts: int
    processed_receipts: int
    total_items: int
    total_spent: float
    stores_count: int
