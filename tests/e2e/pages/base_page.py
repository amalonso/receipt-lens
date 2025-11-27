"""
Base Page Object class with common functionality.
All page objects should inherit from this class.
"""

from playwright.sync_api import Page, expect
from typing import Optional
import time


class BasePage:
    """Base class for all Page Objects."""

    def __init__(self, page: Page, base_url: str):
        """
        Initialize the base page.

        Args:
            page: Playwright page instance
            base_url: Base URL of the application
        """
        self.page = page
        self.base_url = base_url

    def navigate_to(self, path: str = "") -> None:
        """
        Navigate to a specific path.

        Args:
            path: URL path to navigate to (without base URL)
        """
        url = f"{self.base_url}/{path}".rstrip("/")
        self.page.goto(url)

    def wait_for_navigation(self, timeout: int = 30000) -> None:
        """
        Wait for navigation to complete.

        Args:
            timeout: Maximum time to wait in milliseconds
        """
        self.page.wait_for_load_state("networkidle", timeout=timeout)

    def click_element(self, selector: str, timeout: int = 10000) -> None:
        """
        Click an element with explicit wait.

        Args:
            selector: CSS selector or text selector
            timeout: Maximum time to wait in milliseconds
        """
        self.page.wait_for_selector(selector, timeout=timeout)
        self.page.click(selector)

    def fill_input(self, selector: str, value: str, timeout: int = 10000) -> None:
        """
        Fill an input field with explicit wait.

        Args:
            selector: CSS selector of the input
            value: Value to fill
            timeout: Maximum time to wait in milliseconds
        """
        self.page.wait_for_selector(selector, timeout=timeout)
        self.page.fill(selector, value)

    def get_text(self, selector: str, timeout: int = 10000) -> str:
        """
        Get text content of an element.

        Args:
            selector: CSS selector
            timeout: Maximum time to wait in milliseconds

        Returns:
            Text content of the element
        """
        self.page.wait_for_selector(selector, timeout=timeout)
        return self.page.inner_text(selector)

    def is_visible(self, selector: str, timeout: int = 5000) -> bool:
        """
        Check if an element is visible.

        Args:
            selector: CSS selector
            timeout: Maximum time to wait in milliseconds

        Returns:
            True if element is visible, False otherwise
        """
        try:
            self.page.wait_for_selector(selector, state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def wait_for_selector(self, selector: str, timeout: int = 10000, state: str = "visible") -> None:
        """
        Wait for a selector to be in a specific state.

        Args:
            selector: CSS selector
            timeout: Maximum time to wait in milliseconds
            state: State to wait for (visible, attached, hidden, detached)
        """
        self.page.wait_for_selector(selector, state=state, timeout=timeout)

    def take_screenshot(self, name: str) -> bytes:
        """
        Take a screenshot of the current page.

        Args:
            name: Name for the screenshot file

        Returns:
            Screenshot as bytes
        """
        return self.page.screenshot(path=f"screenshots/{name}.png", full_page=True)

    def wait_for_alert(self, timeout: int = 5000) -> Optional[str]:
        """
        Wait for an alert/toast message and return its text.

        Args:
            timeout: Maximum time to wait in milliseconds

        Returns:
            Alert message text or None
        """
        try:
            # Common alert selectors - adjust based on your UI framework
            alert_selectors = [
                ".alert",
                ".toast",
                ".notification",
                "[role='alert']",
                ".success-message",
                ".error-message"
            ]

            for selector in alert_selectors:
                if self.is_visible(selector, timeout=timeout):
                    return self.get_text(selector)

            return None
        except Exception:
            return None

    def get_local_storage_item(self, key: str) -> Optional[str]:
        """
        Get an item from localStorage.

        Args:
            key: Storage key

        Returns:
            Value from localStorage or None
        """
        return self.page.evaluate(f"localStorage.getItem('{key}')")

    def set_local_storage_item(self, key: str, value: str) -> None:
        """
        Set an item in localStorage.

        Args:
            key: Storage key
            value: Value to store
        """
        self.page.evaluate(f"localStorage.setItem('{key}', '{value}')")

    def clear_local_storage(self) -> None:
        """Clear all localStorage items."""
        self.page.evaluate("localStorage.clear()")

    def wait_for_api_response(self, url_pattern: str, timeout: int = 30000) -> None:
        """
        Wait for a specific API response.

        Args:
            url_pattern: Pattern to match in the URL
            timeout: Maximum time to wait in milliseconds
        """
        with self.page.expect_response(lambda response: url_pattern in response.url, timeout=timeout):
            pass

    def reload_page(self) -> None:
        """Reload the current page."""
        self.page.reload()

    def go_back(self) -> None:
        """Navigate back in browser history."""
        self.page.go_back()

    def get_current_url(self) -> str:
        """
        Get the current page URL.

        Returns:
            Current URL
        """
        return self.page.url
