#!/usr/bin/env python3
"""
Migration script to add receipt_review_data table.
Run this once to add the new table to existing databases.
"""

import sys
import os

# Add parent directory to path to import backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database.session import engine
from backend.receipts.models import ReceiptReviewData
from backend.admin.models import SystemConfig
from backend.database.base import Base


def run_migration():
    """Create the receipt_review_data table."""
    print("=" * 50)
    print("Migration: Add receipt_review_data table")
    print("=" * 50)

    print("\n🔧 Creating receipt_review_data table...")

    try:
        # Create only the ReceiptReviewData table
        ReceiptReviewData.__table__.create(bind=engine, checkfirst=True)
        print("✅ Table receipt_review_data created successfully!")

        # Initialize default system configuration
        print("\n🔧 Initializing default system configurations...")
        from backend.database.session import get_db_session

        db = get_db_session()
        try:
            # Check if review_data_retention_days config exists
            config = db.query(SystemConfig).filter(
                SystemConfig.config_key == "review_data_retention_days"
            ).first()

            if not config:
                # Create default config: 30 days retention
                config = SystemConfig(
                    config_key="review_data_retention_days",
                    config_value="30",
                    description="Number of days to retain receipt review data before automatic cleanup"
                )
                db.add(config)
                db.commit()
                print("   ✅ Created default config: review_data_retention_days = 30 days")
            else:
                print(f"   ℹ️  Config already exists: review_data_retention_days = {config.config_value} days")

        except Exception as e:
            print(f"   ⚠️  Error initializing configs: {str(e)}")
            db.rollback()
        finally:
            db.close()

        print("\n✅ Migration completed successfully!")
        print("\nℹ️  Note: Existing receipts will not have review data.")
        print("   Review data will be created for new receipts going forward.")

    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        return False

    print("\n" + "=" * 50)
    return True


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
