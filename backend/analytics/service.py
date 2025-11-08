"""
Analytics service with business logic for data analysis.
Handles monthly summaries, store comparisons, and price evolution.
"""

import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from fastapi import HTTPException, status

from backend.receipts.models import Receipt, Item, Category
from backend.analytics.schemas import (
    MonthlySummaryResponse,
    CategorySpending,
    TopProduct,
    StoreComparisonResponse,
    StoreComparison,
    StoreDeal,
    PriceEvolutionResponse,
    ProductPriceEvolution,
    PricePoint
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service class for analytics operations."""

    @staticmethod
    def get_monthly_summary(
        db: Session,
        user_id: int,
        month: int,
        year: int
    ) -> MonthlySummaryResponse:
        """
        Get spending summary for a specific month.

        Args:
            db: Database session
            user_id: User ID
            month: Month (1-12)
            year: Year

        Returns:
            MonthlySummaryResponse with summary data

        Raises:
            HTTPException: If invalid month/year
        """
        logger.info(f"Generating monthly summary for user {user_id}: {year}-{month:02d}")

        # Validate month/year
        if month < 1 or month > 12:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid month. Must be between 1 and 12"
            )

        if year < 2000 or year > datetime.now().year + 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid year"
            )

        # Get receipts for the month
        receipts = db.query(Receipt).filter(
            Receipt.user_id == user_id,
            extract('year', Receipt.purchase_date) == year,
            extract('month', Receipt.purchase_date) == month
        ).all()

        if not receipts:
            logger.info(f"No receipts found for {year}-{month:02d}")
            return MonthlySummaryResponse(
                month=month,
                year=year,
                total_spent=0.0,
                receipts_count=0,
                items_count=0,
                spending_by_category=[],
                top_products=[],
                avg_receipt_amount=0.0,
                stores_visited=[]
            )

        receipt_ids = [r.id for r in receipts]

        # Calculate total spent
        total_spent = sum(float(r.total_amount) for r in receipts)
        receipts_count = len(receipts)
        avg_receipt = total_spent / receipts_count if receipts_count > 0 else 0.0

        # Get all items for these receipts
        items = db.query(Item).filter(Item.receipt_id.in_(receipt_ids)).all()
        items_count = len(items)

        # Calculate spending by category
        category_spending = AnalyticsService._calculate_category_spending(
            db, items, total_spent
        )

        # Calculate top products
        top_products = AnalyticsService._calculate_top_products(db, items, receipt_ids)

        # Get list of stores visited
        stores_visited = list(set(r.store_name for r in receipts))

        logger.info(
            f"Monthly summary: €{total_spent:.2f}, "
            f"{receipts_count} receipts, "
            f"{items_count} items"
        )

        return MonthlySummaryResponse(
            month=month,
            year=year,
            total_spent=total_spent,
            receipts_count=receipts_count,
            items_count=items_count,
            spending_by_category=category_spending,
            top_products=top_products,
            avg_receipt_amount=avg_receipt,
            stores_visited=stores_visited
        )

    @staticmethod
    def _calculate_category_spending(
        db: Session,
        items: List[Item],
        total_spent: float
    ) -> List[CategorySpending]:
        """Calculate spending breakdown by category."""
        category_data = defaultdict(lambda: {'amount': 0.0, 'count': 0})

        for item in items:
            category_name = item.category.name if item.category else "otros"
            category_data[category_name]['amount'] += float(item.total_price)
            category_data[category_name]['count'] += 1

        result = []
        for category, data in category_data.items():
            percentage = (data['amount'] / total_spent * 100) if total_spent > 0 else 0.0
            result.append(CategorySpending(
                category=category,
                amount=data['amount'],
                percentage=round(percentage, 2),
                item_count=data['count']
            ))

        # Sort by amount descending
        result.sort(key=lambda x: x.amount, reverse=True)

        return result

    @staticmethod
    def _calculate_top_products(
        db: Session,
        items: List[Item],
        receipt_ids: List[int]
    ) -> List[TopProduct]:
        """Calculate top purchased products."""
        product_data = defaultdict(lambda: {
            'count': 0,
            'total_spent': 0.0,
            'prices': [],
            'stores': set()
        })

        # Get receipt-store mapping
        receipts = db.query(Receipt).filter(Receipt.id.in_(receipt_ids)).all()
        receipt_store_map = {r.id: r.store_name for r in receipts}

        for item in items:
            product_name = item.product_name
            product_data[product_name]['count'] += 1
            product_data[product_name]['total_spent'] += float(item.total_price)
            product_data[product_name]['prices'].append(float(item.total_price))
            if item.receipt_id in receipt_store_map:
                product_data[product_name]['stores'].add(receipt_store_map[item.receipt_id])

        result = []
        for product, data in product_data.items():
            avg_price = data['total_spent'] / data['count'] if data['count'] > 0 else 0.0
            result.append(TopProduct(
                product_name=product,
                times_purchased=data['count'],
                total_spent=data['total_spent'],
                avg_price=round(avg_price, 2),
                stores=list(data['stores'])
            ))

        # Sort by times purchased, then by total spent
        result.sort(key=lambda x: (x.times_purchased, x.total_spent), reverse=True)

        # Return top 10
        return result[:10]

    @staticmethod
    def get_store_comparison(
        db: Session,
        user_id: int,
        months: int = 6
    ) -> StoreComparisonResponse:
        """
        Compare prices across different stores.

        Args:
            db: Database session
            user_id: User ID
            months: Number of months to analyze (default 6)

        Returns:
            StoreComparisonResponse with comparison data
        """
        logger.info(f"Generating store comparison for user {user_id} (last {months} months)")

        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=months * 30)

        # Get receipts in date range
        receipts = db.query(Receipt).filter(
            Receipt.user_id == user_id,
            Receipt.purchase_date >= start_date,
            Receipt.purchase_date <= end_date
        ).all()

        if not receipts:
            logger.info("No receipts found for store comparison")
            return StoreComparisonResponse(
                stores=[],
                total_stores=0,
                overall_avg_price=0.0
            )

        receipt_ids = [r.id for r in receipts]

        # Group data by store
        store_data = AnalyticsService._group_by_store(db, receipts, receipt_ids)

        # Calculate product average prices across all stores
        product_avg_prices = AnalyticsService._calculate_product_averages(db, receipt_ids)

        # Calculate overall average price
        total_spent = sum(data['total_spent'] for data in store_data.values())
        total_items = sum(data['items_count'] for data in store_data.values())
        overall_avg_price = total_spent / total_items if total_items > 0 else 0.0

        # Generate comparison for each store
        comparisons = []
        for store_name, data in store_data.items():
            comparison = AnalyticsService._generate_store_comparison(
                store_name,
                data,
                product_avg_prices,
                overall_avg_price
            )
            comparisons.append(comparison)

        # Sort by price index (cheapest first)
        comparisons.sort(key=lambda x: x.price_index)

        logger.info(f"Store comparison: {len(comparisons)} stores analyzed")

        return StoreComparisonResponse(
            stores=comparisons,
            total_stores=len(comparisons),
            overall_avg_price=round(overall_avg_price, 2)
        )

    @staticmethod
    def _group_by_store(
        db: Session,
        receipts: List[Receipt],
        receipt_ids: List[int]
    ) -> Dict:
        """Group receipts and items by store."""
        store_data = defaultdict(lambda: {
            'receipts': [],
            'items': [],
            'total_spent': 0.0,
            'items_count': 0
        })

        for receipt in receipts:
            store_data[receipt.store_name]['receipts'].append(receipt)
            store_data[receipt.store_name]['total_spent'] += float(receipt.total_amount)

        # Get items for each store
        items = db.query(Item).filter(Item.receipt_id.in_(receipt_ids)).all()
        receipt_store_map = {r.id: r.store_name for r in receipts}

        for item in items:
            store_name = receipt_store_map.get(item.receipt_id)
            if store_name:
                store_data[store_name]['items'].append(item)
                store_data[store_name]['items_count'] += 1

        return store_data

    @staticmethod
    def _calculate_product_averages(db: Session, receipt_ids: List[int]) -> Dict[str, float]:
        """Calculate average price for each product across all stores."""
        items = db.query(Item).filter(Item.receipt_id.in_(receipt_ids)).all()

        product_prices = defaultdict(list)
        for item in items:
            product_prices[item.product_name].append(float(item.total_price))

        return {
            product: sum(prices) / len(prices)
            for product, prices in product_prices.items()
        }

    @staticmethod
    def _generate_store_comparison(
        store_name: str,
        data: Dict,
        product_avg_prices: Dict[str, float],
        overall_avg: float
    ) -> StoreComparison:
        """Generate comparison data for a single store."""
        total_spent = data['total_spent']
        visit_count = len(data['receipts'])
        items_count = data['items_count']
        avg_receipt = total_spent / visit_count if visit_count > 0 else 0.0

        # Calculate price index (100 = average)
        store_avg = total_spent / items_count if items_count > 0 else 0.0
        price_index = (store_avg / overall_avg * 100) if overall_avg > 0 else 100.0

        # Find best and worst deals
        deals = []
        for item in data['items']:
            product_name = item.product_name
            if product_name in product_avg_prices:
                avg_price = product_avg_prices[product_name]
                item_price = float(item.total_price)
                difference = item_price - avg_price
                percentage_diff = (difference / avg_price * 100) if avg_price > 0 else 0.0

                deals.append(StoreDeal(
                    product=product_name,
                    price=item_price,
                    avg_price=avg_price,
                    difference=round(difference, 2),
                    percentage_diff=round(percentage_diff, 2)
                ))

        # Sort deals
        deals.sort(key=lambda x: x.difference)

        # Get top 5 best and worst deals
        best_deals = [d for d in deals[:5] if d.difference < 0]
        worst_deals = [d for d in deals[-5:] if d.difference > 0]
        worst_deals.reverse()

        return StoreComparison(
            store_name=store_name,
            total_spent=round(total_spent, 2),
            visit_count=visit_count,
            avg_receipt_amount=round(avg_receipt, 2),
            items_count=items_count,
            price_index=round(price_index, 2),
            best_deals=best_deals,
            worst_deals=worst_deals
        )

    @staticmethod
    def get_price_evolution(
        db: Session,
        user_id: int,
        product_name: str,
        months: int = 6
    ) -> PriceEvolutionResponse:
        """
        Track price evolution of a product over time.

        Args:
            db: Database session
            user_id: User ID
            product_name: Product name to track
            months: Number of months to analyze

        Returns:
            PriceEvolutionResponse with price history

        Raises:
            HTTPException: If product not found
        """
        logger.info(f"Tracking price evolution for '{product_name}' (last {months} months)")

        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=months * 30)

        # Find all purchases of this product
        items = db.query(Item, Receipt).join(
            Receipt, Item.receipt_id == Receipt.id
        ).filter(
            Receipt.user_id == user_id,
            Receipt.purchase_date >= start_date,
            Receipt.purchase_date <= end_date,
            Item.product_name.ilike(f"%{product_name}%")
        ).order_by(Receipt.purchase_date).all()

        if not items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No purchases found for product '{product_name}' in the last {months} months"
            )

        # Group by store
        store_data = defaultdict(list)
        all_prices = []

        for item, receipt in items:
            price_point = PricePoint(
                date=receipt.purchase_date,
                price=float(item.total_price),
                store=receipt.store_name,
                receipt_id=receipt.id
            )
            store_data[receipt.store_name].append(price_point)
            all_prices.append(float(item.total_price))

        # Calculate overall average
        overall_avg = sum(all_prices) / len(all_prices) if all_prices else 0.0

        # Generate evolution data per store
        evolutions = []
        for store_name, prices in store_data.items():
            evolution = AnalyticsService._calculate_store_evolution(store_name, prices)
            evolutions.append(evolution)

        # Sort by average price (cheapest first)
        evolutions.sort(key=lambda x: x.avg_price)

        # Find best and worst stores
        best_store = evolutions[0].store_name if evolutions else None
        worst_store = evolutions[-1].store_name if len(evolutions) > 1 else None

        logger.info(
            f"Price evolution: {len(evolutions)} stores, "
            f"{len(items)} purchases, "
            f"avg: €{overall_avg:.2f}"
        )

        return PriceEvolutionResponse(
            product_name=product_name,
            months=months,
            by_store=evolutions,
            overall_avg_price=round(overall_avg, 2),
            best_store=best_store,
            worst_store=worst_store,
            total_purchases=len(items)
        )

    @staticmethod
    def _calculate_store_evolution(
        store_name: str,
        prices: List[PricePoint]
    ) -> ProductPriceEvolution:
        """Calculate price evolution for a single store."""
        price_values = [p.price for p in prices]
        avg_price = sum(price_values) / len(price_values) if price_values else 0.0
        min_price = min(price_values) if price_values else 0.0
        max_price = max(price_values) if price_values else 0.0

        # Determine trend (simple linear regression)
        trend = AnalyticsService._calculate_trend(prices)

        return ProductPriceEvolution(
            store_name=store_name,
            prices=prices,
            avg_price=round(avg_price, 2),
            min_price=round(min_price, 2),
            max_price=round(max_price, 2),
            price_trend=trend
        )

    @staticmethod
    def _calculate_trend(prices: List[PricePoint]) -> str:
        """Calculate price trend (increasing, decreasing, stable)."""
        if len(prices) < 2:
            return "stable"

        # Simple trend: compare first half vs second half
        mid = len(prices) // 2
        first_half_avg = sum(p.price for p in prices[:mid]) / mid
        second_half_avg = sum(p.price for p in prices[mid:]) / (len(prices) - mid)

        diff_percentage = ((second_half_avg - first_half_avg) / first_half_avg * 100) if first_half_avg > 0 else 0

        if diff_percentage > 5:
            return "increasing"
        elif diff_percentage < -5:
            return "decreasing"
        else:
            return "stable"
