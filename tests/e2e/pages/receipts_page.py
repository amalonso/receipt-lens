"""
Receipts Page Object for viewing receipt list.
"""

from .base_page import BasePage
from playwright.sync_api import Page


class ReceiptsPage(BasePage):
    """Page Object for receipts listing page."""

    # Selectors
    RECEIPTS_LIST = '#receipts-list'
    RECEIPT_ITEM = '.receipt-item'
    LOADING_SPINNER = '.spinner'
    NO_RECEIPTS_MESSAGE = '.empty-state'
    TOTAL_COUNT_BADGE = '#total-count'
    SEARCH_INPUT = '#search-input'
    SORT_SELECT = '#sort-select'
    DELETE_BTN = '.btn-danger'
    DELETE_MODAL = '#delete-modal'
    CONFIRM_DELETE_BTN = '#confirm-delete-btn'
    PAGINATION = '#pagination'
    PREV_BTN = '#prev-btn'
    NEXT_BTN = '#next-btn'
    PAGE_INFO = '#page-info'

    def __init__(self, page: Page, base_url: str):
        """
        Initialize the receipts page.

        Args:
            page: Playwright page instance
            base_url: Base URL of the application
        """
        super().__init__(page, base_url)

    def navigate(self) -> None:
        """Navigate to the receipts page."""
        self.navigate_to("receipts.html")
        self.wait_for_navigation()

    def is_on_receipts_page(self) -> bool:
        """
        Check if currently on the receipts page.

        Returns:
            True if on receipts page, False otherwise
        """
        return "receipts.html" in self.get_current_url()

    def wait_for_receipts_to_load(self, timeout: int = 10000) -> None:
        """
        Wait for receipts to finish loading.

        Args:
            timeout: Maximum time to wait in milliseconds
        """
        # Wait for loading spinner to disappear (if present)
        try:
            self.wait_for_selector(self.LOADING_SPINNER, state="hidden", timeout=5000)
        except Exception:
            pass  # Loading might be too fast to catch

        # Give time for content to render
        self.page.wait_for_timeout(1000)

    def get_receipt_count(self) -> int:
        """
        Get the number of receipts displayed on the page.

        Returns:
            Number of receipt items visible
        """
        self.wait_for_receipts_to_load()
        receipt_items = self.page.query_selector_all(self.RECEIPT_ITEM)
        return len(receipt_items)

    def get_total_count_from_badge(self) -> int:
        """
        Get total count from the badge in the header.

        Returns:
            Total count number
        """
        badge = self.page.query_selector(self.TOTAL_COUNT_BADGE)
        if badge:
            return int(badge.inner_text())
        return 0

    def has_receipts(self) -> bool:
        """
        Check if any receipts are displayed.

        Returns:
            True if receipts are present, False otherwise
        """
        return self.get_receipt_count() > 0

    def get_first_receipt_details(self) -> dict:
        """
        Get details from the first receipt item.

        Returns:
            Dictionary with receipt information (store, total, date, etc.)
        """
        self.wait_for_receipts_to_load()

        first_item = self.page.query_selector(self.RECEIPT_ITEM)
        if not first_item:
            return {}

        # Extract information from the receipt item
        details = {}

        try:
            store = first_item.query_selector('.receipt-store')
            if store:
                details['store'] = store.inner_text()

            amount = first_item.query_selector('.receipt-amount')
            if amount:
                details['amount'] = amount.inner_text()

            date = first_item.query_selector('.receipt-date')
            if date:
                details['date'] = date.inner_text()

            items_count = first_item.query_selector('.receipt-items-count')
            if items_count:
                details['items_count'] = items_count.inner_text()

        except Exception as e:
            print(f"Error extracting receipt details: {e}")

        return details

    def click_first_receipt(self) -> None:
        """Click on the first receipt to view details."""
        self.wait_for_receipts_to_load()

        first_item = self.page.query_selector(self.RECEIPT_ITEM)
        if first_item:
            # Click on the receipt-info div to navigate to detail
            receipt_info = first_item.query_selector('.receipt-info')
            if receipt_info:
                receipt_info.click()
                self.wait_for_navigation()

    def is_empty_state_visible(self) -> bool:
        """
        Check if the empty state message is visible (no receipts).

        Returns:
            True if empty state is visible, False otherwise
        """
        return self.is_visible(self.NO_RECEIPTS_MESSAGE, timeout=3000)

    def search_receipts(self, search_term: str) -> None:
        """
        Search for receipts using search input.

        Args:
            search_term: Text to search for
        """
        if self.is_visible(self.SEARCH_INPUT, timeout=2000):
            self.fill_input(self.SEARCH_INPUT, search_term)
            self.page.wait_for_timeout(1500)  # Wait for search to filter results

    def sort_receipts(self, sort_option: str) -> None:
        """
        Sort receipts using sort dropdown.

        Args:
            sort_option: Sort option value (date-desc, date-asc, amount-desc, amount-asc)
        """
        if self.is_visible(self.SORT_SELECT, timeout=2000):
            self.page.select_option(self.SORT_SELECT, sort_option)
            self.page.wait_for_timeout(1000)

    def click_delete_first_receipt(self) -> None:
        """Click delete button on the first receipt."""
        self.wait_for_receipts_to_load()

        first_item = self.page.query_selector(self.RECEIPT_ITEM)
        if first_item:
            delete_btn = first_item.query_selector(self.DELETE_BTN)
            if delete_btn:
                delete_btn.click()
                self.page.wait_for_timeout(500)

    def is_delete_modal_visible(self) -> bool:
        """
        Check if delete confirmation modal is visible.

        Returns:
            True if modal is visible, False otherwise
        """
        return self.is_visible(self.DELETE_MODAL, timeout=3000)

    def confirm_delete(self) -> None:
        """Confirm deletion in the modal."""
        if self.is_visible(self.CONFIRM_DELETE_BTN, timeout=2000):
            self.click_element(self.CONFIRM_DELETE_BTN)
            # Wait for modal to close and list to refresh
            self.page.wait_for_timeout(2000)

    def is_pagination_visible(self) -> bool:
        """
        Check if pagination controls are visible.

        Returns:
            True if pagination is visible, False otherwise
        """
        return self.is_visible(self.PAGINATION, timeout=3000)

    def get_pagination_info(self) -> str:
        """
        Get pagination information text.

        Returns:
            Pagination text like "Página 1 de 3"
        """
        page_info = self.page.query_selector(self.PAGE_INFO)
        if page_info:
            return page_info.inner_text()
        return ""

    def click_next_page(self) -> None:
        """Click next page button."""
        if self.is_visible(self.NEXT_BTN, timeout=2000):
            self.click_element(self.NEXT_BTN)
            self.wait_for_receipts_to_load()

    def click_prev_page(self) -> None:
        """Click previous page button."""
        if self.is_visible(self.PREV_BTN, timeout=2000):
            self.click_element(self.PREV_BTN)
            self.wait_for_receipts_to_load()

    def is_next_button_disabled(self) -> bool:
        """
        Check if next page button is disabled.

        Returns:
            True if disabled, False otherwise
        """
        next_btn = self.page.query_selector(self.NEXT_BTN)
        if next_btn:
            return next_btn.is_disabled()
        return True

    def is_prev_button_disabled(self) -> bool:
        """
        Check if previous page button is disabled.

        Returns:
            True if disabled, False otherwise
        """
        prev_btn = self.page.query_selector(self.PREV_BTN)
        if prev_btn:
            return prev_btn.is_disabled()
        return True
