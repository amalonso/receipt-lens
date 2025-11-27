"""
Unit tests for receipts service.
Tests business logic, validation, and database operations.
"""

import pytest
import os
import tempfile
from io import BytesIO
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from backend.receipts.service import ReceiptService
from backend.receipts.models import Receipt, Category, Item, ReceiptReviewData
from backend.receipts.schemas import ClaudeAnalysisResponse, ItemSchema
from backend.auth.models import User


# Helper functions

def create_mock_upload_file(filename: str, content: bytes) -> UploadFile:
    """Create a mock UploadFile object for testing."""
    file = BytesIO(content)
    upload_file = UploadFile(filename=filename, file=file)
    # Make read() async-compatible
    upload_file.read = AsyncMock(return_value=content)
    return upload_file


def create_test_user(db: Session, username: str = "testuser", email: str = "testuser@example.com") -> User:
    """Create a test user in the database."""
    from backend.auth.service import AuthService
    from backend.auth.schemas import UserRegisterRequest

    user_data = UserRegisterRequest(
        username=username,
        email=email,
        password="TestPassword123",
        password_confirm="TestPassword123"
    )
    user, token = AuthService.register_user(db=db, user_data=user_data)
    return user


def create_test_category(db: Session, name: str = "bebidas") -> Category:
    """Create a test category in the database."""
    category = Category(name=name)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def create_test_receipt(db: Session, user: User, store_name: str = "Test Store") -> Receipt:
    """Create a test receipt in the database."""
    receipt = Receipt(
        user_id=user.id,
        store_name=store_name,
        purchase_date=date.today(),
        total_amount=Decimal("50.00"),
        image_path="/tmp/test_receipt.jpg",
        image_hash="test_hash_123",
        processed=True
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    return receipt


# Test: File hash calculation

def test_calculate_file_hash():
    """Test that file hash is calculated correctly."""
    content = b"Test receipt image content"
    hash_result = ReceiptService._calculate_file_hash(content)

    # SHA256 hash should be 64 characters (hexadecimal)
    assert len(hash_result) == 64
    assert hash_result.isalnum()

    # Same content should produce same hash
    hash_result2 = ReceiptService._calculate_file_hash(content)
    assert hash_result == hash_result2

    # Different content should produce different hash
    different_content = b"Different content"
    different_hash = ReceiptService._calculate_file_hash(different_content)
    assert hash_result != different_hash


# Test: File validation

def test_validate_file_success():
    """Test that valid files pass validation."""
    valid_files = [
        create_mock_upload_file("receipt.jpg", b"test"),
        create_mock_upload_file("receipt.jpeg", b"test"),
        create_mock_upload_file("receipt.png", b"test"),
        create_mock_upload_file("receipt.pdf", b"test"),
    ]

    for file in valid_files:
        # Should not raise exception
        ReceiptService._validate_file(file)


def test_validate_file_no_filename():
    """Test validation fails when filename is missing."""
    file = Mock(spec=UploadFile)
    file.filename = None

    with pytest.raises(HTTPException) as exc_info:
        ReceiptService._validate_file(file)

    assert exc_info.value.status_code == 400
    assert "No file provided" in exc_info.value.detail


def test_validate_file_invalid_extension():
    """Test validation fails for invalid file extensions."""
    invalid_files = [
        create_mock_upload_file("document.txt", b"test"),
        create_mock_upload_file("script.py", b"test"),
        create_mock_upload_file("image.gif", b"test"),
        create_mock_upload_file("archive.zip", b"test"),
    ]

    for file in invalid_files:
        with pytest.raises(HTTPException) as exc_info:
            ReceiptService._validate_file(file)

        assert exc_info.value.status_code == 400
        assert "not allowed" in exc_info.value.detail.lower()


# Test: Save upload file

@pytest.mark.asyncio
async def test_save_upload_file_success():
    """Test file is saved correctly to disk."""
    content = b"Test image content"
    file = create_mock_upload_file("receipt.jpg", content)

    with tempfile.TemporaryDirectory() as temp_dir:
        file_path, file_hash, file_content = await ReceiptService._save_upload_file(
            file, user_id=1, upload_dir=temp_dir
        )

        # Check file was created
        assert os.path.exists(file_path)
        assert file_content == content

        # Check file_path structure
        assert str(Path(file_path).parent).endswith("user_1")
        assert Path(file_path).suffix == ".jpg"

        # Check hash is correct
        expected_hash = ReceiptService._calculate_file_hash(content)
        assert file_hash == expected_hash

        # Verify file content
        with open(file_path, 'rb') as f:
            saved_content = f.read()
        assert saved_content == content


@pytest.mark.asyncio
async def test_save_upload_file_too_large():
    """Test that oversized files are rejected."""
    # Create file larger than max size (10MB)
    large_content = b"x" * (11 * 1024 * 1024)  # 11MB
    file = create_mock_upload_file("large_receipt.jpg", large_content)

    with tempfile.TemporaryDirectory() as temp_dir:
        with pytest.raises(HTTPException) as exc_info:
            await ReceiptService._save_upload_file(file, user_id=1, upload_dir=temp_dir)

        assert exc_info.value.status_code == 413
        assert "too large" in exc_info.value.detail.lower()


# Test: Check duplicate

def test_check_duplicate_exists(db: Session):
    """Test duplicate detection when receipt exists."""
    user = create_test_user(db)
    file_hash = "duplicate_hash_123"

    # Create existing receipt with this hash
    existing = create_test_receipt(db, user)
    existing.image_hash = file_hash
    db.commit()

    # Check for duplicate
    duplicate = ReceiptService._check_duplicate(db, user.id, file_hash)

    assert duplicate is not None
    assert duplicate.id == existing.id
    assert duplicate.image_hash == file_hash


def test_check_duplicate_not_exists(db: Session):
    """Test no duplicate found for new file."""
    user = create_test_user(db)

    # Check for non-existent hash
    duplicate = ReceiptService._check_duplicate(db, user.id, "unique_hash_456")

    assert duplicate is None


def test_check_duplicate_different_user(db: Session):
    """Test duplicate check is user-specific."""
    user1 = create_test_user(db)

    # Create user2
    user2 = create_test_user(db, username="user2", email="user2@example.com")

    file_hash = "shared_hash_789"

    # Create receipt for user1
    receipt1 = create_test_receipt(db, user1)
    receipt1.image_hash = file_hash
    db.commit()

    # Check duplicate for user2 (should not find user1's receipt)
    duplicate = ReceiptService._check_duplicate(db, user2.id, file_hash)

    assert duplicate is None


# Test: Get or create category

def test_get_or_create_category_exists(db: Session):
    """Test getting existing category."""
    # Create category
    existing = create_test_category(db, "carne")

    # Get it
    category = ReceiptService._get_or_create_category(db, "carne")

    assert category.id == existing.id
    assert category.name == "carne"


def test_get_or_create_category_new(db: Session):
    """Test creating new category when it doesn't exist."""
    # Create a category first (to have at least one)
    create_test_category(db, "bebidas")

    # Get/create non-existent category
    category = ReceiptService._get_or_create_category(db, "nueva_categoria")

    assert category.id is not None
    assert category.name == "nueva_categoria"

    # Verify it's in database
    found = db.query(Category).filter(Category.name == "nueva_categoria").first()
    assert found is not None
    assert found.id == category.id


def test_get_or_create_category_case_insensitive(db: Session):
    """Test category lookup is case-insensitive."""
    # Create category
    create_test_category(db, "verduras")

    # Get with different case
    category = ReceiptService._get_or_create_category(db, "VERDURAS")

    assert category.name == "verduras"


# Test: Get user receipts

def test_get_user_receipts_empty(db: Session):
    """Test getting receipts when user has none."""
    user = create_test_user(db)

    receipts, total = ReceiptService.get_user_receipts(db, user.id)

    assert len(receipts) == 0
    assert total == 0


def test_get_user_receipts_pagination(db: Session):
    """Test pagination works correctly."""
    user = create_test_user(db)

    # Create 25 receipts
    for i in range(25):
        create_test_receipt(db, user, store_name=f"Store {i}")

    # Get first page (20 items)
    receipts_page1, total = ReceiptService.get_user_receipts(db, user.id, skip=0, limit=20)

    assert len(receipts_page1) == 20
    assert total == 25

    # Get second page (5 items)
    receipts_page2, total = ReceiptService.get_user_receipts(db, user.id, skip=20, limit=20)

    assert len(receipts_page2) == 5
    assert total == 25


def test_get_user_receipts_ordering(db: Session):
    """Test receipts are ordered by purchase date descending."""
    user = create_test_user(db)

    # Create receipts with different dates
    from datetime import timedelta
    today = date.today()

    receipt1 = create_test_receipt(db, user, "Store 1")
    receipt1.purchase_date = today - timedelta(days=5)

    receipt2 = create_test_receipt(db, user, "Store 2")
    receipt2.purchase_date = today - timedelta(days=2)

    receipt3 = create_test_receipt(db, user, "Store 3")
    receipt3.purchase_date = today

    db.commit()

    # Get receipts
    receipts, _ = ReceiptService.get_user_receipts(db, user.id)

    # Should be ordered newest first
    assert receipts[0].id == receipt3.id
    assert receipts[1].id == receipt2.id
    assert receipts[2].id == receipt1.id


def test_get_user_receipts_isolation(db: Session):
    """Test that users only see their own receipts."""
    user1 = create_test_user(db)

    # Create user2
    user2 = create_test_user(db, username="user2", email="user2@example.com")

    # Create receipts for both users
    create_test_receipt(db, user1, "User1 Store")
    create_test_receipt(db, user1, "User1 Store 2")
    create_test_receipt(db, user2, "User2 Store")

    # Get receipts for user1
    receipts1, total1 = ReceiptService.get_user_receipts(db, user1.id)

    assert len(receipts1) == 2
    assert total1 == 2
    assert all(r.user_id == user1.id for r in receipts1)

    # Get receipts for user2
    receipts2, total2 = ReceiptService.get_user_receipts(db, user2.id)

    assert len(receipts2) == 1
    assert total2 == 1
    assert receipts2[0].user_id == user2.id


# Test: Get receipt by ID

def test_get_receipt_by_id_success(db: Session):
    """Test getting receipt by ID successfully."""
    user = create_test_user(db)
    receipt = create_test_receipt(db, user)

    found = ReceiptService.get_receipt_by_id(db, receipt.id, user.id)

    assert found is not None
    assert found.id == receipt.id
    assert found.user_id == user.id


def test_get_receipt_by_id_not_found(db: Session):
    """Test error when receipt doesn't exist."""
    user = create_test_user(db)

    with pytest.raises(HTTPException) as exc_info:
        ReceiptService.get_receipt_by_id(db, 999, user.id)

    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail.lower()


def test_get_receipt_by_id_wrong_user(db: Session):
    """Test error when trying to access another user's receipt."""
    user1 = create_test_user(db)

    # Create user2
    user2 = create_test_user(db, username="user2", email="user2@example.com")

    # Create receipt for user1
    receipt = create_test_receipt(db, user1)

    # Try to access with user2
    with pytest.raises(HTTPException) as exc_info:
        ReceiptService.get_receipt_by_id(db, receipt.id, user2.id)

    assert exc_info.value.status_code == 403
    assert "access denied" in exc_info.value.detail.lower()


# Test: Update receipt

def test_update_receipt_basic_fields(db: Session):
    """Test updating basic receipt fields."""
    user = create_test_user(db)
    receipt = create_test_receipt(db, user, "Original Store")

    # Update store name and total
    update_data = {
        "store_name": "Updated Store",
        "total_amount": Decimal("75.50")
    }

    updated = ReceiptService.update_receipt(db, receipt.id, user.id, update_data)

    assert updated.store_name == "Updated Store"
    assert updated.total_amount == Decimal("75.50")


def test_update_receipt_items(db: Session):
    """Test updating receipt items."""
    user = create_test_user(db)
    receipt = create_test_receipt(db, user)
    category = create_test_category(db, "bebidas")

    # Create initial items
    item1 = Item(
        receipt_id=receipt.id,
        category_id=category.id,
        product_name="Original Item",
        quantity=1,
        total_price=Decimal("10.00")
    )
    db.add(item1)
    db.commit()

    # Update with new items
    new_items = [
        {
            "product_name": "New Item 1",
            "category": "bebidas",
            "quantity": 2,
            "total_price": 15.00
        },
        {
            "product_name": "New Item 2",
            "category": "carne",
            "quantity": 1,
            "total_price": 25.00
        }
    ]

    update_data = {"items": new_items}
    updated = ReceiptService.update_receipt(db, receipt.id, user.id, update_data)

    # Check old items are deleted and new ones created
    items = list(updated.items.all())
    assert len(items) == 2
    assert items[0].product_name == "New Item 1"
    assert items[1].product_name == "New Item 2"


# Test: Delete receipt

def test_delete_receipt_success(db: Session):
    """Test deleting receipt successfully."""
    user = create_test_user(db)

    # Create receipt with temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(b"test image")
        tmp_path = tmp.name

    receipt = create_test_receipt(db, user)
    receipt.image_path = tmp_path
    db.commit()

    # Delete receipt
    result = ReceiptService.delete_receipt(db, receipt.id, user.id)

    assert result is True

    # Verify it's deleted from database
    found = db.query(Receipt).filter(Receipt.id == receipt.id).first()
    assert found is None

    # Verify file is deleted
    assert not os.path.exists(tmp_path)


def test_delete_receipt_cascades_to_items(db: Session):
    """Test that deleting receipt also deletes items."""
    user = create_test_user(db)
    receipt = create_test_receipt(db, user)
    category = create_test_category(db, "bebidas")

    # Create items
    item1 = Item(
        receipt_id=receipt.id,
        category_id=category.id,
        product_name="Item 1",
        quantity=1,
        total_price=Decimal("10.00")
    )
    item2 = Item(
        receipt_id=receipt.id,
        category_id=category.id,
        product_name="Item 2",
        quantity=1,
        total_price=Decimal("15.00")
    )
    db.add_all([item1, item2])
    db.commit()

    item1_id = item1.id
    item2_id = item2.id

    # Delete receipt
    ReceiptService.delete_receipt(db, receipt.id, user.id)

    # Verify items are deleted
    items = db.query(Item).filter(Item.id.in_([item1_id, item2_id])).all()
    assert len(items) == 0


# Test: Report receipt

def test_report_receipt(db: Session):
    """Test reporting receipt for admin review."""
    user = create_test_user(db)
    receipt = create_test_receipt(db, user)

    # Create review data
    review_data = ReceiptReviewData(
        receipt_id=receipt.id,
        image_path=receipt.image_path,
        analyzer_used="test_analyzer",
        analysis_response='{"test": "data"}',
        reported=False
    )
    db.add(review_data)
    db.commit()

    # Report receipt
    result = ReceiptService.report_receipt(
        db, receipt.id, user.id, message="Analysis incorrect"
    )

    assert result is True

    # Verify review data is updated
    db.refresh(review_data)
    assert review_data.reported is True
    assert review_data.report_message == "Analysis incorrect"


def test_report_receipt_no_review_data(db: Session):
    """Test error when trying to report receipt without review data."""
    user = create_test_user(db)
    receipt = create_test_receipt(db, user)

    # Don't create review data

    with pytest.raises(HTTPException) as exc_info:
        ReceiptService.report_receipt(db, receipt.id, user.id)

    assert exc_info.value.status_code == 404
    assert "review data not found" in exc_info.value.detail.lower()


# Test: Get unique stores

def test_get_unique_stores(db: Session):
    """Test getting unique store names."""
    user = create_test_user(db)

    # Create receipts with different stores
    create_test_receipt(db, user, "Mercadona")
    create_test_receipt(db, user, "Mercadona")  # Duplicate
    create_test_receipt(db, user, "Carrefour")
    create_test_receipt(db, user, "Lidl")
    create_test_receipt(db, user, "Mercadona")  # Another duplicate

    stores = ReceiptService.get_unique_stores(db, user.id)

    # Should have 3 unique stores
    assert len(stores) == 3

    # Should be ordered by frequency (Mercadona=3, Carrefour=1, Lidl=1)
    assert stores[0]["store_name"] == "Mercadona"
    assert stores[0]["count"] == 3

    # Carrefour and Lidl should both have count=1
    store_names = [s["store_name"] for s in stores[1:]]
    assert "Carrefour" in store_names
    assert "Lidl" in store_names


def test_get_unique_stores_empty(db: Session):
    """Test getting stores when user has no receipts."""
    user = create_test_user(db)

    stores = ReceiptService.get_unique_stores(db, user.id)

    assert len(stores) == 0


def test_get_unique_stores_isolation(db: Session):
    """Test that users only see their own stores."""
    user1 = create_test_user(db)

    # Create user2
    user2 = create_test_user(db, username="user2", email="user2@example.com")

    # Create receipts for both users
    create_test_receipt(db, user1, "User1 Store")
    create_test_receipt(db, user2, "User2 Store")

    # Get stores for user1
    stores1 = ReceiptService.get_unique_stores(db, user1.id)

    assert len(stores1) == 1
    assert stores1[0]["store_name"] == "User1 Store"

    # Get stores for user2
    stores2 = ReceiptService.get_unique_stores(db, user2.id)

    assert len(stores2) == 1
    assert stores2[0]["store_name"] == "User2 Store"
