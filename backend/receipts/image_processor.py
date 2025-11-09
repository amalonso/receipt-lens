"""
Image processing utilities for receipt images.

This module provides functions to:
- Detect and crop receipt borders automatically
- Merge multiple receipt images vertically
- Pre-process images before AI analysis
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ReceiptImageProcessor:
    """Processor for receipt images with automatic border detection and merging."""

    @staticmethod
    def detect_and_crop_receipt(image_path: str, margin: int = 10) -> np.ndarray:
        """
        Detect receipt borders and crop the image automatically.

        Args:
            image_path: Path to the receipt image
            margin: Additional margin in pixels around detected borders

        Returns:
            Cropped image as numpy array
        """
        logger.info(f"Processing image: {image_path}")

        # Read image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not read image: {image_path}")

        original_height, original_width = image.shape[:2]
        logger.debug(f"Original size: {original_width}x{original_height}")

        # Create a copy for processing
        processed = image.copy()

        # Convert to grayscale
        gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Apply adaptive thresholding for better edge detection
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )

        # Find contours
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            logger.warning("No contours found, returning original image")
            return image

        # Find the largest contour (assumed to be the receipt)
        largest_contour = max(contours, key=cv2.contourArea)
        contour_area = cv2.contourArea(largest_contour)
        image_area = original_width * original_height

        # If the largest contour is too small, it's probably not the receipt
        if contour_area < image_area * 0.1:
            logger.warning(f"Largest contour too small ({contour_area / image_area:.1%} of image), returning original")
            return image

        # Get bounding rectangle of the largest contour
        x, y, w, h = cv2.boundingRect(largest_contour)

        logger.debug(f"Detected receipt area: x={x}, y={y}, w={w}, h={h}")

        # Add margin and ensure we don't go out of bounds
        x1 = max(0, x - margin)
        y1 = max(0, y - margin)
        x2 = min(original_width, x + w + margin)
        y2 = min(original_height, y + h + margin)

        # Crop the image
        cropped = image[y1:y2, x1:x2]

        logger.info(f"Cropped to: {cropped.shape[1]}x{cropped.shape[0]} (reduced by {((1 - (cropped.shape[0] * cropped.shape[1]) / image_area) * 100):.1f}%)")

        return cropped

    @staticmethod
    def merge_images_vertically(images: List[np.ndarray], spacing: int = 20) -> np.ndarray:
        """
        Merge multiple images vertically into a single image.

        Args:
            images: List of images as numpy arrays
            spacing: Spacing in pixels between images

        Returns:
            Merged image as numpy array
        """
        if not images:
            raise ValueError("No images provided for merging")

        if len(images) == 1:
            logger.info("Only one image provided, returning as-is")
            return images[0]

        logger.info(f"Merging {len(images)} images vertically")

        # Find maximum width among all images
        max_width = max(img.shape[1] for img in images)

        # Calculate total height
        total_height = sum(img.shape[0] for img in images) + spacing * (len(images) - 1)

        logger.debug(f"Merged image will be: {max_width}x{total_height}")

        # Create a white canvas
        merged = np.ones((total_height, max_width, 3), dtype=np.uint8) * 255

        # Place each image on the canvas
        current_y = 0
        for i, img in enumerate(images):
            h, w = img.shape[:2]

            # Center the image horizontally
            x_offset = (max_width - w) // 2

            # Place image
            merged[current_y:current_y + h, x_offset:x_offset + w] = img

            logger.debug(f"Image {i + 1} placed at y={current_y}, size={w}x{h}")

            # Move to next position
            current_y += h + spacing

        logger.info(f"Successfully merged {len(images)} images into {max_width}x{total_height}")

        return merged

    @staticmethod
    def process_multiple_receipts(
        image_paths: List[str],
        output_path: str,
        crop: bool = True,
        margin: int = 10,
        spacing: int = 20
    ) -> str:
        """
        Process multiple receipt images: crop and merge them.

        Args:
            image_paths: List of paths to receipt images
            output_path: Path where the merged image will be saved
            crop: Whether to crop individual images before merging
            margin: Margin around detected borders when cropping
            spacing: Spacing between images when merging

        Returns:
            Path to the merged image file
        """
        logger.info(f"Processing {len(image_paths)} receipt images")

        processed_images = []

        for i, image_path in enumerate(image_paths):
            logger.info(f"Processing image {i + 1}/{len(image_paths)}: {Path(image_path).name}")

            if crop:
                # Detect and crop receipt
                cropped = ReceiptImageProcessor.detect_and_crop_receipt(image_path, margin)
                processed_images.append(cropped)
            else:
                # Just read the image
                img = cv2.imread(image_path)
                if img is None:
                    logger.error(f"Could not read image: {image_path}")
                    raise ValueError(f"Could not read image: {image_path}")
                processed_images.append(img)

        # Merge all images
        merged = ReceiptImageProcessor.merge_images_vertically(processed_images, spacing)

        # Save merged image
        success = cv2.imwrite(output_path, merged)

        if not success:
            raise IOError(f"Failed to save merged image to: {output_path}")

        logger.info(f"Merged image saved to: {output_path}")

        return output_path

    @staticmethod
    def enhance_receipt_image(image: np.ndarray) -> np.ndarray:
        """
        Enhance receipt image for better OCR/AI analysis.

        Args:
            image: Input image as numpy array

        Returns:
            Enhanced image
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray)

        # Apply adaptive histogram equalization for better contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)

        # Convert back to BGR for consistency
        enhanced_bgr = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

        return enhanced_bgr
