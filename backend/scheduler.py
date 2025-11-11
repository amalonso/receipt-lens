"""
Scheduled tasks for Receipt Lens.
Handles periodic cleanup and maintenance operations.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.database.session import SessionLocal
from backend.receipts.models import ReceiptReviewData
from backend.admin.models import SystemConfig
import os

logger = logging.getLogger(__name__)

scheduler: Optional[AsyncIOScheduler] = None


def get_retention_days(db: Session) -> int:
    """
    Get the review data retention period from system config.

    Args:
        db: Database session

    Returns:
        int: Number of days to retain review data (default: 30)
    """
    config = db.query(SystemConfig).filter(
        SystemConfig.config_key == "review_data_retention_days"
    ).first()

    if config and config.config_value:
        try:
            return int(config.config_value)
        except ValueError:
            logger.warning(f"Invalid retention days value: {config.config_value}, using default 30")
            return 30

    return 30  # Default


def cleanup_old_review_data():
    """
    Clean up old receipt review data based on retention policy.

    This removes ReceiptReviewData records older than the configured retention period.
    IMPORTANT: This ONLY deletes review data, never the actual receipt data.
    """
    logger.info("Starting scheduled cleanup of old review data...")

    db = SessionLocal()
    try:
        # Get retention period from config
        retention_days = get_retention_days(db)
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        logger.info(f"Retention period: {retention_days} days")
        logger.info(f"Deleting review data created before: {cutoff_date}")

        # Find old review data
        old_reviews = db.query(ReceiptReviewData).filter(
            ReceiptReviewData.created_at < cutoff_date
        ).all()

        deleted_count = 0
        deleted_images = 0

        for review in old_reviews:
            # Note: We don't delete the receipt image file here as it's still
            # referenced by the Receipt record. The image will be deleted when
            # the receipt itself is deleted by the user.
            logger.debug(f"Deleting review data {review.id} (created: {review.created_at})")
            db.delete(review)
            deleted_count += 1

        db.commit()

        logger.info(
            f"Cleanup completed: Deleted {deleted_count} review data records "
            f"(older than {retention_days} days)"
        )

        return {
            "success": True,
            "deleted_count": deleted_count,
            "retention_days": retention_days
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error during review data cleanup: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

    finally:
        db.close()


def start_scheduler():
    """
    Start the background scheduler for periodic tasks.

    Schedules:
    - Review data cleanup: Daily at 3:00 AM
    """
    global scheduler

    if scheduler is not None:
        logger.warning("Scheduler already running, skipping start")
        return

    logger.info("Starting background task scheduler...")

    scheduler = AsyncIOScheduler()

    # Schedule cleanup task - runs daily at 3:00 AM
    scheduler.add_job(
        cleanup_old_review_data,
        trigger=CronTrigger(hour=3, minute=0),
        id="cleanup_review_data",
        name="Cleanup old receipt review data",
        replace_existing=True
    )

    scheduler.start()

    logger.info("Background task scheduler started successfully")
    logger.info("Scheduled tasks:")
    for job in scheduler.get_jobs():
        logger.info(f"  - {job.name} (ID: {job.id}, Next run: {job.next_run_time})")


def stop_scheduler():
    """Stop the background scheduler."""
    global scheduler

    if scheduler is not None:
        logger.info("Stopping background task scheduler...")
        scheduler.shutdown()
        scheduler = None
        logger.info("Background task scheduler stopped")


def run_cleanup_now() -> dict:
    """
    Run the cleanup task immediately (for testing or manual trigger).

    Returns:
        dict: Cleanup results
    """
    logger.info("Running cleanup task manually...")
    return cleanup_old_review_data()
