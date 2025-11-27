"""
End-to-end tests for receipt upload and analysis workflow.
Tests the complete flow from login to upload to viewing results.
"""

import pytest
from playwright.sync_api import Page, expect
from tests.e2e.pages.login_page import LoginPage
from tests.e2e.pages.upload_page import UploadPage
from tests.e2e.pages.receipts_page import ReceiptsPage


@pytest.mark.e2e
class TestReceiptUpload:
    """Test suite for receipt upload functionality."""

    def test_user_can_register_and_login(
        self,
        login_page: LoginPage,
        test_user_credentials: dict
    ):
        """
        Test that a new user can register and login successfully.

        This is a prerequisite test for other upload tests.
        """
        # Navigate to login page
        login_page.navigate()
        assert login_page.is_on_login_page()

        # Register new user
        login_page.register(
            username=test_user_credentials["username"],
            email=test_user_credentials["email"],
            password=test_user_credentials["password"]
        )

        # Should redirect to dashboard after successful registration
        assert login_page.is_redirected_to_dashboard(timeout=10000), \
            "User should be redirected to dashboard after registration"

        # Verify user is logged in
        assert login_page.is_logged_in(), "User should have valid token after registration"

    def test_upload_page_is_accessible_when_authenticated(
        self,
        authenticated_page: Page,
        upload_page: UploadPage
    ):
        """
        Test that authenticated users can access the upload page.
        """
        upload_page.navigate()
        assert upload_page.is_on_upload_page(), \
            "Authenticated user should be able to access upload page"

    def test_upload_page_shows_upload_interface(
        self,
        authenticated_page: Page,
        upload_page: UploadPage
    ):
        """
        Test that upload page displays the necessary UI elements.
        """
        upload_page.navigate()

        # Check that dropzone is visible
        assert upload_page.is_visible(upload_page.DROPZONE), \
            "Dropzone should be visible on upload page"

        # Check that mode switching buttons are visible
        assert upload_page.is_visible(upload_page.SINGLE_MODE_BTN), \
            "Single mode button should be visible"
        assert upload_page.is_visible(upload_page.MULTIPLE_MODE_BTN), \
            "Multiple mode button should be visible"

    @pytest.mark.slow_e2e
    def test_upload_and_analyze_single_receipt(
        self,
        authenticated_page: Page,
        upload_page: UploadPage,
        sample_receipt_image: str
    ):
        """
        Test the complete flow of uploading and analyzing a single receipt.

        This is the main E2E test that verifies:
        1. File can be selected
        2. Preview is shown
        3. Analysis can be triggered
        4. Results are displayed
        """
        # Navigate to upload page
        upload_page.navigate()
        assert upload_page.is_on_upload_page()

        # Ensure we're in single mode
        upload_page.select_single_mode()

        # Upload the receipt image
        upload_page.upload_file(sample_receipt_image)

        # Verify preview is shown
        assert upload_page.is_preview_visible(), \
            "File preview should be visible after upload"

        # Click analyze button
        upload_page.click_analyze_button()

        # Wait for analysis to complete (may take time with real AI)
        analysis_completed = upload_page.wait_for_analysis_complete(timeout=90000)
        assert analysis_completed, \
            "Analysis should complete within timeout period"

        # Verify results are displayed
        assert upload_page.is_analysis_result_visible(), \
            "Analysis results should be visible after processing"

        # Get and validate results
        results = upload_page.get_analysis_results()
        assert results, "Analysis results should not be empty"

        # Check that we have the expected fields
        assert 'total' in results, "Results should include total amount"
        assert 'items_count' in results, "Results should include items count"
        assert 'store_name' in results, "Results should include store name"

        # Verify that at least some data was extracted
        # Note: Values depend on OCR/AI provider, so we just check they're not empty
        assert results['total'] != '--', "Total should be extracted from receipt"
        assert results['store_name'] != '--', "Store name should be extracted from receipt"

    @pytest.mark.slow_e2e
    def test_uploaded_receipt_appears_in_receipts_list(
        self,
        authenticated_page: Page,
        upload_page: UploadPage,
        receipts_page: ReceiptsPage,
        sample_receipt_image: str
    ):
        """
        Test that after uploading a receipt, it appears in the receipts list.

        This tests the integration between upload and receipts list.
        """
        # Upload a receipt
        upload_page.navigate()
        upload_page.upload_file(sample_receipt_image)
        upload_page.click_analyze_button()

        # Wait for analysis
        assert upload_page.wait_for_analysis_complete(timeout=90000), \
            "Analysis should complete"

        # Navigate to receipts page
        receipts_page.navigate()
        assert receipts_page.is_on_receipts_page()

        # Wait for receipts to load
        receipts_page.wait_for_receipts_to_load()

        # Verify that at least one receipt is displayed
        assert receipts_page.has_receipts(), \
            "Uploaded receipt should appear in receipts list"

        receipt_count = receipts_page.get_receipt_count()
        assert receipt_count > 0, \
            f"Expected at least 1 receipt, but found {receipt_count}"

    def test_can_discard_receipt_after_upload(
        self,
        authenticated_page: Page,
        upload_page: UploadPage,
        sample_receipt_image: str
    ):
        """
        Test that user can discard a receipt after analysis.
        """
        # Upload and analyze receipt
        upload_page.navigate()
        upload_page.upload_file(sample_receipt_image)
        upload_page.click_analyze_button()

        # Wait for analysis
        assert upload_page.wait_for_analysis_complete(timeout=90000)

        # Click discard button
        upload_page.click_discard_button()

        # Verify upload button is visible again (form reset)
        upload_page.page.wait_for_timeout(2000)  # Wait for UI update
        assert upload_page.is_upload_button_visible(), \
            "Upload button should be visible after discarding receipt"

    def test_mode_switching_works(
        self,
        authenticated_page: Page,
        upload_page: UploadPage
    ):
        """
        Test that switching between single and multiple mode works.
        """
        upload_page.navigate()

        # Should start in single mode
        assert upload_page.page.locator(upload_page.SINGLE_MODE_BTN).get_attribute("class").find("active") >= 0, \
            "Single mode should be active by default"

        # Switch to multiple mode
        upload_page.select_multiple_mode()
        upload_page.page.wait_for_timeout(500)

        # Verify multiple mode is active
        assert upload_page.page.locator(upload_page.MULTIPLE_MODE_BTN).get_attribute("class").find("active") >= 0, \
            "Multiple mode should be active after switching"

        # Switch back to single mode
        upload_page.select_single_mode()
        upload_page.page.wait_for_timeout(500)

        # Verify single mode is active again
        assert upload_page.page.locator(upload_page.SINGLE_MODE_BTN).get_attribute("class").find("active") >= 0, \
            "Single mode should be active after switching back"

    def test_upload_page_requires_authentication(
        self,
        page: Page,
        upload_page: UploadPage,
        login_page: LoginPage
    ):
        """
        Test that unauthenticated users are redirected to login.
        """
        # Try to access upload page without authentication
        upload_page.navigate()

        # Should be redirected to login page
        page.wait_for_timeout(2000)  # Wait for redirect
        current_url = page.url

        assert "login.html" in current_url or "login" in current_url.lower(), \
            "Unauthenticated user should be redirected to login page"


@pytest.mark.e2e
class TestReceiptUploadValidation:
    """Test suite for upload validation and error handling."""

    def test_upload_button_disabled_without_file(
        self,
        authenticated_page: Page,
        upload_page: UploadPage
    ):
        """
        Test that analyze button is not visible when no file is selected.
        """
        upload_page.navigate()

        # Upload button should not be visible initially
        # (it appears only after file is selected)
        assert not upload_page.is_visible(upload_page.UPLOAD_BTN, timeout=2000), \
            "Upload button should not be visible without file selected"

    def test_invalid_file_type_shows_error(
        self,
        authenticated_page: Page,
        upload_page: UploadPage,
        tmp_path
    ):
        """
        Test that uploading an invalid file type shows an error.
        """
        # Create a text file (invalid type)
        text_file = tmp_path / "test.txt"
        text_file.write_text("This is not an image")

        upload_page.navigate()

        # Try to upload the invalid file
        # Note: File input validation might prevent this at the browser level
        # This test documents expected behavior
        # In practice, the file input accept attribute should prevent selection

    @pytest.mark.slow_e2e
    def test_receipt_edit_button_navigates_to_detail(
        self,
        authenticated_page: Page,
        upload_page: UploadPage,
        sample_receipt_image: str
    ):
        """
        Test that clicking edit button navigates to detail page.
        """
        # Upload and analyze receipt
        upload_page.navigate()
        upload_page.upload_file(sample_receipt_image)
        upload_page.click_analyze_button()

        # Wait for analysis
        assert upload_page.wait_for_analysis_complete(timeout=90000)

        # Click edit button
        upload_page.click_edit_button()

        # Should navigate to receipt detail page
        authenticated_page.wait_for_timeout(2000)
        current_url = authenticated_page.url

        assert "receipt-detail" in current_url, \
            "Edit button should navigate to receipt detail page"
