"""
Pydantic schemas for analytics request/response validation.
"""

from typing import List, Optional
from datetime import date as DateType
from pydantic import BaseModel, Field


class CategorySpending(BaseModel):
    """Schema for spending by category."""

    category: str = Field(..., description="Category name")
    amount: float = Field(..., description="Total amount spent")
    percentage: float = Field(..., description="Percentage of total spending")
    item_count: int = Field(..., description="Number of items in category")


class TopProduct(BaseModel):
    """Schema for top purchased products."""

    product_name: str = Field(..., description="Product name")
    times_purchased: int = Field(..., description="Number of times purchased")
    total_spent: float = Field(..., description="Total amount spent on product")
    avg_price: float = Field(..., description="Average price per purchase")
    stores: List[str] = Field(..., description="Stores where product was purchased")


class MonthlySummaryResponse(BaseModel):
    """Response schema for monthly spending summary."""

    month: int = Field(..., description="Month (1-12)")
    year: int = Field(..., description="Year")
    total_spent: float = Field(..., description="Total amount spent in month")
    receipts_count: int = Field(..., description="Number of receipts in month")
    items_count: int = Field(..., description="Number of items purchased")
    spending_by_category: List[CategorySpending] = Field(
        ...,
        description="Spending breakdown by category"
    )
    top_products: List[TopProduct] = Field(
        ...,
        description="Most frequently purchased products"
    )
    avg_receipt_amount: float = Field(..., description="Average receipt amount")
    stores_visited: List[str] = Field(..., description="List of stores visited")


class StoreDeal(BaseModel):
    """Schema for best/worst deals in a store."""

    product: str = Field(..., description="Product name")
    price: float = Field(..., description="Price in this store")
    avg_price: float = Field(..., description="Average price across all stores")
    difference: float = Field(..., description="Price difference vs average")
    percentage_diff: float = Field(..., description="Percentage difference vs average")


class StoreComparison(BaseModel):
    """Schema for store comparison data."""

    store_name: str = Field(..., description="Store name")
    total_spent: float = Field(..., description="Total amount spent at store")
    visit_count: int = Field(..., description="Number of visits to store")
    avg_receipt_amount: float = Field(..., description="Average receipt amount")
    items_count: int = Field(..., description="Total items purchased")
    price_index: float = Field(
        ...,
        description="Price index (100 = average, >100 = more expensive, <100 = cheaper)"
    )
    best_deals: List[StoreDeal] = Field(..., description="Products cheaper than average")
    worst_deals: List[StoreDeal] = Field(..., description="Products more expensive than average")


class StoreComparisonResponse(BaseModel):
    """Response schema for store comparison."""

    stores: List[StoreComparison] = Field(..., description="Comparison data per store")
    total_stores: int = Field(..., description="Total number of stores")
    overall_avg_price: float = Field(..., description="Overall average price across all stores")


class PricePoint(BaseModel):
    """Schema for a single price point."""

    date: DateType = Field(..., description="Purchase date")
    price: float = Field(..., description="Price at this date")
    store: str = Field(..., description="Store name")
    receipt_id: int = Field(..., description="Receipt ID")


class ProductPriceEvolution(BaseModel):
    """Schema for product price evolution over time."""

    store_name: str = Field(..., description="Store name")
    prices: List[PricePoint] = Field(..., description="Price history")
    avg_price: float = Field(..., description="Average price in this store")
    min_price: float = Field(..., description="Minimum price seen")
    max_price: float = Field(..., description="Maximum price seen")
    price_trend: str = Field(
        ...,
        description="Price trend (increasing, decreasing, stable)"
    )


class PriceEvolutionResponse(BaseModel):
    """Response schema for price evolution."""

    product_name: str = Field(..., description="Product name")
    months: int = Field(..., description="Number of months analyzed")
    by_store: List[ProductPriceEvolution] = Field(
        ...,
        description="Price evolution per store"
    )
    overall_avg_price: float = Field(..., description="Overall average price")
    best_store: Optional[str] = Field(None, description="Store with best average price")
    worst_store: Optional[str] = Field(None, description="Store with worst average price")
    total_purchases: int = Field(..., description="Total number of times purchased")


class AnalyticsResponse(BaseModel):
    """Standard analytics response wrapper."""

    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


class SpendingTrend(BaseModel):
    """Schema for spending trend over time."""

    month: str = Field(..., description="Month in YYYY-MM format")
    total_spent: float = Field(..., description="Total amount spent")
    receipts_count: int = Field(..., description="Number of receipts")
    avg_receipt: float = Field(..., description="Average receipt amount")


class CategoryTrend(BaseModel):
    """Schema for category spending trend."""

    category: str = Field(..., description="Category name")
    months: List[SpendingTrend] = Field(..., description="Monthly data")
    total_spent: float = Field(..., description="Total spent in category")
    avg_monthly: float = Field(..., description="Average monthly spending")
