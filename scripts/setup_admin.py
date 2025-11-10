#!/usr/bin/env python3
"""
Script to run admin feature migration and setup first admin user.
Usage: python scripts/setup_admin.py [--make-admin USERNAME]
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from backend.database.session import engine, SessionLocal
from backend.auth.models import User


def run_migration():
    """Execute the admin features migration SQL script."""
    migration_file = Path(__file__).parent.parent / "backend" / "database" / "migrations" / "001_add_admin_features.sql"

    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False

    print("📄 Reading migration file...")
    with open(migration_file, 'r') as f:
        migration_sql = f.read()

    print("🔄 Executing migration...")
    try:
        # Execute the entire SQL file as a single block to respect transaction boundaries
        # The migration file contains BEGIN/COMMIT, so we use raw connection
        with engine.raw_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(migration_sql)
                conn.commit()
                print("✅ Migration completed successfully!")
                return True
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                cursor.close()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def make_user_admin(username: str):
    """Make a user an admin."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()

        if not user:
            print(f"❌ User '{username}' not found")
            return False

        if user.is_admin:
            print(f"ℹ️  User '{username}' is already an admin")
            return True

        user.is_admin = True
        user.is_active = True  # Ensure user is also active
        db.commit()

        print(f"✅ User '{username}' is now an admin!")
        return True
    except Exception as e:
        print(f"❌ Error making user admin: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def make_first_user_admin():
    """Make the first registered user an admin."""
    db = SessionLocal()
    try:
        # Get the first user by ID
        first_user = db.query(User).order_by(User.id).first()

        if not first_user:
            print("❌ No users found in database")
            return False

        if first_user.is_admin:
            print(f"ℹ️  First user '{first_user.username}' is already an admin")
            return True

        first_user.is_admin = True
        first_user.is_active = True
        db.commit()

        print(f"✅ First user '{first_user.username}' is now an admin!")
        return True
    except Exception as e:
        print(f"❌ Error making first user admin: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def list_users():
    """List all users with their admin status."""
    db = SessionLocal()
    try:
        users = db.query(User).order_by(User.id).all()

        if not users:
            print("No users found in database")
            return

        print("\n👥 Users in system:")
        print("-" * 80)
        print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Admin':<10} {'Active':<10}")
        print("-" * 80)

        for user in users:
            admin_status = "✓ Yes" if user.is_admin else "✗ No"
            active_status = "✓ Yes" if user.is_active else "✗ No"
            print(f"{user.id:<5} {user.username:<20} {user.email:<30} {admin_status:<10} {active_status:<10}")

        print("-" * 80)
        print(f"Total: {len(users)} users ({sum(1 for u in users if u.is_admin)} admins)")
    except Exception as e:
        print(f"❌ Error listing users: {e}")
    finally:
        db.close()


def main():
    print("=" * 80)
    print("Receipt Lens - Admin Setup Script")
    print("=" * 80)
    print()

    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--make-admin' and len(sys.argv) > 2:
            username = sys.argv[2]
            print(f"🔧 Making user '{username}' an admin...\n")
            success = make_user_admin(username)
            if success:
                print()
                list_users()
            return

        elif sys.argv[1] == '--list':
            list_users()
            return

        elif sys.argv[1] == '--help':
            print("Usage:")
            print("  python scripts/setup_admin.py                    # Run migration and make first user admin")
            print("  python scripts/setup_admin.py --make-admin USER  # Make specific user admin")
            print("  python scripts/setup_admin.py --list             # List all users")
            print("  python scripts/setup_admin.py --help             # Show this help")
            return

    # Default behavior: run migration and make first user admin
    print("🚀 Step 1: Running database migration...\n")
    migration_success = run_migration()

    if not migration_success:
        print("\n❌ Setup failed due to migration error")
        return

    print("\n🚀 Step 2: Making first user an admin...\n")
    admin_success = make_first_user_admin()

    if not admin_success:
        print("\n⚠️  Could not set first user as admin")
        print("    You can manually set an admin using:")
        print("    python scripts/setup_admin.py --make-admin USERNAME")

    print()
    list_users()

    print("\n" + "=" * 80)
    print("✅ Admin setup completed!")
    print("=" * 80)
    print("\n📌 Next steps:")
    print("   1. Restart the application")
    print("   2. Login with your admin user")
    print("   3. Access admin panel at /admin-dashboard.html")
    print()


if __name__ == "__main__":
    main()
