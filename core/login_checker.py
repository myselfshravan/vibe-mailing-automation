"""
Gmail Login Checker for VibeMailing
Handles login status verification and manual login prompts.
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from core.logger import get_logger
from core.browser import find_element_with_fallback


logger = get_logger()


# Gmail inbox indicators (multiple selectors for reliability)
GMAIL_INBOX_SELECTORS = [
    ("css", "div[role='button'][gh='cm']"),  # Compose button
    ("xpath", "//div[@aria-label='Compose']"),
    ("xpath", "//div[@role='main']"),         # Main content area
    ("css", "div.nH.bkL"),                    # Gmail wrapper
    ("xpath", "//table[@role='grid']"),       # Email list
    ("css", "div[aria-label='Search mail']"),
]

# Login page indicators
LOGIN_PAGE_INDICATORS = [
    ("css", "input[type='email']"),
    ("css", "input[type='password']"),
    ("xpath", "//h1[contains(text(), 'Sign in')]"),
    ("xpath", "//div[contains(text(), 'Use your Google Account')]"),
]


def check_login_status(driver: webdriver.Chrome, timeout: int = 10) -> bool:
    """
    Check if user is logged into Gmail.

    Args:
        driver: Chrome WebDriver instance
        timeout: Timeout for checking elements

    Returns:
        True if logged in, False otherwise
    """
    logger.info("Checking Gmail login status...")

    try:
        # Navigate to Gmail if not already there
        if "mail.google.com" not in driver.current_url:
            logger.debug("Navigating to Gmail...")
            driver.get("https://mail.google.com/mail/u/0/")
            time.sleep(3)  # Wait for page load

        # Try to find inbox indicators
        inbox_element = find_element_with_fallback(
            driver,
            GMAIL_INBOX_SELECTORS,
            timeout=timeout
        )

        if inbox_element:
            logger.info("✓ User is logged in")
            return True

        # Check if we're on login page
        login_element = find_element_with_fallback(
            driver,
            LOGIN_PAGE_INDICATORS,
            timeout=5
        )

        if login_element:
            logger.info("✗ User is not logged in (on login page)")
            return False

        # Unclear state - assume not logged in
        logger.warning("Login status unclear - assuming not logged in")
        return False

    except Exception as e:
        logger.error(f"Error checking login status: {e}", exc_info=True)
        return False


def prompt_manual_login(driver: webdriver.Chrome, email: str = None) -> bool:
    """
    Prompt user to log in manually.
    Handles 2FA and other authentication requirements.

    Args:
        driver: Chrome WebDriver instance
        email: Email address to display in prompt

    Returns:
        True if login successful, False otherwise
    """
    email_display = f" ({email})" if email else ""

    print("\n" + "="*60)
    print("⚠️  LOGIN REQUIRED")
    print("="*60)
    print(f"\nPlease complete the following steps{email_display}:")
    print("1. Log in to your Gmail account in the browser")
    print("2. Complete 2FA (two-factor authentication) if prompted")
    print("3. Wait until you see your Gmail inbox")
    print("4. Return here and press Enter")
    print("\nNote: The browser window should be visible.")
    print("="*60 + "\n")

    logger.info(f"Prompting user to log in{email_display}")

    # Navigate to Google accounts login page
    try:
        driver.get("https://accounts.google.com/")
        time.sleep(2)
    except Exception as e:
        logger.warning(f"Error navigating to login page: {e}")

    # Wait for user confirmation
    input("Press Enter once you're logged in and see your inbox...")

    # Verify login
    logger.info("Verifying login...")
    if check_login_status(driver, timeout=30):
        print("\n✓ Login verified successfully!\n")
        logger.info("✓ Manual login completed successfully")
        return True
    else:
        print("\n✗ Login verification failed. Please try again.\n")
        logger.error("✗ Login verification failed after manual attempt")
        return False


def wait_for_gmail_inbox(
    driver: webdriver.Chrome,
    timeout: int = 60
) -> bool:
    """
    Wait for Gmail inbox to load.

    Args:
        driver: Chrome WebDriver instance
        timeout: Maximum wait time in seconds

    Returns:
        True if inbox loaded, False otherwise
    """
    logger.debug(f"Waiting for Gmail inbox (timeout: {timeout}s)...")

    start_time = time.time()
    while time.time() - start_time < timeout:
        if check_login_status(driver, timeout=5):
            return True
        time.sleep(2)

    logger.warning("Timeout waiting for Gmail inbox")
    return False


def verify_logged_in_account(driver: webdriver.Chrome) -> str:
    """
    Attempt to get the email address of the logged-in account.

    Args:
        driver: Chrome WebDriver instance

    Returns:
        Email address if found, None otherwise
    """
    try:
        # Try to find account email in Gmail UI
        # This is approximate - Gmail's UI changes frequently
        account_selectors = [
            ("css", "div[aria-label*='Google Account']"),
            ("xpath", "//div[contains(@aria-label, 'Account')]"),
            ("css", "a[aria-label*='Google Account']"),
        ]

        account_element = find_element_with_fallback(
            driver,
            account_selectors,
            timeout=5
        )

        if account_element:
            # Try to extract email from aria-label or text
            aria_label = account_element.get_attribute('aria-label')
            if aria_label and '@' in aria_label:
                # Extract email from aria-label
                parts = aria_label.split()
                for part in parts:
                    if '@' in part:
                        logger.debug(f"Found logged-in account: {part}")
                        return part.strip('()')

        logger.debug("Could not determine logged-in account email")
        return None

    except Exception as e:
        logger.debug(f"Error verifying logged-in account: {e}")
        return None


def ensure_logged_in(driver: webdriver.Chrome, email: str = None) -> bool:
    """
    Ensure user is logged in, prompting if necessary.

    Args:
        driver: Chrome WebDriver instance
        email: Expected email address (optional)

    Returns:
        True if logged in, False otherwise
    """
    if check_login_status(driver):
        return True

    logger.warning("User not logged in, prompting for manual login...")
    return prompt_manual_login(driver, email)
