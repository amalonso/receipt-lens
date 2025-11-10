"""
Pydantic schemas for admin API request/response validation.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ============ USER MANAGEMENT ============

class UserStatsResponse(BaseModel):
    """User with statistics response schema."""
    id: int
    username: str
    email: str
    is_admin: bool
    is_active: bool
    last_login: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
    total_receipts: int = 0
    total_spending: float = 0.0
    first_purchase: Optional[str] = None
    last_purchase: Optional[str] = None
    unique_stores: int = 0
    total_items: int = 0
    total_api_calls: int = 0
    total_api_cost: float = 0.0


class UsersListResponse(BaseModel):
    """Paginated users list response."""
    users: List[UserStatsResponse]
    total: int
    page: int
    page_size: int


class ToggleUserStatusRequest(BaseModel):
    """Request to toggle user status."""
    pass  # No body needed, user_id comes from path


# ============ DASHBOARD & ANALYTICS ============

class SystemDashboardResponse(BaseModel):
    """System dashboard metrics response."""
    users: Dict[str, Any]
    receipts: Dict[str, Any]
    spending: Dict[str, Any]
    items: Dict[str, Any]
    stores: Dict[str, Any]
    api: Dict[str, Any]


class UsageAnalyticsRequest(BaseModel):
    """Request for usage analytics."""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    group_by: str = Field(default="month", pattern="^(day|week|month)$")


class UsageDataPoint(BaseModel):
    """Single usage data point."""
    user_id: int
    username: str
    email: str
    period: str
    receipts_count: int
    total_spending: float
    items_count: int
    api_calls: int
    api_cost: float


class UsageAnalyticsResponse(BaseModel):
    """Usage analytics response."""
    period: Dict[str, Any]
    summary: Dict[str, Any]
    data: List[UsageDataPoint]


class MonthlySpending(BaseModel):
    """Monthly spending data point."""
    year: int
    month: int
    receipt_count: int
    total_amount: float


class CategorySpending(BaseModel):
    """Category spending data point."""
    category: str
    item_count: int
    total_spent: float


class StoreSpending(BaseModel):
    """Store spending data point."""
    store_name: str
    visit_count: int
    total_spent: float
    avg_receipt: float


class TopProduct(BaseModel):
    """Top product data point."""
    product_name: str
    category: Optional[str]
    purchase_count: int
    total_quantity: float
    total_spent: float
    avg_price: float


class UserAnalyticsResponse(BaseModel):
    """User analytics response."""
    user: Dict[str, Any]
    monthly_spending: List[MonthlySpending]
    category_spending: List[CategorySpending]
    store_spending: List[StoreSpending]
    top_products: List[TopProduct]


class AggregatedMonthlySpending(BaseModel):
    """Aggregated monthly spending data point."""
    year: int
    month: int
    receipt_count: int
    user_count: int
    total_amount: float


class AggregatedCategorySpending(BaseModel):
    """Aggregated category spending data point."""
    category: str
    item_count: int
    user_count: int
    total_spent: float
    avg_price: float


class AggregatedStoreSpending(BaseModel):
    """Aggregated store spending data point."""
    store_name: str
    visit_count: int
    user_count: int
    total_spent: float
    avg_receipt: float


class AggregatedTopProduct(BaseModel):
    """Aggregated top product data point."""
    product_name: str
    category: Optional[str]
    purchase_count: int
    buyer_count: int
    total_quantity: float
    total_spent: float
    avg_price: float
    min_price: float
    max_price: float


class AggregatedAnalyticsResponse(BaseModel):
    """Aggregated analytics response."""
    monthly_spending: List[AggregatedMonthlySpending]
    category_spending: List[AggregatedCategorySpending]
    store_spending: List[AggregatedStoreSpending]
    top_products: List[AggregatedTopProduct]


# ============ CONFIGURATION ============

class SystemConfigResponse(BaseModel):
    """System configuration item response."""
    id: int
    config_key: str
    config_value: str
    value_type: str
    category: Optional[str]
    description: Optional[str]
    is_sensitive: bool
    updated_by: Optional[int]
    updated_at: str
    created_at: str


class UpdateConfigRequest(BaseModel):
    """Request to update configuration."""
    config_value: str = Field(..., min_length=1)


# ============ ACTIVITY LOGS ============

class ActivityLogResponse(BaseModel):
    """Activity log response."""
    id: int
    user_id: Optional[int]
    username: Optional[str] = None
    action: str
    entity_type: Optional[str]
    entity_id: Optional[int]
    details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: str


class ActivityLogsListResponse(BaseModel):
    """Paginated activity logs response."""
    logs: List[ActivityLogResponse]
    total: int
    page: int
    page_size: int


# ============ RECEIPTS (ADMIN VIEW) ============

class ReceiptAdminResponse(BaseModel):
    """Receipt with user info response (admin view)."""
    id: int
    user_id: int
    username: Optional[str]
    user_email: Optional[str]
    store_name: str
    purchase_date: str
    total_amount: float
    image_path: str
    processed: bool
    created_at: str


class ReceiptsListAdminResponse(BaseModel):
    """Paginated receipts list response (admin view)."""
    receipts: List[ReceiptAdminResponse]
    total: int
    page: int
    page_size: int


# ============ API RESPONSE WRAPPER ============

class AdminApiResponse(BaseModel):
    """Generic API response wrapper."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    message: Optional[str] = None
