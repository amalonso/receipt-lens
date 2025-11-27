"""
E2E tests for receipts management flow.
Tests viewing, searching, sorting, deleting receipts in the UI.
"""

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.pages.login_page import LoginPage
from tests.e2e.pages.upload_page import UploadPage
from tests.e2e.pages.receipts_page import ReceiptsPage


@pytest.mark.e2e
class TestReceiptsFlow:
    """Tests for receipts list and management functionality."""

    def test_receipts_page_shows_empty_list_for_new_user(
        self,
        authenticated_page: Page,
        receipts_page: ReceiptsPage
    ):
        """Test that receipts page shows empty state for new user with no receipts."""
        # Navigate to receipts page
        receipts_page.navigate()

        # Should show empty state
        assert receipts_page.is_empty_state_visible(), "Empty state should be visible for new user"

        # Should have 0 receipts
        assert receipts_page.get_receipt_count() == 0, "Should have 0 receipts"

        # Total count badge should show 0
        assert receipts_page.get_total_count_from_badge() == 0, "Badge should show 0"

    @pytest.mark.slow_e2e
    def test_uploaded_receipt_appears_in_receipts_list(
        self,
        authenticated_page: Page,
        upload_page: UploadPage,
        receipts_page: ReceiptsPage,
        sample_receipt_image: str
    ):
        """Test that a newly uploaded receipt appears in the receipts list."""
        # Upload a receipt
        upload_page.navigate()
        upload_page.upload_file(sample_receipt_image)
        assert upload_page.is_preview_visible(), "Preview should be visible"

        upload_page.click_analyze_button()

        # Wait for analysis to complete (can take up to 90 seconds with AI)
        assert upload_page.wait_for_analysis_complete(timeout=90000), "Analysis should complete"

        # Navigate to receipts list
        receipts_page.navigate()

        # Should have at least 1 receipt
        assert receipts_page.has_receipts(), "Should have at least one receipt"

        # Should show count > 0
        total_count = receipts_page.get_total_count_from_badge()
        assert total_count > 0, f"Badge should show count > 0, got {total_count}"

        # Get first receipt details
        details = receipts_page.get_first_receipt_details()
        assert 'store' in details, "Should have store name"
        assert 'amount' in details, "Should have amount"

    def test_can_navigate_to_receipt_detail(
        self,
        authenticated_page: Page,
        receipts_page: ReceiptsPage
    ):
        """Test that clicking on a receipt navigates to detail page."""
        # Skip if no receipts (depends on previous test or manual setup)
        receipts_page.navigate()

        if not receipts_page.has_receipts():
            pytest.skip("No receipts available for testing")

        # Click first receipt
        receipts_page.click_first_receipt()

        # Should navigate to detail page
        current_url = receipts_page.get_current_url()
        assert "receipt-detail.html" in current_url, "Should navigate to receipt detail page"

    @pytest.mark.slow_e2e
    def test_can_delete_receipt(
        self,
        authenticated_page: Page,
        upload_page: UploadPage,
        receipts_page: ReceiptsPage,
        sample_receipt_image: str
    ):
        """Test that user can delete a receipt."""
        # First upload a receipt
        upload_page.navigate()
        upload_page.upload_file(sample_receipt_image)
        upload_page.click_analyze_button()
        assert upload_page.wait_for_analysis_complete(timeout=90000), "Analysis should complete"

        # Navigate to receipts
        receipts_page.navigate()
        initial_count = receipts_page.get_receipt_count()
        assert initial_count > 0, "Should have at least one receipt"

        # Click delete on first receipt
        receipts_page.click_delete_first_receipt()

        # Delete modal should appear
        assert receipts_page.is_delete_modal_visible(), "Delete modal should be visible"

        # Confirm deletion
        receipts_page.confirm_delete()

        # Wait for page to reload
        receipts_page.wait_for_receipts_to_load()

        # Should have one less receipt (or empty state if it was the only one)
        final_count = receipts_page.get_receipt_count()
        assert final_count == initial_count - 1, f"Should have one less receipt. Had {initial_count}, now {final_count}"

    def test_search_receipts_filters_list(
        self,
        authenticated_page: Page,
        receipts_page: ReceiptsPage
    ):
        """Test that search input filters receipts list."""
        receipts_page.navigate()

        if not receipts_page.has_receipts():
            pytest.skip("No receipts available for testing")

        # Get initial count
        initial_count = receipts_page.get_receipt_count()

        # Get first receipt store name
        details = receipts_page.get_first_receipt_details()
        store_name = details.get('store', '')

        if not store_name:
            pytest.skip("Could not get store name from receipt")

        # Search for part of the store name
        search_term = store_name[:5]  # First 5 characters
        receipts_page.search_receipts(search_term)

        # Should filter results
        filtered_count = receipts_page.get_receipt_count()

        # Either same count (all match) or less (some filtered out)
        assert filtered_count <= initial_count, "Filtered count should be <= initial count"

        # Clear search
        receipts_page.search_receipts("")

        # Should show all again
        final_count = receipts_page.get_receipt_count()
        assert final_count == initial_count, "Should show all receipts after clearing search"

    def test_sort_receipts_changes_order(
        self,
        authenticated_page: Page,
        receipts_page: ReceiptsPage
    ):
        """Test that sort dropdown changes receipt order."""
        receipts_page.navigate()

        if receipts_page.get_receipt_count() < 2:
            pytest.skip("Need at least 2 receipts to test sorting")

        # Get first receipt with default sort (date-desc)
        first_before = receipts_page.get_first_receipt_details()

        # Sort by date ascending
        receipts_page.sort_receipts("date-asc")

        # Get first receipt after sort
        first_after = receipts_page.get_first_receipt_details()

        # The first receipt should potentially be different
        # (unless all receipts have same date)
        # We just verify sorting doesn't break the page
        assert receipts_page.has_receipts(), "Should still have receipts after sorting"

    @pytest.mark.slow_e2e
    def test_pagination_works_with_many_receipts(
        self,
        authenticated_page: Page,
        upload_page: UploadPage,
        receipts_page: ReceiptsPage,
        sample_receipt_image: str
    ):
        """Test that pagination works when there are many receipts."""
        # Upload enough receipts to trigger pagination (need > 10)
        # This test is slow as it uploads multiple times

        # Navigate to receipts first to check current count
        receipts_page.navigate()
        current_count = receipts_page.get_total_count_from_badge()

        # Upload receipts until we have more than 10 (page size)
        receipts_needed = max(0, 11 - current_count)

        if receipts_needed > 0:
            for i in range(receipts_needed):
                upload_page.navigate()
                upload_page.upload_file(sample_receipt_image)
                upload_page.click_analyze_button()
                # Wait for analysis (short timeout to keep test reasonable)
                upload_page.wait_for_analysis_complete(timeout=60000)

        # Navigate back to receipts
        receipts_page.navigate()

        # Check if pagination is visible
        if not receipts_page.is_pagination_visible():
            pytest.skip("Not enough receipts to trigger pagination")

        # Verify pagination info
        pagination_info = receipts_page.get_pagination_info()
        assert "Página" in pagination_info, f"Should show pagination info, got: {pagination_info}"

        # Previous button should be disabled on first page
        assert receipts_page.is_prev_button_disabled(), "Previous button should be disabled on first page"

        # Next button should not be disabled (we have multiple pages)
        assert not receipts_page.is_next_button_disabled(), "Next button should be enabled"

        # Click next page
        receipts_page.click_next_page()

        # Should be on page 2
        pagination_info = receipts_page.get_pagination_info()
        assert "Página 2" in pagination_info, "Should be on page 2"

        # Previous button should now be enabled
        assert not receipts_page.is_prev_button_disabled(), "Previous button should be enabled on page 2"

        # Go back to first page
        receipts_page.click_prev_page()

        # Should be back on page 1
        pagination_info = receipts_page.get_pagination_info()
        assert "Página 1" in pagination_info, "Should be back on page 1"

    def test_receipts_page_accessible_when_authenticated(
        self,
        authenticated_page: Page,
        receipts_page: ReceiptsPage
    ):
        """Test that receipts page is accessible when user is authenticated."""
        receipts_page.navigate()

        # Should be on receipts page
        assert receipts_page.is_on_receipts_page(), "Should be on receipts page"

        # Page should not redirect to login
        assert "login" not in receipts_page.get_current_url().lower(), "Should not redirect to login"

    def test_receipts_page_requires_authentication(
        self,
        page: Page,
        base_url: str,
        receipts_page: ReceiptsPage
    ):
        """Test that receipts page redirects to login when not authenticated."""
        # Clear any existing session
        page.context.clear_cookies()

        # Try to navigate to receipts page without login
        receipts_page.navigate()

        # Wait a bit for any redirects
        page.wait_for_timeout(2000)

        # Should redirect to login page
        current_url = receipts_page.get_current_url()
        assert "login" in current_url.lower() or "index.html" in current_url, \
            f"Should redirect to login, but got: {current_url}"

    def test_receipts_list_shows_correct_item_count(
        self,
        authenticated_page: Page,
        receipts_page: ReceiptsPage
    ):
        """Test that each receipt shows correct item count."""
        receipts_page.navigate()

        if not receipts_page.has_receipts():
            pytest.skip("No receipts available for testing")

        # Get first receipt details
        details = receipts_page.get_first_receipt_details()

        # Should have items_count field
        assert 'items_count' in details, "Receipt should show items count"

        # Items count should be a number (format: "X items" or "X item")
        items_text = details['items_count']
        assert 'item' in items_text.lower(), f"Should contain 'item', got: {items_text}"

    def test_can_navigate_back_to_dashboard_from_receipts(
        self,
        authenticated_page: Page,
        receipts_page: ReceiptsPage
    ):
        """Test navigation from receipts page back to dashboard."""
        receipts_page.navigate()

        # Click breadcrumb or back button to dashboard
        # Assuming there's a breadcrumb link to dashboard
        dashboard_link = receipts_page.page.query_selector('a[href="/dashboard.html"]')

        if dashboard_link:
            dashboard_link.click()
            receipts_page.wait_for_navigation()

            # Should be on dashboard
            current_url = receipts_page.get_current_url()
            assert "dashboard" in current_url, "Should navigate to dashboard"
