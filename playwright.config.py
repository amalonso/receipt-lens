"""
Playwright configuration for E2E tests.
This file is optional but provides centralized configuration.
"""

import os

# Base URL for tests
BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:8001")

# Browser configuration
HEADLESS = os.getenv("E2E_HEADLESS", "true").lower() == "true"
SLOW_MO = int(os.getenv("E2E_SLOW_MO", "0"))  # Slow down operations in ms

# Timeout configuration
DEFAULT_TIMEOUT = 30000  # 30 seconds
NAVIGATION_TIMEOUT = 30000  # 30 seconds

# Screenshot and video configuration
SCREENSHOT_ON_FAILURE = True
VIDEO_ON_FAILURE = True

# Directories
SCREENSHOTS_DIR = "test-results/screenshots"
VIDEOS_DIR = "test-results/videos"
TRACES_DIR = "test-results/traces"

# Retry configuration for flaky tests
RETRIES = int(os.getenv("E2E_RETRIES", "0"))  # Number of retries for failed tests

# Browser channels (chromium, firefox, webkit)
BROWSERS = ["chromium"]  # Can be extended to test on multiple browsers

# Device emulation (optional)
# Uncomment to test mobile views
# DEVICES = ["iPhone 13", "Pixel 5"]

# Configuration dict (can be imported in conftest.py)
CONFIG = {
    "base_url": BASE_URL,
    "headless": HEADLESS,
    "slow_mo": SLOW_MO,
    "default_timeout": DEFAULT_TIMEOUT,
    "navigation_timeout": NAVIGATION_TIMEOUT,
    "screenshot_on_failure": SCREENSHOT_ON_FAILURE,
    "video_on_failure": VIDEO_ON_FAILURE,
    "screenshots_dir": SCREENSHOTS_DIR,
    "videos_dir": VIDEOS_DIR,
    "traces_dir": TRACES_DIR,
    "retries": RETRIES,
    "browsers": BROWSERS,
}
