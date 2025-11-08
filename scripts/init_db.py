#!/usr/bin/env python3
"""
Database initialization script.
Creates tables and optionally creates an admin user.
"""

import sys
import os
from getpass import getpass

# Add parent directory to path to import backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database.session import engine, get_db_session
from backend.database.base import Base, import_models
from backend.auth.models import User
from backend.auth.service import AuthService
from backend.auth.schemas import UserRegisterRequest


def init_database():
    """Initialize database by creating all tables."""
    print("🔧 Initializing database...")

    # Import all models
    import_models()

    # Create all tables
    Base.metadata.create_all(bind=engine)

    print("✅ Database tables created successfully!")


def create_admin_user():
    """Create an admin user interactively."""
    print("\n👤 Create Admin User")
    print("=" * 50)

    # Get user input
    username = input("Enter admin username (default: admin): ").strip() or "admin"
    email = input("Enter admin email: ").strip()

    while not email:
        print("❌ Email is required!")
        email = input("Enter admin email: ").strip()

    # Get password securely
    while True:
        password = getpass("Enter admin password (min 8 chars, uppercase, lowercase, digit): ")
        password_confirm = getpass("Confirm password: ")

        if password != password_confirm:
            print("❌ Passwords do not match! Try again.\n")
            continue

        if len(password) < 8:
            print("❌ Password must be at least 8 characters! Try again.\n")
            continue

        # Check password strength
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)

        if not (has_upper and has_lower and has_digit):
            print("❌ Password must contain uppercase, lowercase, and digit! Try again.\n")
            continue

        break

    # Create user in database
    db = get_db_session()

    try:
        # Check if user already exists
        existing = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing:
            if existing.username == username:
                print(f"❌ Username '{username}' already exists!")
            else:
                print(f"❌ Email '{email}' already exists!")
            return False

        # Create user
        user_data = UserRegisterRequest(
            username=username,
            email=email,
            password=password
        )

        user, token = AuthService.register_user(db, user_data)

        print(f"\n✅ Admin user created successfully!")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   User ID: {user.id}")
        print(f"\n🔑 JWT Token (valid for 24 hours):")
        print(f"   {token.access_token}")

        return True

    except Exception as e:
        print(f"\n❌ Error creating admin user: {str(e)}")
        db.rollback()
        return False

    finally:
        db.close()


def main():
    """Main function."""
    print("=" * 50)
    print("Receipt Lens - Database Initialization")
    print("=" * 50)

    # Initialize database
    init_database()

    # Ask if user wants to create admin
    create_admin = input("\nDo you want to create an admin user? (y/n): ").strip().lower()

    if create_admin == 'y':
        success = create_admin_user()
        if success:
            print("\n🎉 Setup complete! You can now start the application.")
        else:
            print("\n⚠️  Database initialized but admin user creation failed.")
    else:
        print("\n✅ Database initialized successfully!")
        print("   You can create users via the /api/auth/register endpoint.")

    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
