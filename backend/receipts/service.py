"""
Receipt service with business logic for receipt management.
Handles file upload, Claude AI analysis, and database operations.
"""

import logging
import hashlib
import os
from datetime import datetime, date
from typing import List, Optional, Tuple
from pathlib import Path

from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.config import settings
from backend.receipts.models import Receipt, Item, Category
from backend.receipts.schemas import (
    ClaudeAnalysisResponse,
    ReceiptDetailResponse,
    ReceiptListItem,
    ItemSchema
)
from backend.receipts.analyzer_factory import get_analyzer
from backend.receipts.vision_analyzer import VisionAnalyzerError
from backend.receipts.paddleocr_analyzer import (
    get_paddleocr_analyzer,
    is_paddleocr_available,
    PaddleOCRAnalyzerError
)

logger = logging.getLogger(__name__)


class ReceiptService:
    """Service class for receipt operations."""

    # Maximum file size in bytes (10MB)
    MAX_FILE_SIZE = settings.max_upload_size_mb * 1024 * 1024

    # Allowed file extensions
    ALLOWED_EXTENSIONS = settings.allowed_extensions

    @staticmethod
    def _calculate_file_hash(file_content: bytes) -> str:
        """
        Calculate SHA256 hash of file content.

        Args:
            file_content: Binary file content

        Returns:
            Hexadecimal SHA256 hash
        """
        return hashlib.sha256(file_content).hexdigest()

    @staticmethod
    def _validate_file(file: UploadFile) -> None:
        """
        Validate uploaded file.

        Args:
            file: Uploaded file

        Raises:
            HTTPException: If validation fails
        """
        # Check if file exists
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )

        # Check file extension
        file_ext = Path(file.filename).suffix.lower().lstrip('.')
        if file_ext not in ReceiptService.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(ReceiptService.ALLOWED_EXTENSIONS)}"
            )

        logger.info(f"File validation passed: {file.filename} (.{file_ext})")

    @staticmethod
    async def _save_upload_file(
        file: UploadFile,
        user_id: int,
        upload_dir: str = None
    ) -> Tuple[str, str, bytes]:
        """
        Save uploaded file to disk.

        Args:
            file: Uploaded file
            user_id: User ID (for organizing files)
            upload_dir: Upload directory (defaults to settings.upload_dir)

        Returns:
            Tuple of (file_path, file_hash, file_content)

        Raises:
            HTTPException: If file cannot be saved
        """
        try:
            # Read file content
            file_content = await file.read()

            # Check file size
            if len(file_content) > ReceiptService.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File too large. Maximum size: {settings.max_upload_size_mb}MB"
                )

            # Calculate hash
            file_hash = ReceiptService._calculate_file_hash(file_content)

            # Create upload directory structure
            upload_base = upload_dir or settings.upload_dir
            user_upload_dir = Path(upload_base) / f"user_{user_id}"
            user_upload_dir.mkdir(parents=True, exist_ok=True)

            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_ext = Path(file.filename).suffix
            filename = f"{timestamp}_{file_hash[:8]}{file_ext}"
            file_path = user_upload_dir / filename

            # Save file
            with open(file_path, 'wb') as f:
                f.write(file_content)

            logger.info(f"File saved: {file_path} (hash: {file_hash[:16]}...)")
            return str(file_path), file_hash, file_content

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {str(e)}"
            )

    @staticmethod
    def _check_duplicate(db: Session, user_id: int, file_hash: str) -> Optional[Receipt]:
        """
        Check if receipt with same hash already exists for user.

        Args:
            db: Database session
            user_id: User ID
            file_hash: File hash

        Returns:
            Existing receipt or None
        """
        return db.query(Receipt).filter(
            Receipt.user_id == user_id,
            Receipt.image_hash == file_hash
        ).first()

    @staticmethod
    def _get_or_create_category(db: Session, category_name: str) -> Category:
        """
        Get or create a category by name.

        Args:
            db: Database session
            category_name: Category name

        Returns:
            Category object
        """
        category = db.query(Category).filter(
            Category.name == category_name.lower()
        ).first()

        if not category:
            # Category should exist from init.sql, but create if not
            category = Category(name=category_name.lower())
            db.add(category)
            db.flush()
            logger.warning(f"Created missing category: {category_name}")

        return category

    @staticmethod
    async def upload_and_analyze_receipt(
        db: Session,
        user_id: int,
        file: UploadFile
    ) -> Receipt:
        """
        Upload receipt image, analyze with Claude, and save to database.

        Args:
            db: Database session
            user_id: User ID
            file: Uploaded file

        Returns:
            Receipt object

        Raises:
            HTTPException: If upload or analysis fails
        """
        logger.info(f"Processing receipt upload for user {user_id}: {file.filename}")

        # Validate file
        ReceiptService._validate_file(file)

        # Save file
        file_path, file_hash, file_content = await ReceiptService._save_upload_file(
            file, user_id
        )

        try:
            # Check for duplicates
            existing = ReceiptService._check_duplicate(db, user_id, file_hash)
            if existing:
                logger.warning(f"Duplicate receipt detected: {file_hash}")
                # Delete newly uploaded file
                os.remove(file_path)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"This receipt has already been uploaded (Receipt ID: {existing.id})"
                )

            # Determine which analyzer to use
            use_claude = settings.anthropic_api_key is not None

            if use_claude:
                # Analyze with Claude
                logger.info("Starting Claude AI analysis...")
                try:
                    analyzer = get_analyzer()
                    analysis = await analyzer.analyze_receipt(file_path)
                    # Validate analysis
                    analyzer.validate_analysis(analysis)
                except VisionAnalyzerError as vision_error:
                    # If vision API fails and PaddleOCR is available, fallback
                    if is_paddleocr_available():
                        logger.warning(f"Vision API analysis failed, falling back to PaddleOCR: {str(vision_error)}")
                        use_claude = False
                    else:
                        raise

            if not use_claude:
                # Use PaddleOCR fallback
                if not is_paddleocr_available():
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="No analysis service available. Please configure ANTHROPIC_API_KEY or install PaddleOCR."
                    )

                logger.info("Starting PaddleOCR analysis (local fallback)...")
                paddleocr_analyzer = get_paddleocr_analyzer()
                analysis = await paddleocr_analyzer.analyze_receipt(file_path)

            # Parse date
            try:
                purchase_date = datetime.strptime(analysis.purchase_date, '%Y-%m-%d').date()
            except ValueError:
                logger.warning(f"Invalid date from Claude: {analysis.purchase_date}, using today")
                purchase_date = date.today()

            # Create receipt
            receipt = Receipt(
                user_id=user_id,
                store_name=analysis.store_name,
                purchase_date=purchase_date,
                total_amount=analysis.total_amount,
                image_path=file_path,
                image_hash=file_hash,
                processed=True
            )

            db.add(receipt)
            db.flush()  # Get receipt ID

            logger.info(f"Created receipt: ID={receipt.id}, store={receipt.store_name}")

            # Create items
            for item_data in analysis.items:
                # Get or create category
                category = ReceiptService._get_or_create_category(db, item_data.category)

                item = Item(
                    receipt_id=receipt.id,
                    category_id=category.id,
                    product_name=item_data.product_name,
                    quantity=item_data.quantity,
                    unit_price=item_data.unit_price,
                    total_price=item_data.total_price
                )
                db.add(item)

            # Commit transaction
            db.commit()
            db.refresh(receipt)

            logger.info(
                f"Receipt processed successfully: {len(analysis.items)} items saved"
            )

            return receipt

        except HTTPException:
            db.rollback()
            # Delete uploaded file on error
            if os.path.exists(file_path):
                os.remove(file_path)
            raise


        except (VisionAnalyzerError, PaddleOCRAnalyzerError) as e:
            db.rollback()
            # Delete uploaded file on error
            if os.path.exists(file_path):
                os.remove(file_path)
            logger.error(f"Vision analysis error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Could not analyze receipt: {str(e)}"
            )

        except Exception as e:
            db.rollback()
            # Delete uploaded file on error
            if os.path.exists(file_path):
                os.remove(file_path)
            logger.error(f"Unexpected error processing receipt: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process receipt: {str(e)}"
            )

    @staticmethod
    def get_user_receipts(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Receipt], int]:
        """
        Get paginated list of user's receipts.

        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (receipts list, total count)
        """
        query = db.query(Receipt).filter(Receipt.user_id == user_id)

        total = query.count()

        receipts = query.order_by(
            Receipt.purchase_date.desc(),
            Receipt.created_at.desc()
        ).offset(skip).limit(limit).all()

        logger.info(f"Retrieved {len(receipts)} receipts for user {user_id} (total: {total})")

        return receipts, total

    @staticmethod
    def get_receipt_by_id(
        db: Session,
        receipt_id: int,
        user_id: int
    ) -> Optional[Receipt]:
        """
        Get a specific receipt by ID (with user ownership check).

        Args:
            db: Database session
            receipt_id: Receipt ID
            user_id: User ID (for ownership verification)

        Returns:
            Receipt object or None

        Raises:
            HTTPException: If receipt not found or access denied
        """
        receipt = db.query(Receipt).filter(
            Receipt.id == receipt_id
        ).first()

        if not receipt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receipt not found"
            )

        if receipt.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this receipt"
            )

        return receipt

    @staticmethod
    def delete_receipt(
        db: Session,
        receipt_id: int,
        user_id: int
    ) -> bool:
        """
        Delete a receipt and its associated file.

        Args:
            db: Database session
            receipt_id: Receipt ID
            user_id: User ID (for ownership verification)

        Returns:
            True if deleted successfully

        Raises:
            HTTPException: If receipt not found or access denied
        """
        receipt = ReceiptService.get_receipt_by_id(db, receipt_id, user_id)

        # Delete file from disk
        if os.path.exists(receipt.image_path):
            try:
                os.remove(receipt.image_path)
                logger.info(f"Deleted receipt file: {receipt.image_path}")
            except Exception as e:
                logger.warning(f"Could not delete file {receipt.image_path}: {str(e)}")

        # Delete from database (cascade will delete items)
        db.delete(receipt)
        db.commit()

        logger.info(f"Deleted receipt ID={receipt_id} for user {user_id}")

        return True
