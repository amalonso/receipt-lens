"""
Analytics router with FastAPI endpoints.
Handles monthly summaries, store comparisons, and price tracking.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.dependencies import get_db, get_current_user
from backend.auth.models import User
from backend.analytics.service import AnalyticsService
from backend.analytics.schemas import (
    AnalyticsResponse,
    MonthlySummaryResponse,
    StoreComparisonResponse,
    PriceEvolutionResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/monthly-summary",
    response_model=AnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get monthly spending summary",
    description="Get detailed spending analytics for a specific month"
)
async def get_monthly_summary(
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    year: int = Query(..., ge=2000, description="Year"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get monthly spending summary with category breakdown and top products.

    - **month**: Month number (1-12)
    - **year**: Year

    Returns:
    - Total spent in the month
    - Number of receipts and items
    - Spending breakdown by category
    - Top 10 most purchased products
    - Average receipt amount
    - List of stores visited
    """
    logger.info(f"GET /api/analytics/monthly-summary - user: {current_user.id}, {year}-{month:02d}")

    try:
        summary = AnalyticsService.get_monthly_summary(
            db,
            current_user.id,
            month,
            year
        )

        return {
            "success": True,
            "data": summary.dict(),
            "error": None
        }

    except Exception as e:
        logger.error(f"Monthly summary error: {str(e)}")
        raise


@router.get(
    "/store-comparison",
    response_model=AnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare stores by price",
    description="Compare prices and deals across different stores"
)
async def get_store_comparison(
    months: int = Query(6, ge=1, le=24, description="Number of months to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Compare prices across different stores.

    - **months**: Number of months to analyze (default 6, max 24)

    Returns for each store:
    - Total spent and visit count
    - Average receipt amount
    - Price index (100 = average, >100 = more expensive, <100 = cheaper)
    - Best deals (products cheaper than average)
    - Worst deals (products more expensive than average)

    Stores are sorted by price index (cheapest first).
    """
    logger.info(f"GET /api/analytics/store-comparison - user: {current_user.id}, months: {months}")

    try:
        comparison = AnalyticsService.get_store_comparison(
            db,
            current_user.id,
            months
        )

        return {
            "success": True,
            "data": comparison.dict(),
            "error": None
        }

    except Exception as e:
        logger.error(f"Store comparison error: {str(e)}")
        raise


@router.get(
    "/price-evolution",
    response_model=AnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Track product price evolution",
    description="Track how a product's price changes over time across different stores"
)
async def get_price_evolution(
    product: str = Query(..., min_length=2, description="Product name to track"),
    months: int = Query(6, ge=1, le=24, description="Number of months to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Track price evolution of a specific product over time.

    - **product**: Product name (partial match supported)
    - **months**: Number of months to analyze (default 6, max 24)

    Returns:
    - Price history by store
    - Average, minimum, and maximum prices per store
    - Price trend (increasing, decreasing, stable)
    - Best and worst stores for this product
    - Total number of purchases

    Stores are sorted by average price (cheapest first).
    """
    logger.info(f"GET /api/analytics/price-evolution - user: {current_user.id}, product: {product}")

    try:
        evolution = AnalyticsService.get_price_evolution(
            db,
            current_user.id,
            product,
            months
        )

        return {
            "success": True,
            "data": evolution.dict(),
            "error": None
        }

    except Exception as e:
        logger.error(f"Price evolution error: {str(e)}")
        raise
