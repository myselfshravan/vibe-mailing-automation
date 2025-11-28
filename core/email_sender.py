"""
Gmail Email Sender for VibeMailing
Automates email sending through Gmail web interface using Selenium.
"""

import time
from typing import Tuple, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from core.logger import get_logger
from core.browser import find_element_with_fallback, wait_for_element_clickable


logger = get_logger()


# Gmail selector patterns (with multiple fallbacks for reliability)
GMAIL_SELECTORS = {
    "compose_button": [
        ("css", "div[role='button'][gh='cm']"),
        ("xpath", "//div[@role='button' and @aria-label='Compose']"),
        ("xpath", "//div[contains(@aria-label, 'Compose')]"),
        ("css", ".T-I.T-I-KE.L3"),
    ],
    "to_field": [
        ("css", "input[aria-label='To recipients']"),
        ("xpath", "//input[@aria-label='To recipients']"),
        ("css", "input.agP.aFw"),
        ("xpath", "//input[@class='agP aFw']"),
        ("css", "input[name='to']"),
        ("xpath", "//input[@aria-label='To']"),
    ],
    "subject_field": [
        ("css", "input[name='subjectbox']"),
        ("xpath", "//input[@name='subjectbox']"),
        ("css", "input.aoT"),
        ("xpath", "//input[@aria-label='Subject']"),
        ("css", "input[placeholder='Subject']"),
    ],
    "body_field": [
        ("css", "div[aria-label='Message Body'][contenteditable='true']"),
        ("xpath", "//div[@aria-label='Message Body' and @contenteditable='true']"),
        ("css", "div.Am.aiL.Al.editable"),
        ("xpath", "//div[@role='textbox' and @aria-label='Message Body']"),
        ("css", "div[role='textbox'][aria-label='Message Body']"),
        ("css", "textarea[aria-label='Message Body']"),
    ],
    "send_button": [
        ("css", "div[role='button'][aria-label^='Send']"),
        ("xpath", "//div[@role='button' and starts-with(@aria-label, 'Send')]"),
        ("xpath", "//div[@role='button' and contains(@aria-label, 'Send')]"),
        ("css", ".T-I.J-J5-Ji.aoO.v7.T-I-atl.L3"),
    ],
    "sent_confirmation": [
        ("xpath", "//*[contains(text(), 'Message sent')]"),
        ("css", "span.bAq"),
        ("xpath", "//*[contains(text(), 'Your message has been sent')]"),
    ],
}


def send_email(
    driver: webdriver.Chrome,
    to: str,
    subject: str,
    body: str,
    timeout: int = 30
) -> Tuple[bool, str]:
    """
    Send email through Gmail web interface.

    Args:
        driver: Chrome WebDriver instance
        to: Recipient email address
        subject: Email subject
        body: Email body
        timeout: Timeout for operations

    Returns:
        Tuple of (success, message)
    """
    logger.info(f"Sending email to {to}")
    logger.debug(f"Subject: {subject}")

    try:
        # Ensure we're on Gmail
        if "mail.google.com" not in driver.current_url:
            logger.debug("Navigating to Gmail...")
            driver.get("https://mail.google.com/mail/u/0/")
            time.sleep(3)

        # Step 1: Open compose window
        logger.debug("Opening compose window...")
        if not open_compose(driver):
            return False, "Failed to open compose window"

        time.sleep(2)  # Wait for compose window to fully load

        # Step 2: Fill recipient
        logger.debug(f"Filling recipient: {to}")
        if not fill_recipient(driver, to):
            return False, f"Failed to fill recipient: {to}"

        time.sleep(0.5)

        # Step 3: Fill subject
        logger.debug(f"Filling subject: {subject}")
        if not fill_subject(driver, subject):
            return False, "Failed to fill subject"

        time.sleep(0.5)

        # Step 4: Fill body
        logger.debug(f"Filling body: {len(body)} characters")
        if not fill_body(driver, body):
            return False, "Failed to fill body"

        time.sleep(1)

        # Step 5: Click send
        logger.debug("Clicking send button...")
        if not click_send(driver):
            return False, "Failed to click send button"

        # Step 6: Verify sent
        time.sleep(2)  # Wait for send confirmation
        logger.debug("Verifying email sent...")
        if not verify_sent(driver, timeout=10):
            # Check for error messages
            error = handle_send_errors(driver)
            return False, error or "Email may not have sent (no confirmation)"

        logger.info(f"✓ Email sent successfully to {to}")
        return True, "Email sent successfully"

    except Exception as e:
        error_msg = f"Error sending email: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg


def open_compose(driver: webdriver.Chrome) -> bool:
    """
    Open Gmail compose window.

    Args:
        driver: Chrome WebDriver instance

    Returns:
        True if successful, False otherwise
    """
    try:
        compose_btn = find_element_with_fallback(
            driver,
            GMAIL_SELECTORS["compose_button"],
            timeout=10
        )

        if not compose_btn:
            logger.error("Compose button not found")
            return False

        compose_btn.click()
        logger.debug("✓ Compose window opened")
        return True

    except Exception as e:
        logger.error(f"Error opening compose: {e}")
        return False


def fill_recipient(driver: webdriver.Chrome, email: str) -> bool:
    """
    Fill recipient email address.

    Args:
        driver: Chrome WebDriver instance
        email: Recipient email

    Returns:
        True if successful, False otherwise
    """
    try:
        to_field = find_element_with_fallback(
            driver,
            GMAIL_SELECTORS["to_field"],
            timeout=10
        )

        if not to_field:
            logger.error("To field not found")
            return False

        to_field.clear()
        to_field.send_keys(email)
        to_field.send_keys(Keys.TAB)  # Move to next field

        logger.debug(f"✓ Recipient filled: {email}")
        return True

    except Exception as e:
        logger.error(f"Error filling recipient: {e}")
        return False


def fill_subject(driver: webdriver.Chrome, subject: str) -> bool:
    """
    Fill email subject.

    Args:
        driver: Chrome WebDriver instance
        subject: Email subject

    Returns:
        True if successful, False otherwise
    """
    try:
        subject_field = find_element_with_fallback(
            driver,
            GMAIL_SELECTORS["subject_field"],
            timeout=10
        )

        if not subject_field:
            logger.error("Subject field not found")
            return False

        subject_field.clear()
        subject_field.send_keys(subject)

        logger.debug(f"✓ Subject filled: {subject}")
        return True

    except Exception as e:
        logger.error(f"Error filling subject: {e}")
        return False


def fill_body(driver: webdriver.Chrome, body: str) -> bool:
    """
    Fill email body.
    Note: Gmail body is a contenteditable div, not a textarea.

    Args:
        driver: Chrome WebDriver instance
        body: Email body text

    Returns:
        True if successful, False otherwise
    """
    try:
        body_field = find_element_with_fallback(
            driver,
            GMAIL_SELECTORS["body_field"],
            timeout=10
        )

        if not body_field:
            logger.error("Body field not found")
            return False

        # Click to focus
        body_field.click()
        time.sleep(0.3)

        # Clear existing content
        body_field.clear()

        # Send keys (works with contenteditable div)
        body_field.send_keys(body)

        logger.debug(f"✓ Body filled: {len(body)} characters")
        return True

    except Exception as e:
        logger.error(f"Error filling body: {e}")
        return False


def click_send(driver: webdriver.Chrome) -> bool:
    """
    Click send button.

    Args:
        driver: Chrome WebDriver instance

    Returns:
        True if successful, False otherwise
    """
    try:
        send_btn = find_element_with_fallback(
            driver,
            GMAIL_SELECTORS["send_button"],
            timeout=10
        )

        if not send_btn:
            logger.error("Send button not found")
            # Try keyboard shortcut as fallback
            logger.debug("Trying keyboard shortcut (Ctrl+Enter / Cmd+Enter)")
            try:
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.COMMAND + Keys.RETURN)
                return True
            except:
                return False

        send_btn.click()
        logger.debug("✓ Send button clicked")
        return True

    except Exception as e:
        logger.error(f"Error clicking send: {e}")
        return False


def verify_sent(driver: webdriver.Chrome, timeout: int = 10) -> bool:
    """
    Verify email was sent successfully.
    Looks for "Message sent" confirmation.

    Args:
        driver: Chrome WebDriver instance
        timeout: Timeout for verification

    Returns:
        True if sent confirmation found, False otherwise
    """
    try:
        # Look for sent confirmation
        sent_element = find_element_with_fallback(
            driver,
            GMAIL_SELECTORS["sent_confirmation"],
            timeout=timeout
        )

        if sent_element:
            logger.debug("✓ Send confirmation found")
            return True

        # Fallback: check if compose window closed
        # If compose is gone, email was likely sent
        try:
            driver.find_element(By.CSS_SELECTOR, "div[role='dialog']")
            # Compose still open - likely not sent
            logger.debug("Compose window still open - may not have sent")
            return False
        except:
            # Compose closed - likely sent
            logger.debug("Compose window closed - assuming sent")
            return True

    except Exception as e:
        logger.debug(f"Error verifying sent: {e}")
        return False


def handle_send_errors(driver: webdriver.Chrome) -> Optional[str]:
    """
    Detect and return Gmail send error messages.

    Args:
        driver: Chrome WebDriver instance

    Returns:
        Error message if found, None otherwise
    """
    error_selectors = [
        ("xpath", "//*[contains(text(), 'could not be sent')]"),
        ("xpath", "//*[contains(text(), 'Invalid email')]"),
        ("xpath", "//*[contains(text(), 'Oops')]"),
        ("css", "div[role='alert']"),
        ("xpath", "//*[contains(text(), 'error')]"),
    ]

    try:
        error_element = find_element_with_fallback(
            driver,
            error_selectors,
            timeout=3
        )

        if error_element:
            error_text = error_element.text
            logger.error(f"Gmail error detected: {error_text}")
            return error_text

    except Exception as e:
        logger.debug(f"Error checking for send errors: {e}")

    return None


def close_compose_window(driver: webdriver.Chrome) -> bool:
    """
    Close compose window (if open).

    Args:
        driver: Chrome WebDriver instance

    Returns:
        True if successful or already closed, False otherwise
    """
    try:
        # Try to find and click close button
        close_selectors = [
            ("css", "img[aria-label='Save & close']"),
            ("xpath", "//img[@aria-label='Save & close']"),
        ]

        close_btn = find_element_with_fallback(
            driver,
            close_selectors,
            timeout=3
        )

        if close_btn:
            close_btn.click()
            logger.debug("✓ Compose window closed")
            return True

        # If no close button found, compose may already be closed
        return True

    except Exception as e:
        logger.debug(f"Error closing compose window: {e}")
        return False


def wait_for_compose_ready(driver: webdriver.Chrome, timeout: int = 10) -> bool:
    """
    Wait for compose window to be fully ready.

    Args:
        driver: Chrome WebDriver instance
        timeout: Timeout in seconds

    Returns:
        True if ready, False otherwise
    """
    try:
        # Wait for to field to be present and visible
        to_field = find_element_with_fallback(
            driver,
            GMAIL_SELECTORS["to_field"],
            timeout=timeout
        )

        return to_field is not None

    except Exception as e:
        logger.debug(f"Error waiting for compose ready: {e}")
        return False
