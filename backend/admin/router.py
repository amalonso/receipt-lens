"""
Admin API router for administrative endpoints.
Requires admin authentication for all routes.
"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.dependencies import get_db, get_admin_user
from backend.auth.models import User
from backend.admin.service import AdminService
from backend.admin.schemas import (
    UsersListResponse,
    UserStatsResponse,
    SystemDashboardResponse,
    UsageAnalyticsRequest,
    UsageAnalyticsResponse,
    UserAnalyticsResponse,
    AggregatedAnalyticsResponse,
    SystemConfigResponse,
    UpdateConfigRequest,
    ActivityLogsListResponse,
    ActivityLogResponse,
    ReceiptsListAdminResponse,
    ReceiptAdminResponse,
    AdminApiResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"],
    dependencies=[Depends(get_admin_user)]  # All routes require admin
)


# ============ USER MANAGEMENT ============

@router.get("/users", response_model=UsersListResponse)
async def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_admin: Optional[bool] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Get all users with filters, pagination, and statistics.

    **Requires admin privileges.**

    Query parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - search: Search in username or email
    - is_active: Filter by active status
    - is_admin: Filter by admin status
    - sort_by: Sort field (default: created_at)
    - sort_order: Sort order (asc or desc, default: desc)
    """
    try:
        skip = (page - 1) * page_size
        users, total = AdminService.get_all_users(
            db=db,
            skip=skip,
            limit=page_size,
            search=search,
            is_active=is_active,
            is_admin=is_admin,
            sort_by=sort_by,
            sort_order=sort_order
        )

        return UsersListResponse(
            users=users,
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users"
        )


@router.patch("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Toggle user active status (enable/disable account).

    **Requires admin privileges.**

    Cannot disable your own account.
    """
    try:
        user = AdminService.toggle_user_active(db, user_id, current_user.id)
        return {
            "success": True,
            "message": f"User {'activated' if user.is_active else 'deactivated'} successfully",
            "data": user.to_dict()
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error toggling user active status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user status"
        )


@router.patch("/users/{user_id}/toggle-admin")
async def toggle_user_admin(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Toggle user admin status (grant/revoke admin privileges).

    **Requires admin privileges.**
    """
    try:
        user = AdminService.toggle_user_admin(db, user_id, current_user.id)
        return {
            "success": True,
            "message": f"User admin status {'granted' if user.is_admin else 'revoked'} successfully",
            "data": user.to_dict()
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error toggling user admin status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user admin status"
        )


@router.get("/users/{user_id}/statistics")
async def get_user_statistics(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Get detailed statistics for a specific user.

    **Requires admin privileges.**
    """
    try:
        stats = AdminService.get_user_statistics(db, user_id)
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"Error fetching user statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user statistics"
        )


# ============ DASHBOARD & ANALYTICS ============

@router.get("/dashboard", response_model=SystemDashboardResponse)
async def get_system_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Get system-wide dashboard metrics.

    **Requires admin privileges.**

    Returns comprehensive metrics including:
    - User statistics (total, active, new)
    - Receipt statistics
    - Spending analytics
    - API usage and costs
    """
    try:
        dashboard_data = AdminService.get_system_dashboard(db)
        return dashboard_data
    except Exception as e:
        logger.error(f"Error fetching system dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard data"
        )


@router.get("/usage-analytics", response_model=UsageAnalyticsResponse)
async def get_usage_analytics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    group_by: str = Query("month", pattern="^(day|week|month)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Get detailed usage analytics with costs per user.

    **Requires admin privileges.**

    Query parameters:
    - start_date: Start date (ISO format, default: 1 year ago)
    - end_date: End date (ISO format, default: now)
    - group_by: Grouping period (day, week, or month, default: month)

    Returns usage metrics grouped by user and time period, including:
    - Receipt counts
    - Spending totals
    - API calls and costs
    """
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None

        analytics_data = AdminService.get_usage_analytics(
            db=db,
            start_date=start,
            end_date=end,
            group_by=group_by
        )
        return analytics_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error fetching usage analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch usage analytics"
        )


@router.get("/analytics/user/{user_id}", response_model=UserAnalyticsResponse)
async def get_user_analytics(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Get detailed shopping analytics for a specific user.

    **Requires admin privileges.**

    Returns comprehensive shopping analytics including:
    - Monthly spending trends
    - Category spending breakdown
    - Store visit patterns
    - Top purchased products
    """
    try:
        analytics_data = AdminService.get_user_analytics(db, user_id)
        return analytics_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error fetching user analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user analytics"
        )


@router.get("/analytics/aggregated", response_model=AggregatedAnalyticsResponse)
async def get_aggregated_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Get aggregated shopping analytics across all users.

    **Requires admin privileges.**

    Returns comprehensive analytics combining all users' data:
    - Monthly spending trends (all users)
    - Category spending breakdown (all users)
    - Store comparison (all users)
    - Top products across platform
    """
    try:
        analytics_data = AdminService.get_aggregated_analytics(db)
        return analytics_data
    except Exception as e:
        logger.error(f"Error fetching aggregated analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch aggregated analytics"
        )


# ============ CONFIGURATION MANAGEMENT ============

@router.get("/config")
async def get_all_config(
    include_sensitive: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Get all system configuration.

    **Requires admin privileges.**

    Query parameters:
    - include_sensitive: Include sensitive values (default: false, shown as ***)
    """
    try:
        configs = AdminService.get_all_config(db, include_sensitive=include_sensitive)
        return {
            "success": True,
            "data": configs
        }
    except Exception as e:
        logger.error(f"Error fetching configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch configuration"
        )


@router.get("/config/{config_key}")
async def get_config_by_key(
    config_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Get specific configuration by key.

    **Requires admin privileges.**
    """
    try:
        config = AdminService.get_config_by_key(db, config_key)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration key '{config_key}' not found"
            )

        return {
            "success": True,
            "data": config.to_dict(include_sensitive=True)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch configuration"
        )


@router.patch("/config/{config_key}")
async def update_config(
    config_key: str,
    request: UpdateConfigRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Update system configuration value.

    **Requires admin privileges.**

    Changes are logged in activity log.
    """
    try:
        config = AdminService.update_config(
            db=db,
            config_key=config_key,
            config_value=request.config_value,
            admin_id=current_user.id
        )

        return {
            "success": True,
            "message": f"Configuration '{config_key}' updated successfully",
            "data": config.to_dict(include_sensitive=True)
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update configuration"
        )


# ============ ACTIVITY LOGS ============

@router.get("/activity-logs", response_model=ActivityLogsListResponse)
async def get_activity_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Get activity logs with filters and pagination.

    **Requires admin privileges.**

    Query parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 50, max: 200)
    - user_id: Filter by user
    - action: Filter by action type
    - entity_type: Filter by entity type
    - start_date: Filter from date (ISO format)
    - end_date: Filter to date (ISO format)
    """
    try:
        skip = (page - 1) * page_size
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None

        logs, total = AdminService.get_activity_logs(
            db=db,
            skip=skip,
            limit=page_size,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            start_date=start,
            end_date=end
        )

        return ActivityLogsListResponse(
            logs=logs,
            total=total,
            page=page,
            page_size=page_size
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error fetching activity logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch activity logs"
        )


# ============ RECEIPTS (ADMIN VIEW) ============

@router.get("/receipts", response_model=ReceiptsListAdminResponse)
async def get_all_receipts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[int] = Query(None),
    store_name: Optional[str] = Query(None),
    processed: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Get all receipts across users (admin view).

    **Requires admin privileges.**

    Query parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - user_id: Filter by user
    - store_name: Filter by store name (partial match)
    - processed: Filter by processing status
    """
    try:
        skip = (page - 1) * page_size
        receipts, total = AdminService.get_all_receipts_admin(
            db=db,
            skip=skip,
            limit=page_size,
            user_id=user_id,
            store_name=store_name,
            processed=processed
        )

        return ReceiptsListAdminResponse(
            receipts=receipts,
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.error(f"Error fetching receipts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch receipts"
        )


# ============ HEALTH CHECK ============

@router.get("/health")
async def admin_health_check(
    current_user: User = Depends(get_admin_user)
):
    """
    Admin health check endpoint.

    **Requires admin privileges.**

    Returns confirmation that admin authentication is working.
    """
    return {
        "success": True,
        "message": "Admin API is healthy",
        "admin_user": current_user.username
    }
