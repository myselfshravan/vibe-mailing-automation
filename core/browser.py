"""
Browser Management for VibeMailing
Handles Chrome browser launch with profile persistence.
"""

import os
import time
from pathlib import Path
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from core.logger import get_logger
from core.config_loader import get_absolute_path


logger = get_logger()


def create_browser(
    profile_dir: str,
    headless: bool = False,
    window_size: str = "1920,1080",
    timeout: int = 30
) -> webdriver.Chrome:
    """
    Create and configure Chrome browser with profile persistence.

    Args:
        profile_dir: Directory for Chrome user profile
        headless: Run browser in headless mode
        window_size: Browser window size (WIDTHxHEIGHT)
        timeout: Implicit wait timeout in seconds

    Returns:
        Configured Chrome WebDriver instance
    """
    logger.info(f"Creating browser with profile: {profile_dir}")

    # Ensure profile directory exists
    profile_path = get_absolute_path(profile_dir)
    Path(profile_path).mkdir(parents=True, exist_ok=True)

    logger.debug(f"Profile absolute path: {profile_path}")

    # Configure Chrome options
    options = Options()

    # Profile persistence (critical for avoiding re-login)
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument("--profile-directory=Default")

    # Window size
    options.add_argument(f"--window-size={window_size}")

    # Disable automation detection
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # Disable unnecessary features for performance
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")

    # User agent (optional - helps avoid detection)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/142.0.0.0 Safari/537.36"
    )

    # Headless mode (if requested)
    if headless:
        options.add_argument("--headless=new")  # New headless mode
        logger.info("Running in headless mode")

    # Suppress logging
    options.add_argument("--log-level=3")  # Suppress most logs
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    # Create WebDriver
    try:
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(timeout)

        logger.info(f"✓ Browser launched successfully")
        logger.debug(f"Browser session ID: {driver.session_id}")

        return driver

    except Exception as e:
        logger.error(f"Failed to create browser: {e}", exc_info=True)
        raise


def close_browser(driver: webdriver.Chrome) -> None:
    """
    Safely close browser.

    Args:
        driver: Chrome WebDriver instance
    """
    try:
        logger.info("Closing browser...")
        driver.quit()
        logger.info("✓ Browser closed successfully")
    except Exception as e:
        logger.warning(f"Error closing browser: {e}")


def wait_for_element(
    driver: webdriver.Chrome,
    selector: str,
    by: By = By.CSS_SELECTOR,
    timeout: int = 30
) -> Optional[object]:
    """
    Wait for element to be present.

    Args:
        driver: Chrome WebDriver instance
        selector: Element selector
        by: Selector type (CSS_SELECTOR, XPATH, etc.)
        timeout: Maximum wait time in seconds

    Returns:
        WebElement if found, None otherwise
    """
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )
        return element
    except TimeoutException:
        logger.debug(f"Element not found: {selector}")
        return None


def wait_for_element_clickable(
    driver: webdriver.Chrome,
    selector: str,
    by: By = By.CSS_SELECTOR,
    timeout: int = 30
) -> Optional[object]:
    """
    Wait for element to be clickable.

    Args:
        driver: Chrome WebDriver instance
        selector: Element selector
        by: Selector type
        timeout: Maximum wait time in seconds

    Returns:
        WebElement if found and clickable, None otherwise
    """
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, selector))
        )
        return element
    except TimeoutException:
        logger.debug(f"Element not clickable: {selector}")
        return None


def safe_click(element: object, retry: int = 3) -> bool:
    """
    Safely click element with retry logic.

    Args:
        element: WebElement to click
        retry: Number of retry attempts

    Returns:
        True if click succeeded, False otherwise
    """
    for attempt in range(retry):
        try:
            element.click()
            return True
        except Exception as e:
            logger.debug(f"Click attempt {attempt + 1} failed: {e}")
            time.sleep(0.5)

    return False


def safe_send_keys(element: object, text: str, retry: int = 3) -> bool:
    """
    Safely send keys to element with retry logic.

    Args:
        element: WebElement to send keys to
        text: Text to send
        retry: Number of retry attempts

    Returns:
        True if send succeeded, False otherwise
    """
    for attempt in range(retry):
        try:
            element.clear()
            element.send_keys(text)
            return True
        except Exception as e:
            logger.debug(f"Send keys attempt {attempt + 1} failed: {e}")
            time.sleep(0.5)

    return False


def find_element_with_fallback(
    driver: webdriver.Chrome,
    selectors: list,
    timeout: int = 10
) -> Optional[object]:
    """
    Try multiple selectors until one works.

    Args:
        driver: Chrome WebDriver instance
        selectors: List of (by_type, selector) tuples
        timeout: Timeout for each selector attempt

    Returns:
        WebElement if found, None otherwise

    Example:
        selectors = [
            ("css", "div.class1"),
            ("xpath", "//div[@id='id1']"),
        ]
    """
    for by_type, selector in selectors:
        try:
            by = By.CSS_SELECTOR if by_type == "css" else By.XPATH
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            logger.debug(f"Found element with selector: {selector}")
            return element
        except TimeoutException:
            continue

    logger.debug(f"No element found with {len(selectors)} selectors")
    return None
