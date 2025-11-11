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
    items_count: int = Field(default=0, description="Number of items extracted from the receipt")

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

        Validates that the date is a real calendar date using datetime.strptime.
        The service layer has fallback logic to use today's date if needed.
        """
        if not v:
            raise ValueError('Date cannot be empty')

        try:
            # Validate using datetime.strptime for proper date validation
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')


class ReceiptUpdateRequest(BaseModel):
    """Schema for updating a receipt."""

    store_name: Optional[str] = Field(None, description="Store name")

    class Config:
        from_attributes = True


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


class ReceiptReviewDataResponse(BaseModel):
    """Response schema for receipt review data."""

    id: int
    receipt_id: int
    image_path: str
    analyzer_used: str
    analysis_response: str  # JSON string
    reported: bool
    report_message: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReceiptReviewListItem(BaseModel):
    """Schema for receipt review data in list view."""

    id: int
    receipt_id: int
    analyzer_used: str
    reported: bool
    created_at: datetime
    # Receipt information
    store_name: str
    purchase_date: date
    total_amount: float

    class Config:
        from_attributes = True


class ReceiptReviewListResponse(BaseModel):
    """Paginated list of receipt review data."""

    reviews: List[ReceiptReviewListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class ReportReceiptRequest(BaseModel):
    """Request schema for reporting a problematic receipt."""

    message: Optional[str] = Field(None, description="Optional message describing the issue")

    class Config:
        from_attributes = True


class TestAnalyzerRequest(BaseModel):
    """Request schema for testing an analyzer on a receipt."""

    analyzer_name: str = Field(..., description="Name of the analyzer to test (claude, openai, google_vision, etc.)")

    class Config:
        from_attributes = True


class TestAnalyzerResponse(BaseModel):
    """Response schema for analyzer test results."""

    success: bool
    analyzer_name: str
    analysis_response: Optional[str] = None  # JSON string
    error: Optional[str] = None
    processing_time_ms: Optional[int] = None

    class Config:
        from_attributes = True
