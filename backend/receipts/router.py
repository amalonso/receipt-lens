"""
Receipt router with FastAPI endpoints.
Handles receipt upload, retrieval, and deletion.
"""

import logging
import math
from typing import List

from fastapi import APIRouter, Depends, File, UploadFile, Query, status
from sqlalchemy.orm import Session

from backend.dependencies import get_db, get_current_user
from backend.auth.models import User
from backend.receipts.service import ReceiptService
from backend.receipts.schemas import (
    ReceiptUploadResponse,
    ReceiptDetailResponse,
    ReceiptListResponse,
    ReceiptListItem,
    ReceiptResponse,
    ReceiptUpdateRequest,
    ReportReceiptRequest,
    ItemSchema
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/upload",
    response_model=ReceiptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and analyze receipt",
    description="Upload a receipt image for AI analysis and data extraction"
)
async def upload_receipt(
    file: UploadFile = File(..., description="Receipt image file (JPG, PNG, PDF)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a receipt image for analysis.

    - **file**: Receipt image (max 10MB, formats: jpg, png, pdf)

    The receipt will be analyzed by Claude AI to extract:
    - Store name
    - Purchase date
    - Individual items with categories and prices
    - Total amount

    Returns the created receipt with extracted data.
    """
    logger.info(f"POST /api/receipts/upload - user_id: {current_user.id}, file: {file.filename}")

    try:
        receipt = await ReceiptService.upload_and_analyze_receipt(
            db,
            current_user.id,
            file
        )

        # Get items count
        items_count = receipt.items.count()

        # Create response with items count
        receipt_data = ReceiptUploadResponse(
            id=receipt.id,
            store_name=receipt.store_name,
            purchase_date=receipt.purchase_date,
            total_amount=float(receipt.total_amount),
            image_path=receipt.image_path,
            processed=receipt.processed,
            created_at=receipt.created_at,
            items_count=items_count
        )

        return {
            "success": True,
            "data": {
                "receipt": receipt_data.dict(),
                "message": f"Receipt uploaded and analyzed successfully. {items_count} items extracted."
            },
            "error": None
        }

    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise


@router.post(
    "/upload-multiple",
    response_model=ReceiptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and merge multiple receipt images",
    description="Upload multiple receipt images for a single long receipt. Images will be automatically cropped, merged, and analyzed."
)
async def upload_multiple_receipts(
    files: List[UploadFile] = File(..., description="Multiple receipt image files (JPG, PNG)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload multiple receipt images for a single long receipt.

    This is useful for long receipts (like supermarket receipts) where multiple
    photos are needed to capture all details.

    - **files**: Multiple receipt images (max 10MB each, formats: jpg, png)

    The process:
    1. Each image is automatically cropped to remove background
    2. All images are merged vertically into one
    3. The merged image is analyzed by AI to extract:
       - Store name
       - Purchase date
       - Individual items with categories and prices
       - Total amount

    Returns the created receipt with extracted data.
    """
    logger.info(f"POST /api/receipts/upload-multiple - user_id: {current_user.id}, files: {len(files)}")

    if not files:
        return {
            "success": False,
            "data": None,
            "error": "No files provided"
        }

    if len(files) > 10:
        return {
            "success": False,
            "data": None,
            "error": "Maximum 10 images allowed per receipt"
        }

    try:
        receipt = await ReceiptService.upload_and_analyze_multiple_receipts(
            db,
            current_user.id,
            files
        )

        return {
            "success": True,
            "data": {
                "receipt": ReceiptUploadResponse.from_orm(receipt).dict(),
                "message": f"{len(files)} images merged and analyzed successfully. {len(receipt.items.all())} items extracted."
            },
            "error": None
        }

    except Exception as e:
        logger.error(f"Multiple upload error: {str(e)}")
        raise


@router.get(
    "",
    response_model=ReceiptResponse,
    status_code=status.HTTP_200_OK,
    summary="List user receipts",
    description="Get paginated list of user's receipts"
)
async def list_receipts(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a paginated list of the current user's receipts.

    - **page**: Page number (starting from 1)
    - **page_size**: Number of receipts per page (max 100)

    Returns receipts ordered by purchase date (most recent first).
    """
    logger.info(f"GET /api/receipts - user_id: {current_user.id}, page: {page}, page_size: {page_size}")

    skip = (page - 1) * page_size
    receipts, total = ReceiptService.get_user_receipts(db, current_user.id, skip, page_size)

    # Calculate total pages
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    # Convert to response format
    receipt_items = []
    for receipt in receipts:
        item_count = receipt.items.count()
        receipt_items.append(ReceiptListItem(
            id=receipt.id,
            store_name=receipt.store_name,
            purchase_date=receipt.purchase_date,
            total_amount=float(receipt.total_amount),
            processed=receipt.processed,
            item_count=item_count,
            created_at=receipt.created_at
        ))

    list_response = ReceiptListResponse(
        receipts=receipt_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

    return {
        "success": True,
        "data": list_response.dict(),
        "error": None
    }


@router.get(
    "/{receipt_id}",
    response_model=ReceiptResponse,
    status_code=status.HTTP_200_OK,
    summary="Get receipt details",
    description="Get detailed information about a specific receipt including all items"
)
async def get_receipt(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific receipt.

    - **receipt_id**: Receipt ID

    Returns complete receipt data including all extracted items.
    """
    logger.info(f"GET /api/receipts/{receipt_id} - user_id: {current_user.id}")

    receipt = ReceiptService.get_receipt_by_id(db, receipt_id, current_user.id)

    # Convert items to schema
    items = []
    for item in receipt.items.all():
        items.append(ItemSchema(
            product_name=item.product_name,
            category=item.category.name if item.category else "otros",
            quantity=float(item.quantity) if item.quantity else 1.0,
            unit_price=float(item.unit_price) if item.unit_price else None,
            total_price=float(item.total_price)
        ))

    detail = ReceiptDetailResponse(
        id=receipt.id,
        user_id=receipt.user_id,
        store_name=receipt.store_name,
        purchase_date=receipt.purchase_date,
        total_amount=float(receipt.total_amount),
        image_path=receipt.image_path,
        processed=receipt.processed,
        created_at=receipt.created_at,
        items=items
    )

    return {
        "success": True,
        "data": detail.dict(),
        "error": None
    }


@router.patch(
    "/{receipt_id}",
    response_model=ReceiptResponse,
    status_code=status.HTTP_200_OK,
    summary="Update receipt",
    description="Update a receipt's information (e.g., store name)"
)
async def update_receipt(
    receipt_id: int,
    update_data: ReceiptUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a receipt's information.

    - **receipt_id**: Receipt ID
    - **update_data**: Fields to update

    Currently supports updating:
    - store_name: Store/supermarket name
    """
    logger.info(f"PATCH /api/receipts/{receipt_id} - user_id: {current_user.id}")

    # Convert to dict, excluding None values
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}

    receipt = ReceiptService.update_receipt(db, receipt_id, current_user.id, update_dict)

    # Convert items to schema
    items = []
    for item in receipt.items.all():
        items.append(ItemSchema(
            product_name=item.product_name,
            category=item.category.name if item.category else "otros",
            quantity=float(item.quantity) if item.quantity else 1.0,
            unit_price=float(item.unit_price) if item.unit_price else None,
            total_price=float(item.total_price)
        ))

    detail = ReceiptDetailResponse(
        id=receipt.id,
        user_id=receipt.user_id,
        store_name=receipt.store_name,
        purchase_date=receipt.purchase_date,
        total_amount=float(receipt.total_amount),
        image_path=receipt.image_path,
        processed=receipt.processed,
        created_at=receipt.created_at,
        items=items
    )

    return {
        "success": True,
        "data": detail.dict(),
        "error": None
    }


@router.delete(
    "/{receipt_id}",
    response_model=ReceiptResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete receipt",
    description="Delete a receipt and its associated data"
)
async def delete_receipt(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a receipt.

    - **receipt_id**: Receipt ID

    This will permanently delete the receipt, all associated items,
    and the uploaded image file.
    """
    logger.info(f"DELETE /api/receipts/{receipt_id} - user_id: {current_user.id}")

    ReceiptService.delete_receipt(db, receipt_id, current_user.id)

    return {
        "success": True,
        "data": {
            "message": f"Receipt {receipt_id} deleted successfully"
        },
        "error": None
    }


@router.post(
    "/{receipt_id}/report",
    response_model=ReceiptResponse,
    status_code=status.HTTP_200_OK,
    summary="Report receipt analysis issue",
    description="Report a problem with the receipt analysis for admin review"
)
async def report_receipt(
    receipt_id: int,
    report_data: ReportReceiptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Report a problem with receipt analysis.

    - **receipt_id**: Receipt ID
    - **message**: Optional message describing the issue

    This will mark the receipt for admin review.
    The admin can then review the analysis and test different analyzers.
    """
    logger.info(f"POST /api/receipts/{receipt_id}/report - user_id: {current_user.id}")

    ReceiptService.report_receipt(db, receipt_id, current_user.id, report_data.message)

    return {
        "success": True,
        "data": {
            "message": "Gracias por tu feedback. Tu reporte será revisado por un administrador."
        },
        "error": None
    }
