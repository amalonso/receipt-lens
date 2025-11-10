"""
Admin service with business logic for administrative operations.
Handles user management, system analytics, configuration, and activity logging.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from decimal import Decimal

from sqlalchemy import func, desc, and_, or_, text, case
from sqlalchemy.orm import Session

from backend.auth.models import User
from backend.receipts.models import Receipt, Item, Category
from backend.admin.models import ApiCost, ActivityLog, SystemConfig

logger = logging.getLogger(__name__)


class AdminService:
    """Service class for administrative operations."""

    # ============ USER MANAGEMENT ============

    @staticmethod
    def get_all_users(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_admin: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> tuple[List[Dict], int]:
        """
        Get all users with filters and pagination.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            search: Search term for username or email
            is_active: Filter by active status
            is_admin: Filter by admin status
            sort_by: Field to sort by
            sort_order: Sort order (asc or desc)

        Returns:
            tuple: (list of user dicts with stats, total count)
        """
        query = db.query(User)

        # Apply filters
        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    User.username.ilike(search_term),
                    User.email.ilike(search_term)
                )
            )

        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        if is_admin is not None:
            query = query.filter(User.is_admin == is_admin)

        # Get total count
        total_count = query.count()

        # Apply sorting
        sort_column = getattr(User, sort_by, User.created_at)
        if sort_order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        # Apply pagination
        users = query.offset(skip).limit(limit).all()

        # Enrich with statistics
        user_data = []
        for user in users:
            stats = AdminService.get_user_statistics(db, user.id)
            user_dict = user.to_dict()
            user_dict.update(stats)
            user_data.append(user_dict)

        return user_data, total_count

    @staticmethod
    def get_user_statistics(db: Session, user_id: int) -> Dict:
        """
        Get comprehensive statistics for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            dict: User statistics
        """
        # Receipt statistics
        receipt_stats = db.query(
            func.count(Receipt.id).label("total_receipts"),
            func.coalesce(func.sum(Receipt.total_amount), 0).label("total_spending"),
            func.min(Receipt.purchase_date).label("first_purchase"),
            func.max(Receipt.purchase_date).label("last_purchase"),
            func.count(func.distinct(Receipt.store_name)).label("unique_stores")
        ).filter(Receipt.user_id == user_id).first()

        # API cost statistics
        api_cost_stats = db.query(
            func.count(ApiCost.id).label("total_api_calls"),
            func.coalesce(func.sum(ApiCost.cost_usd), 0).label("total_api_cost")
        ).filter(ApiCost.user_id == user_id).first()

        # Item count
        item_count = db.query(func.count(Item.id)).join(Receipt).filter(
            Receipt.user_id == user_id
        ).scalar()

        return {
            "total_receipts": receipt_stats.total_receipts or 0,
            "total_spending": float(receipt_stats.total_spending or 0),
            "first_purchase": receipt_stats.first_purchase.isoformat() if receipt_stats.first_purchase else None,
            "last_purchase": receipt_stats.last_purchase.isoformat() if receipt_stats.last_purchase else None,
            "unique_stores": receipt_stats.unique_stores or 0,
            "total_items": item_count or 0,
            "total_api_calls": api_cost_stats.total_api_calls or 0,
            "total_api_cost": float(api_cost_stats.total_api_cost or 0)
        }

    @staticmethod
    def toggle_user_active(db: Session, user_id: int, admin_id: int) -> User:
        """
        Toggle user active status.

        Args:
            db: Database session
            user_id: User ID to toggle
            admin_id: Admin performing the action

        Returns:
            User: Updated user object

        Raises:
            ValueError: If user not found or trying to disable self
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        if user_id == admin_id:
            raise ValueError("Cannot disable your own account")

        user.is_active = not user.is_active
        db.commit()
        db.refresh(user)

        # Log activity
        AdminService.log_activity(
            db=db,
            user_id=admin_id,
            action="user_status_changed",
            entity_type="user",
            entity_id=user_id,
            details={
                "username": user.username,
                "new_status": "active" if user.is_active else "inactive"
            }
        )

        logger.info(f"User {user.username} (ID: {user_id}) status changed to {'active' if user.is_active else 'inactive'} by admin {admin_id}")

        return user

    @staticmethod
    def toggle_user_admin(db: Session, user_id: int, admin_id: int) -> User:
        """
        Toggle user admin status.

        Args:
            db: Database session
            user_id: User ID to toggle
            admin_id: Admin performing the action

        Returns:
            User: Updated user object

        Raises:
            ValueError: If user not found
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        user.is_admin = not user.is_admin
        db.commit()
        db.refresh(user)

        # Log activity
        AdminService.log_activity(
            db=db,
            user_id=admin_id,
            action="user_role_changed",
            entity_type="user",
            entity_id=user_id,
            details={
                "username": user.username,
                "new_role": "admin" if user.is_admin else "user"
            }
        )

        logger.info(f"User {user.username} (ID: {user_id}) role changed to {'admin' if user.is_admin else 'user'} by admin {admin_id}")

        return user

    # ============ SYSTEM ANALYTICS ============

    @staticmethod
    def get_system_dashboard(db: Session) -> Dict:
        """
        Get system-wide dashboard metrics.

        Args:
            db: Database session

        Returns:
            dict: System metrics
        """
        # User statistics
        total_users = db.query(func.count(User.id)).scalar()
        active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
        admin_users = db.query(func.count(User.id)).filter(User.is_admin == True).scalar()

        # Receipt statistics
        total_receipts = db.query(func.count(Receipt.id)).scalar()
        total_spending = db.query(func.coalesce(func.sum(Receipt.total_amount), 0)).scalar()
        processed_receipts = db.query(func.count(Receipt.id)).filter(Receipt.processed == True).scalar()

        # Item statistics
        total_items = db.query(func.count(Item.id)).scalar()
        total_stores = db.query(func.count(func.distinct(Receipt.store_name))).scalar()

        # API cost statistics
        total_api_calls = db.query(func.count(ApiCost.id)).scalar()
        total_api_cost = db.query(func.coalesce(func.sum(ApiCost.cost_usd), 0)).scalar()
        successful_calls = db.query(func.count(ApiCost.id)).filter(ApiCost.success == True).scalar()

        # Recent activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        new_users_24h = db.query(func.count(User.id)).filter(User.created_at >= yesterday).scalar()
        new_receipts_24h = db.query(func.count(Receipt.id)).filter(Receipt.created_at >= yesterday).scalar()

        # Recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        new_users_7d = db.query(func.count(User.id)).filter(User.created_at >= week_ago).scalar()
        new_receipts_7d = db.query(func.count(Receipt.id)).filter(Receipt.created_at >= week_ago).scalar()
        api_cost_7d = db.query(func.coalesce(func.sum(ApiCost.cost_usd), 0)).filter(
            ApiCost.created_at >= week_ago
        ).scalar()

        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "inactive": total_users - active_users,
                "admins": admin_users,
                "new_24h": new_users_24h,
                "new_7d": new_users_7d
            },
            "receipts": {
                "total": total_receipts,
                "processed": processed_receipts,
                "pending": total_receipts - processed_receipts,
                "new_24h": new_receipts_24h,
                "new_7d": new_receipts_7d
            },
            "spending": {
                "total": float(total_spending),
                "avg_per_receipt": float(total_spending / total_receipts) if total_receipts > 0 else 0,
                "avg_per_user": float(total_spending / total_users) if total_users > 0 else 0
            },
            "items": {
                "total": total_items,
                "avg_per_receipt": float(total_items / total_receipts) if total_receipts > 0 else 0
            },
            "stores": {
                "total": total_stores
            },
            "api": {
                "total_calls": total_api_calls,
                "successful_calls": successful_calls,
                "failed_calls": total_api_calls - successful_calls,
                "total_cost": float(total_api_cost),
                "avg_cost_per_call": float(total_api_cost / total_api_calls) if total_api_calls > 0 else 0,
                "cost_7d": float(api_cost_7d)
            }
        }

    @staticmethod
    def get_usage_analytics(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = "month"
    ) -> Dict:
        """
        Get detailed usage analytics with costs per user.

        Args:
            db: Database session
            start_date: Start date for filtering
            end_date: End date for filtering
            group_by: Grouping period (day, week, month)

        Returns:
            dict: Usage analytics
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=365)
        if not end_date:
            end_date = datetime.utcnow()

        # Determine date truncation function based on group_by
        if group_by == "day":
            date_trunc = func.date_trunc('day', Receipt.created_at)
        elif group_by == "week":
            date_trunc = func.date_trunc('week', Receipt.created_at)
        else:  # month
            date_trunc = func.date_trunc('month', Receipt.created_at)

        # Query usage by user and period
        usage_query = db.query(
            User.id.label("user_id"),
            User.username,
            User.email,
            date_trunc.label("period"),
            func.count(func.distinct(Receipt.id)).label("receipts_count"),
            func.coalesce(func.sum(Receipt.total_amount), 0).label("total_spending"),
            func.count(func.distinct(Item.id)).label("items_count")
        ).join(Receipt, User.id == Receipt.user_id).outerjoin(
            Item, Receipt.id == Item.receipt_id
        ).filter(
            and_(
                Receipt.created_at >= start_date,
                Receipt.created_at <= end_date
            )
        ).group_by(User.id, User.username, User.email, date_trunc).order_by(
            date_trunc.desc(), func.count(func.distinct(Receipt.id)).desc()
        ).all()

        # Query API costs by user and period
        api_costs_query = db.query(
            ApiCost.user_id,
            date_trunc.label("period"),
            func.count(ApiCost.id).label("api_calls"),
            func.coalesce(func.sum(ApiCost.cost_usd), 0).label("api_cost")
        ).filter(
            and_(
                ApiCost.created_at >= start_date,
                ApiCost.created_at <= end_date
            )
        ).group_by(ApiCost.user_id, date_trunc).all()

        # Create a dict for quick API cost lookup
        api_costs_dict = {}
        for row in api_costs_query:
            key = (row.user_id, row.period)
            api_costs_dict[key] = {
                "api_calls": row.api_calls,
                "api_cost": float(row.api_cost)
            }

        # Combine data
        result = []
        for row in usage_query:
            key = (row.user_id, row.period)
            api_data = api_costs_dict.get(key, {"api_calls": 0, "api_cost": 0.0})

            result.append({
                "user_id": row.user_id,
                "username": row.username,
                "email": row.email,
                "period": row.period.isoformat() if row.period else None,
                "receipts_count": row.receipts_count,
                "total_spending": float(row.total_spending),
                "items_count": row.items_count,
                "api_calls": api_data["api_calls"],
                "api_cost": api_data["api_cost"]
            })

        # Calculate totals
        total_receipts = sum(r["receipts_count"] for r in result)
        total_spending = sum(r["total_spending"] for r in result)
        total_api_calls = sum(r["api_calls"] for r in result)
        total_api_cost = sum(r["api_cost"] for r in result)

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "group_by": group_by
            },
            "summary": {
                "total_receipts": total_receipts,
                "total_spending": total_spending,
                "total_api_calls": total_api_calls,
                "total_api_cost": total_api_cost
            },
            "data": result
        }

    @staticmethod
    def get_user_analytics(db: Session, user_id: int) -> Dict:
        """
        Get detailed analytics for a specific user (for admin shopping dashboard).

        Args:
            db: Database session
            user_id: User ID

        Returns:
            dict: User analytics
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        # Monthly spending
        monthly_spending = db.query(
            func.extract('year', Receipt.purchase_date).label('year'),
            func.extract('month', Receipt.purchase_date).label('month'),
            func.count(Receipt.id).label('receipt_count'),
            func.coalesce(func.sum(Receipt.total_amount), 0).label('total_amount')
        ).filter(Receipt.user_id == user_id).group_by(
            func.extract('year', Receipt.purchase_date),
            func.extract('month', Receipt.purchase_date)
        ).order_by(desc('year'), desc('month')).limit(12).all()

        # Category spending
        category_spending = db.query(
            Category.name,
            func.count(Item.id).label('item_count'),
            func.coalesce(func.sum(Item.total_price), 0).label('total_spent')
        ).join(Item, Category.id == Item.category_id).join(
            Receipt, Item.receipt_id == Receipt.id
        ).filter(Receipt.user_id == user_id).group_by(Category.name).all()

        # Store spending
        store_spending = db.query(
            Receipt.store_name,
            func.count(Receipt.id).label('visit_count'),
            func.coalesce(func.sum(Receipt.total_amount), 0).label('total_spent'),
            func.avg(Receipt.total_amount).label('avg_receipt')
        ).filter(Receipt.user_id == user_id).group_by(
            Receipt.store_name
        ).order_by(desc('total_spent')).limit(10).all()

        # Top products
        top_products = db.query(
            Item.product_name,
            Category.name.label('category'),
            func.count(Item.id).label('purchase_count'),
            func.sum(Item.quantity).label('total_quantity'),
            func.coalesce(func.sum(Item.total_price), 0).label('total_spent'),
            func.avg(Item.unit_price).label('avg_price')
        ).join(Receipt, Item.receipt_id == Receipt.id).outerjoin(
            Category, Item.category_id == Category.id
        ).filter(Receipt.user_id == user_id).group_by(
            Item.product_name, Category.name
        ).order_by(desc('purchase_count')).limit(20).all()

        return {
            "user": user.to_dict(),
            "monthly_spending": [
                {
                    "year": int(row.year),
                    "month": int(row.month),
                    "receipt_count": row.receipt_count,
                    "total_amount": float(row.total_amount)
                }
                for row in monthly_spending
            ],
            "category_spending": [
                {
                    "category": row.name,
                    "item_count": row.item_count,
                    "total_spent": float(row.total_spent)
                }
                for row in category_spending
            ],
            "store_spending": [
                {
                    "store_name": row.store_name,
                    "visit_count": row.visit_count,
                    "total_spent": float(row.total_spent),
                    "avg_receipt": float(row.avg_receipt)
                }
                for row in store_spending
            ],
            "top_products": [
                {
                    "product_name": row.product_name,
                    "category": row.category,
                    "purchase_count": row.purchase_count,
                    "total_quantity": float(row.total_quantity),
                    "total_spent": float(row.total_spent),
                    "avg_price": float(row.avg_price)
                }
                for row in top_products
            ]
        }

    @staticmethod
    def get_aggregated_analytics(db: Session) -> Dict:
        """
        Get aggregated analytics across all users (for admin shopping dashboard).

        Args:
            db: Database session

        Returns:
            dict: Aggregated analytics
        """
        # Monthly spending (all users)
        monthly_spending = db.query(
            func.extract('year', Receipt.purchase_date).label('year'),
            func.extract('month', Receipt.purchase_date).label('month'),
            func.count(Receipt.id).label('receipt_count'),
            func.count(func.distinct(Receipt.user_id)).label('user_count'),
            func.coalesce(func.sum(Receipt.total_amount), 0).label('total_amount')
        ).group_by(
            func.extract('year', Receipt.purchase_date),
            func.extract('month', Receipt.purchase_date)
        ).order_by(desc('year'), desc('month')).limit(12).all()

        # Category spending (all users)
        category_spending = db.query(
            Category.name,
            func.count(Item.id).label('item_count'),
            func.count(func.distinct(Receipt.user_id)).label('user_count'),
            func.coalesce(func.sum(Item.total_price), 0).label('total_spent'),
            func.avg(Item.unit_price).label('avg_price')
        ).join(Item, Category.id == Item.category_id).join(
            Receipt, Item.receipt_id == Receipt.id
        ).group_by(Category.name).all()

        # Store spending (all users)
        store_spending = db.query(
            Receipt.store_name,
            func.count(Receipt.id).label('visit_count'),
            func.count(func.distinct(Receipt.user_id)).label('user_count'),
            func.coalesce(func.sum(Receipt.total_amount), 0).label('total_spent'),
            func.avg(Receipt.total_amount).label('avg_receipt')
        ).group_by(Receipt.store_name).order_by(desc('total_spent')).limit(10).all()

        # Top products (all users)
        top_products = db.query(
            Item.product_name,
            Category.name.label('category'),
            func.count(Item.id).label('purchase_count'),
            func.count(func.distinct(Receipt.user_id)).label('buyer_count'),
            func.sum(Item.quantity).label('total_quantity'),
            func.coalesce(func.sum(Item.total_price), 0).label('total_spent'),
            func.avg(Item.unit_price).label('avg_price'),
            func.min(Item.unit_price).label('min_price'),
            func.max(Item.unit_price).label('max_price')
        ).join(Receipt, Item.receipt_id == Receipt.id).outerjoin(
            Category, Item.category_id == Category.id
        ).group_by(Item.product_name, Category.name).order_by(
            desc('purchase_count')
        ).limit(30).all()

        return {
            "monthly_spending": [
                {
                    "year": int(row.year),
                    "month": int(row.month),
                    "receipt_count": row.receipt_count,
                    "user_count": row.user_count,
                    "total_amount": float(row.total_amount)
                }
                for row in monthly_spending
            ],
            "category_spending": [
                {
                    "category": row.name,
                    "item_count": row.item_count,
                    "user_count": row.user_count,
                    "total_spent": float(row.total_spent),
                    "avg_price": float(row.avg_price) if row.avg_price else 0
                }
                for row in category_spending
            ],
            "store_spending": [
                {
                    "store_name": row.store_name,
                    "visit_count": row.visit_count,
                    "user_count": row.user_count,
                    "total_spent": float(row.total_spent),
                    "avg_receipt": float(row.avg_receipt)
                }
                for row in store_spending
            ],
            "top_products": [
                {
                    "product_name": row.product_name,
                    "category": row.category,
                    "purchase_count": row.purchase_count,
                    "buyer_count": row.buyer_count,
                    "total_quantity": float(row.total_quantity),
                    "total_spent": float(row.total_spent),
                    "avg_price": float(row.avg_price) if row.avg_price else 0,
                    "min_price": float(row.min_price) if row.min_price else 0,
                    "max_price": float(row.max_price) if row.max_price else 0
                }
                for row in top_products
            ]
        }

    # ============ CONFIGURATION MANAGEMENT ============

    @staticmethod
    def get_all_config(db: Session, include_sensitive: bool = False) -> List[Dict]:
        """
        Get all system configuration.

        Args:
            db: Database session
            include_sensitive: Whether to include sensitive values

        Returns:
            list: Configuration items
        """
        configs = db.query(SystemConfig).order_by(SystemConfig.category, SystemConfig.config_key).all()
        return [config.to_dict(include_sensitive=include_sensitive) for config in configs]

    @staticmethod
    def get_config_by_key(db: Session, config_key: str) -> Optional[SystemConfig]:
        """
        Get configuration by key.

        Args:
            db: Database session
            config_key: Configuration key

        Returns:
            SystemConfig or None
        """
        return db.query(SystemConfig).filter(SystemConfig.config_key == config_key).first()

    @staticmethod
    def update_config(
        db: Session,
        config_key: str,
        config_value: str,
        admin_id: int
    ) -> SystemConfig:
        """
        Update configuration value.

        Args:
            db: Database session
            config_key: Configuration key
            config_value: New value
            admin_id: Admin performing the update

        Returns:
            SystemConfig: Updated configuration

        Raises:
            ValueError: If config not found
        """
        config = db.query(SystemConfig).filter(SystemConfig.config_key == config_key).first()
        if not config:
            raise ValueError(f"Configuration key '{config_key}' not found")

        old_value = config.config_value
        config.config_value = config_value
        config.updated_by = admin_id
        config.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(config)

        # Log activity
        AdminService.log_activity(
            db=db,
            user_id=admin_id,
            action="config_updated",
            entity_type="config",
            entity_id=config.id,
            details={
                "config_key": config_key,
                "old_value": old_value if not config.is_sensitive else "***",
                "new_value": config_value if not config.is_sensitive else "***"
            }
        )

        logger.info(f"Configuration '{config_key}' updated by admin {admin_id}")

        return config

    # ============ ACTIVITY LOGGING ============

    @staticmethod
    def log_activity(
        db: Session,
        user_id: Optional[int],
        action: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ActivityLog:
        """
        Log an activity for audit trail.

        Args:
            db: Database session
            user_id: User performing the action (None for system)
            action: Action type
            entity_type: Type of entity affected
            entity_id: ID of entity affected
            details: Additional details as dict
            ip_address: IP address
            user_agent: User agent string

        Returns:
            ActivityLog: Created log entry
        """
        log = ActivityLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )

        db.add(log)
        db.commit()
        db.refresh(log)

        return log

    @staticmethod
    def get_activity_logs(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> tuple[List[Dict], int]:
        """
        Get activity logs with filters.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            user_id: Filter by user
            action: Filter by action
            entity_type: Filter by entity type
            start_date: Filter by start date
            end_date: Filter by end date

        Returns:
            tuple: (list of log dicts with user info, total count)
        """
        query = db.query(ActivityLog)

        # Apply filters
        if user_id is not None:
            query = query.filter(ActivityLog.user_id == user_id)

        if action:
            query = query.filter(ActivityLog.action == action)

        if entity_type:
            query = query.filter(ActivityLog.entity_type == entity_type)

        if start_date:
            query = query.filter(ActivityLog.created_at >= start_date)

        if end_date:
            query = query.filter(ActivityLog.created_at <= end_date)

        # Get total count
        total_count = query.count()

        # Order and paginate
        logs = query.order_by(desc(ActivityLog.created_at)).offset(skip).limit(limit).all()

        # Enrich with user information
        result = []
        for log in logs:
            log_dict = log.to_dict()
            if log.user_id:
                user = db.query(User).filter(User.id == log.user_id).first()
                if user:
                    log_dict["username"] = user.username
            result.append(log_dict)

        return result, total_count

    @staticmethod
    def get_all_receipts_admin(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[int] = None,
        store_name: Optional[str] = None,
        processed: Optional[bool] = None
    ) -> tuple[List[Dict], int]:
        """
        Get all receipts across users (admin view).

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            user_id: Filter by user
            store_name: Filter by store
            processed: Filter by processing status

        Returns:
            tuple: (list of receipt dicts with user info, total count)
        """
        query = db.query(Receipt)

        # Apply filters
        if user_id is not None:
            query = query.filter(Receipt.user_id == user_id)

        if store_name:
            query = query.filter(Receipt.store_name.ilike(f"%{store_name}%"))

        if processed is not None:
            query = query.filter(Receipt.processed == processed)

        # Get total count
        total_count = query.count()

        # Order and paginate
        receipts = query.order_by(desc(Receipt.created_at)).offset(skip).limit(limit).all()

        # Enrich with user information
        result = []
        for receipt in receipts:
            receipt_dict = receipt.to_dict()
            user = db.query(User).filter(User.id == receipt.user_id).first()
            if user:
                receipt_dict["username"] = user.username
                receipt_dict["user_email"] = user.email
            result.append(receipt_dict)

        return result, total_count
