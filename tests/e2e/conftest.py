"""
Pytest configuration and fixtures for E2E tests with Playwright.
"""

import pytest
import os
import time
from pathlib import Path
from playwright.sync_api import Page, Browser, BrowserContext, Playwright
from typing import Generator

# Import page objects
from tests.e2e.pages.login_page import LoginPage
from tests.e2e.pages.upload_page import UploadPage
from tests.e2e.pages.receipts_page import ReceiptsPage


# Configuration
BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:8001")
HEADLESS = os.getenv("E2E_HEADLESS", "true").lower() == "true"
SLOW_MO = int(os.getenv("E2E_SLOW_MO", "0"))  # Milliseconds to slow down Playwright operations


def pytest_configure(config):
    """Configure pytest with custom markers for E2E tests."""
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests using Playwright"
    )
    config.addinivalue_line(
        "markers", "slow_e2e: Slow E2E tests that take longer to execute"
    )


@pytest.fixture(scope="session")
def browser_type_launch_args():
    """
    Browser launch arguments.

    Returns:
        dict: Launch arguments for the browser
    """
    return {
        "headless": HEADLESS,
        "slow_mo": SLOW_MO,
        # Uncomment for debugging
        # "devtools": True,
    }


@pytest.fixture(scope="session")
def browser_context_args():
    """
    Browser context arguments.

    Returns:
        dict: Context arguments including viewport, etc.
    """
    return {
        "viewport": {"width": 1280, "height": 720},
        "ignore_https_errors": True,  # For local testing with self-signed certs
        "locale": "es-ES",
        # Record video for debugging (optional)
        # "record_video_dir": "test-results/videos/",
    }


@pytest.fixture(scope="session")
def base_url() -> str:
    """
    Fixture providing base URL for the application.

    Returns:
        str: Base URL of the application under test
    """
    return BASE_URL


@pytest.fixture(scope="function")
def page(page: Page, base_url: str) -> Generator[Page, None, None]:
    """
    Override default page fixture to add custom configuration.

    Args:
        page: Playwright page from pytest-playwright
        base_url: Base URL fixture

    Yields:
        Page: Configured Playwright page
    """
    # Set default timeout
    page.set_default_timeout(30000)  # 30 seconds

    # Set default navigation timeout
    page.set_default_navigation_timeout(30000)

    # Optional: Capture console messages for debugging
    page.on("console", lambda msg: print(f"Console {msg.type}: {msg.text}"))

    # Optional: Capture page errors
    page.on("pageerror", lambda err: print(f"Page error: {err}"))

    yield page

    # Cleanup after test
    # Screenshots on failure are handled by pytest-playwright automatically


@pytest.fixture(scope="function")
def context(context: BrowserContext) -> Generator[BrowserContext, None, None]:
    """
    Override default context fixture for additional configuration.

    Args:
        context: Browser context from pytest-playwright

    Yields:
        BrowserContext: Configured browser context
    """
    # Clear cookies and storage before each test
    context.clear_cookies()

    yield context

    # Cleanup after test
    context.close()


@pytest.fixture(scope="function")
def login_page(page: Page, base_url: str) -> LoginPage:
    """
    Fixture providing LoginPage object.

    Args:
        page: Playwright page fixture
        base_url: Base URL fixture

    Returns:
        LoginPage: Login page object
    """
    return LoginPage(page, base_url)


@pytest.fixture(scope="function")
def upload_page(page: Page, base_url: str) -> UploadPage:
    """
    Fixture providing UploadPage object.

    Args:
        page: Playwright page fixture
        base_url: Base URL fixture

    Returns:
        UploadPage: Upload page object
    """
    return UploadPage(page, base_url)


@pytest.fixture(scope="function")
def receipts_page(page: Page, base_url: str) -> ReceiptsPage:
    """
    Fixture providing ReceiptsPage object.

    Args:
        page: Playwright page fixture
        base_url: Base URL fixture

    Returns:
        ReceiptsPage: Receipts page object
    """
    return ReceiptsPage(page, base_url)


@pytest.fixture(scope="function")
def test_user_credentials() -> dict:
    """
    Fixture providing test user credentials.

    Returns:
        dict: User credentials for testing
    """
    timestamp = int(time.time())
    return {
        "username": f"testuser_{timestamp}",
        "email": f"testuser_{timestamp}@example.com",
        "password": "TestPassword123!"
    }


@pytest.fixture(scope="function")
def registered_user(login_page: LoginPage, test_user_credentials: dict) -> dict:
    """
    Fixture that creates a registered user.

    Args:
        login_page: Login page object
        test_user_credentials: User credentials fixture

    Returns:
        dict: User credentials
    """
    login_page.navigate()

    # Register the user
    login_page.register(
        username=test_user_credentials["username"],
        email=test_user_credentials["email"],
        password=test_user_credentials["password"]
    )

    # Wait for redirect to dashboard
    if not login_page.is_redirected_to_dashboard(timeout=10000):
        raise Exception("Failed to register user - redirect to dashboard did not occur")

    return test_user_credentials


@pytest.fixture(scope="function")
def authenticated_page(page: Page, base_url: str, test_user_credentials: dict) -> Page:
    """
    Fixture providing an authenticated page session.
    Creates a new user, logs in, and returns the page with valid session.

    Args:
        page: Playwright page fixture
        base_url: Base URL fixture
        test_user_credentials: User credentials fixture

    Returns:
        Page: Authenticated Playwright page
    """
    login_page = LoginPage(page, base_url)
    login_page.navigate()

    # Register and login
    login_page.register(
        username=test_user_credentials["username"],
        email=test_user_credentials["email"],
        password=test_user_credentials["password"]
    )

    # Wait for successful registration and redirect
    login_page.is_redirected_to_dashboard(timeout=10000)

    return page


@pytest.fixture(scope="session")
def sample_receipt_image() -> str:
    """
    Fixture providing path to a sample receipt image for testing.
    Creates a simple test image if it doesn't exist.

    Returns:
        str: Absolute path to sample receipt image
    """
    fixtures_dir = Path(__file__).parent / "fixtures"
    fixtures_dir.mkdir(exist_ok=True)

    image_path = fixtures_dir / "sample_receipt.jpg"

    # If image doesn't exist, create a simple one for testing
    if not image_path.exists():
        try:
            from PIL import Image, ImageDraw, ImageFont

            # Create a simple receipt-like image
            img = Image.new('RGB', (600, 800), color='white')
            draw = ImageDraw.Draw(img)

            # Draw some text that looks like a receipt
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            except:
                font = ImageFont.load_default()

            receipt_text = [
                "SUPERMERCADO TEST",
                "123 Calle Principal",
                "Tel: 555-1234",
                "",
                "TICKET #12345",
                "Fecha: 2024-01-15",
                "",
                "PRODUCTOS:",
                "Leche           2.50€",
                "Pan             1.20€",
                "Huevos          3.00€",
                "Manzanas        2.80€",
                "",
                "TOTAL:          9.50€",
                "",
                "Gracias por su compra"
            ]

            y_position = 50
            for line in receipt_text:
                draw.text((50, y_position), line, fill='black', font=font)
                y_position += 35

            img.save(image_path, 'JPEG')
        except ImportError:
            # If PIL is not available, create a minimal file
            # Note: This won't be a valid image but allows tests to run
            image_path.write_bytes(b'')

    return str(image_path.absolute())


@pytest.fixture(scope="function")
def wait_for_backend(base_url: str) -> None:
    """
    Fixture to ensure backend is ready before running tests.

    Args:
        base_url: Base URL fixture
    """
    import httpx
    import time

    max_retries = 30
    retry_delay = 2  # seconds

    for i in range(max_retries):
        try:
            response = httpx.get(f"{base_url}/api/health", timeout=5.0)
            if response.status_code == 200:
                return
        except Exception:
            pass

        if i < max_retries - 1:
            time.sleep(retry_delay)

    raise Exception(f"Backend at {base_url} not responding after {max_retries * retry_delay} seconds")


@pytest.fixture(autouse=True, scope="function")
def ensure_clean_state(page: Page):
    """
    Auto-use fixture to ensure clean state before each test.

    Args:
        page: Playwright page fixture
    """
    # Clear browser storage before each test
    try:
        page.context.clear_cookies()
        page.evaluate("localStorage.clear()")
        page.evaluate("sessionStorage.clear()")
    except Exception:
        pass  # Ignore errors if page is not yet initialized

    yield

    # Cleanup after test if needed
