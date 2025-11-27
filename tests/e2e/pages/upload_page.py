"""
Upload Page Object for receipt upload and analysis.
"""

from .base_page import BasePage
from playwright.sync_api import Page
from pathlib import Path
from typing import Optional


class UploadPage(BasePage):
    """Page Object for upload page."""

    # Selectors
    FILE_INPUT = '#file-input'
    DROPZONE = '#dropzone'
    PREVIEW_CONTAINER = '#preview-container'
    IMAGE_PREVIEW = '#image-preview'
    UPLOAD_BTN = '#upload-btn'
    UPLOAD_BTN_MULTIPLE = '#upload-btn-multiple'
    PROGRESS_BAR = '#progress-bar'
    PROGRESS_FILL = '#progress-fill'
    ANALYSIS_RESULT = '#analysis-result'
    RESULT_STATS = '#result-stats'
    ITEMS_PREVIEW = '#items-preview'
    EDIT_BTN = '#edit-btn'
    DISCARD_BTN = '#discard-btn'

    # Mode switching
    SINGLE_MODE_BTN = '#single-mode-btn'
    MULTIPLE_MODE_BTN = '#multiple-mode-btn'
    MULTIPLE_PREVIEW_CONTAINER = '#multiple-preview-container'

    def __init__(self, page: Page, base_url: str):
        """
        Initialize the upload page.

        Args:
            page: Playwright page instance
            base_url: Base URL of the application
        """
        super().__init__(page, base_url)

    def navigate(self) -> None:
        """Navigate to the upload page."""
        self.navigate_to("upload.html")
        self.wait_for_navigation()

    def is_on_upload_page(self) -> bool:
        """
        Check if currently on the upload page.

        Returns:
            True if on upload page, False otherwise
        """
        return "upload.html" in self.get_current_url() and self.is_visible(self.DROPZONE)

    def select_single_mode(self) -> None:
        """Switch to single image upload mode."""
        self.click_element(self.SINGLE_MODE_BTN)
        self.page.wait_for_timeout(500)

    def select_multiple_mode(self) -> None:
        """Switch to multiple images upload mode."""
        self.click_element(self.MULTIPLE_MODE_BTN)
        self.page.wait_for_timeout(500)

    def upload_file(self, file_path: str) -> None:
        """
        Upload a single file by selecting it through file input.

        Args:
            file_path: Absolute path to the file to upload
        """
        # Ensure we're in single mode
        self.select_single_mode()

        # Set file to input
        self.page.set_input_files(self.FILE_INPUT, file_path)

        # Wait for preview to appear
        self.wait_for_selector(self.PREVIEW_CONTAINER, state="visible")

    def upload_multiple_files(self, file_paths: list[str]) -> None:
        """
        Upload multiple files for stitching.

        Args:
            file_paths: List of absolute paths to files to upload
        """
        # Ensure we're in multiple mode
        self.select_multiple_mode()

        # Set files to input
        self.page.set_input_files(self.FILE_INPUT, file_paths)

        # Wait for multiple preview container to appear
        self.wait_for_selector(self.MULTIPLE_PREVIEW_CONTAINER, state="visible")

    def click_analyze_button(self) -> None:
        """Click the analyze button to start processing the receipt."""
        if self.is_visible(self.UPLOAD_BTN):
            self.click_element(self.UPLOAD_BTN)
        elif self.is_visible(self.UPLOAD_BTN_MULTIPLE):
            self.click_element(self.UPLOAD_BTN_MULTIPLE)

        # Wait for processing to start
        self.page.wait_for_timeout(1000)

    def wait_for_analysis_complete(self, timeout: int = 60000) -> bool:
        """
        Wait for the analysis to complete and results to appear.

        Args:
            timeout: Maximum time to wait in milliseconds

        Returns:
            True if analysis completed successfully, False otherwise
        """
        try:
            # Wait for analysis result container to become visible
            self.wait_for_selector(f"{self.ANALYSIS_RESULT}.active", timeout=timeout)
            return True
        except Exception:
            return False

    def get_analysis_results(self) -> dict:
        """
        Extract analysis results from the page.

        Returns:
            Dictionary with total, items_count, and store_name
        """
        if not self.is_visible(self.ANALYSIS_RESULT):
            return {}

        # Wait for stats to be populated
        self.page.wait_for_timeout(500)

        # Extract stats from result-stat elements
        stats = self.page.query_selector_all(f"{self.RESULT_STATS} .result-stat")

        results = {
            'total': '',
            'items_count': '',
            'store_name': ''
        }

        if len(stats) >= 3:
            # Total
            total_value = stats[0].query_selector('.result-stat-value')
            if total_value:
                results['total'] = total_value.inner_text()

            # Items count
            items_value = stats[1].query_selector('.result-stat-value')
            if items_value:
                results['items_count'] = items_value.inner_text()

            # Store name
            store_value = stats[2].query_selector('.result-stat-value')
            if store_value:
                results['store_name'] = store_value.inner_text()

        return results

    def get_detected_items(self) -> list[dict]:
        """
        Get list of detected items from the preview.

        Returns:
            List of dictionaries with item information
        """
        if not self.is_visible(self.ITEMS_PREVIEW):
            return []

        items = []
        # This is a simplified extraction - adjust based on actual HTML structure
        items_text = self.get_text(self.ITEMS_PREVIEW)

        return items  # TODO: Parse items if needed for specific tests

    def is_analysis_result_visible(self) -> bool:
        """
        Check if analysis results are displayed.

        Returns:
            True if results are visible, False otherwise
        """
        return self.is_visible(f"{self.ANALYSIS_RESULT}.active")

    def click_edit_button(self) -> None:
        """Click the edit button to navigate to edit page."""
        self.click_element(self.EDIT_BTN)
        self.wait_for_navigation()

    def click_discard_button(self) -> None:
        """Click the discard button and confirm the action."""
        self.click_element(self.DISCARD_BTN)

        # Handle confirmation dialog
        self.page.on("dialog", lambda dialog: dialog.accept())
        self.page.wait_for_timeout(1000)

    def is_upload_button_visible(self) -> bool:
        """
        Check if upload/analyze button is visible.

        Returns:
            True if button is visible, False otherwise
        """
        return self.is_visible(self.UPLOAD_BTN) or self.is_visible(self.UPLOAD_BTN_MULTIPLE)

    def upload_and_analyze(self, file_path: str, timeout: int = 60000) -> dict:
        """
        Complete flow: upload file and wait for analysis results.

        Args:
            file_path: Path to the file to upload
            timeout: Maximum time to wait for analysis

        Returns:
            Dictionary with analysis results
        """
        # Upload the file
        self.upload_file(file_path)

        # Click analyze button
        self.click_analyze_button()

        # Wait for analysis to complete
        if not self.wait_for_analysis_complete(timeout=timeout):
            return {}

        # Get results
        return self.get_analysis_results()

    def is_preview_visible(self) -> bool:
        """
        Check if file preview is visible after upload.

        Returns:
            True if preview is visible, False otherwise
        """
        return self.is_visible(self.PREVIEW_CONTAINER)
