"""
Receipt-related models for SQLAlchemy ORM.
Defines Receipt, Item, and Category models for database persistence.
"""

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship

from backend.database.base import Base


class Category(Base):
    """
    Product category model.

    Attributes:
        id: Primary key
        name: Category name (bebidas, carne, verduras, etc.)
        items: Relationship to Item model (one-to-many)
    """

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)

    # Relationships
    items = relationship("Item", back_populates="category", lazy="dynamic")

    def __repr__(self) -> str:
        """String representation of Category."""
        return f"<Category(id={self.id}, name='{self.name}')>"


class Receipt(Base):
    """
    Receipt model for uploaded grocery receipts.

    Attributes:
        id: Primary key
        user_id: Foreign key to User
        store_name: Name of the store
        purchase_date: Date of purchase
        total_amount: Total amount spent
        image_path: Path to uploaded image
        image_hash: SHA256 hash for duplicate detection
        processed: Whether the receipt has been processed by Claude
        created_at: Timestamp of upload
        user: Relationship to User model
        items: Relationship to Item model (one-to-many)
    """

    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    store_name = Column(String(100), nullable=False, index=True)
    purchase_date = Column(Date, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    image_path = Column(String(255), nullable=False)
    image_hash = Column(String(64), index=True)
    processed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="receipts")
    items = relationship(
        "Item",
        back_populates="receipt",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    def __repr__(self) -> str:
        """String representation of Receipt."""
        return (
            f"<Receipt(id={self.id}, store='{self.store_name}', "
            f"date={self.purchase_date}, total={self.total_amount})>"
        )

    def to_dict(self) -> dict:
        """
        Convert Receipt object to dictionary.

        Returns:
            dict: Receipt data
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "store_name": self.store_name,
            "purchase_date": self.purchase_date.isoformat() if self.purchase_date else None,
            "total_amount": float(self.total_amount) if self.total_amount else 0.0,
            "image_path": self.image_path,
            "processed": self.processed,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Item(Base):
    """
    Individual item from a receipt.

    Attributes:
        id: Primary key
        receipt_id: Foreign key to Receipt
        category_id: Foreign key to Category
        product_name: Name of the product
        quantity: Quantity purchased
        unit_price: Price per unit
        total_price: Total price for this item
        created_at: Timestamp of creation
        receipt: Relationship to Receipt model
        category: Relationship to Category model
    """

    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(Integer, ForeignKey("receipts.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    product_name = Column(String(200), nullable=False, index=True)
    quantity = Column(Numeric(10, 3), default=1.0)
    unit_price = Column(Numeric(10, 2))
    total_price = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    receipt = relationship("Receipt", back_populates="items")
    category = relationship("Category", back_populates="items")

    def __repr__(self) -> str:
        """String representation of Item."""
        return (
            f"<Item(id={self.id}, product='{self.product_name}', "
            f"quantity={self.quantity}, price={self.total_price})>"
        )

    def to_dict(self) -> dict:
        """
        Convert Item object to dictionary.

        Returns:
            dict: Item data
        """
        return {
            "id": self.id,
            "receipt_id": self.receipt_id,
            "category_id": self.category_id,
            "product_name": self.product_name,
            "quantity": float(self.quantity) if self.quantity else 1.0,
            "unit_price": float(self.unit_price) if self.unit_price else None,
            "total_price": float(self.total_price) if self.total_price else 0.0,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ReceiptReviewData(Base):
    """
    Review data for receipts - stores temporary data for admin review.

    This table stores the original image, analyzer used, and raw analysis response
    to allow administrators to review the accuracy of the analysis and test
    different analyzers. Data is periodically cleaned based on retention settings.

    CASCADE BEHAVIOR (IMPORTANT):
    - The CASCADE on receipt_id means: "If a Receipt is deleted, delete its ReceiptReviewData"
    - It does NOT mean: "If ReceiptReviewData is deleted, delete the Receipt"
    - This is a one-way relationship ensuring data integrity
    - When the cleanup process deletes old ReceiptReviewData, the Receipt remains intact

    Attributes:
        id: Primary key
        receipt_id: Foreign key to Receipt
        image_path: Path to the original uploaded image (copy for review)
        analyzer_used: Name of the analyzer that processed this receipt
        analysis_response: Raw JSON response from the analyzer
        reported: Whether this receipt was reported by the user as problematic
        report_message: Optional message from user when reporting
        reviewed_at: Timestamp when admin reviewed this (nullable)
        created_at: Timestamp of creation
        receipt: Relationship to Receipt model
    """

    __tablename__ = "receipt_review_data"

    id = Column(Integer, primary_key=True, index=True)
    # CASCADE direction: Receipt deletion → ReceiptReviewData deletion (NOT the other way)
    receipt_id = Column(Integer, ForeignKey("receipts.id", ondelete="CASCADE"), nullable=False)
    image_path = Column(String(255), nullable=False)
    analyzer_used = Column(String(50), nullable=False, index=True)
    analysis_response = Column(Text, nullable=False)  # JSON string
    reported = Column(Boolean, default=False, nullable=False, index=True)
    report_message = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    receipt = relationship("Receipt", backref="review_data")

    def __repr__(self) -> str:
        """String representation of ReceiptReviewData."""
        return (
            f"<ReceiptReviewData(id={self.id}, receipt_id={self.receipt_id}, "
            f"analyzer='{self.analyzer_used}', reported={self.reported})>"
        )

    def to_dict(self) -> dict:
        """
        Convert ReceiptReviewData object to dictionary.

        Returns:
            dict: Review data
        """
        return {
            "id": self.id,
            "receipt_id": self.receipt_id,
            "image_path": self.image_path,
            "analyzer_used": self.analyzer_used,
            "analysis_response": self.analysis_response,
            "reported": self.reported,
            "report_message": self.report_message,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
