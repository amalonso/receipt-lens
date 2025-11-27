"""
Login Page Object for authentication flows.
"""

from .base_page import BasePage
from playwright.sync_api import Page


class LoginPage(BasePage):
    """Page Object for login and registration."""

    # Selectors
    LOGIN_TAB = '[data-tab="login"]'
    REGISTER_TAB = '[data-tab="register"]'

    # Login form selectors
    LOGIN_USERNAME_INPUT = '#login-username'
    LOGIN_PASSWORD_INPUT = '#login-password'
    LOGIN_SUBMIT_BTN = '#login-btn'
    LOGIN_ERROR = '#login-error'

    # Register form selectors
    REGISTER_USERNAME_INPUT = '#register-username'
    REGISTER_EMAIL_INPUT = '#register-email'
    REGISTER_PASSWORD_INPUT = '#register-password'
    REGISTER_PASSWORD_CONFIRM_INPUT = '#register-password-confirm'
    REGISTER_SUBMIT_BTN = '#register-btn'
    REGISTER_ERROR = '#register-error'

    def __init__(self, page: Page, base_url: str):
        """
        Initialize the login page.

        Args:
            page: Playwright page instance
            base_url: Base URL of the application
        """
        super().__init__(page, base_url)

    def navigate(self) -> None:
        """Navigate to the login page."""
        self.navigate_to("login.html")
        self.wait_for_navigation()

    def is_on_login_page(self) -> bool:
        """
        Check if currently on the login page.

        Returns:
            True if on login page, False otherwise
        """
        return "login.html" in self.get_current_url() or self.is_visible(self.LOGIN_TAB)

    def switch_to_register_tab(self) -> None:
        """Switch to the registration tab."""
        self.click_element(self.REGISTER_TAB)

    def switch_to_login_tab(self) -> None:
        """Switch to the login tab."""
        self.click_element(self.LOGIN_TAB)

    def login(self, username: str, password: str) -> None:
        """
        Perform login with credentials.

        Args:
            username: Username or email
            password: Password
        """
        # Ensure we're on login tab
        if not self.page.locator(self.LOGIN_TAB).get_attribute("class").find("active") >= 0:
            self.switch_to_login_tab()

        # Fill credentials
        self.fill_input(self.LOGIN_USERNAME_INPUT, username)
        self.fill_input(self.LOGIN_PASSWORD_INPUT, password)

        # Submit form
        self.click_element(self.LOGIN_SUBMIT_BTN)

        # Wait for navigation or error
        self.page.wait_for_timeout(1000)  # Allow time for API call

    def register(
        self,
        username: str,
        email: str,
        password: str,
        password_confirm: str = None
    ) -> None:
        """
        Perform registration with user details.

        Args:
            username: Desired username
            email: Email address
            password: Password
            password_confirm: Password confirmation (defaults to password if not provided)
        """
        if password_confirm is None:
            password_confirm = password

        # Switch to register tab
        self.switch_to_register_tab()

        # Fill registration form
        self.fill_input(self.REGISTER_USERNAME_INPUT, username)
        self.fill_input(self.REGISTER_EMAIL_INPUT, email)
        self.fill_input(self.REGISTER_PASSWORD_INPUT, password)
        self.fill_input(self.REGISTER_PASSWORD_CONFIRM_INPUT, password_confirm)

        # Submit form
        self.click_element(self.REGISTER_SUBMIT_BTN)

        # Wait for navigation or error
        self.page.wait_for_timeout(1000)  # Allow time for API call

    def get_login_error(self) -> str:
        """
        Get login error message if present.

        Returns:
            Error message text or empty string
        """
        if self.is_visible(self.LOGIN_ERROR, timeout=2000):
            return self.get_text(self.LOGIN_ERROR)
        return ""

    def get_register_error(self) -> str:
        """
        Get registration error message if present.

        Returns:
            Error message text or empty string
        """
        if self.is_visible(self.REGISTER_ERROR, timeout=2000):
            return self.get_text(self.REGISTER_ERROR)
        return ""

    def is_redirected_to_dashboard(self, timeout: int = 5000) -> bool:
        """
        Check if successfully redirected to dashboard after login/register.

        Args:
            timeout: Maximum time to wait for redirect in milliseconds

        Returns:
            True if redirected to dashboard, False otherwise
        """
        try:
            self.page.wait_for_url("**/dashboard.html", timeout=timeout)
            return True
        except Exception:
            return False

    def is_logged_in(self) -> bool:
        """
        Check if user is already logged in (has token in localStorage).

        Returns:
            True if logged in, False otherwise
        """
        token = self.get_local_storage_item("token")
        return token is not None and token != ""

    def logout(self) -> None:
        """Clear authentication token from localStorage."""
        self.clear_local_storage()
