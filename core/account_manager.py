"""
Account Manager for VibeMailing
Handles Gmail account selection and profile management.
"""

import os
from typing import Dict, List, Optional
from selenium import webdriver
from core.logger import get_logger
from core.config_loader import load_accounts, get_absolute_path
from core.browser import create_browser
from core.login_checker import ensure_logged_in


logger = get_logger()


def list_accounts() -> List[Dict[str, str]]:
    """
    Get list of configured Gmail accounts.

    Returns:
        List of account dictionaries
    """
    return load_accounts()


def get_account_by_id(account_id: str) -> Optional[Dict[str, str]]:
    """
    Get account configuration by ID.

    Args:
        account_id: Account ID

    Returns:
        Account dictionary if found, None otherwise
    """
    accounts = list_accounts()
    for account in accounts:
        if account['id'] == account_id:
            return account
    return None


def get_account_by_email(email: str) -> Optional[Dict[str, str]]:
    """
    Get account configuration by email.

    Args:
        email: Email address

    Returns:
        Account dictionary if found, None otherwise
    """
    accounts = list_accounts()
    for account in accounts:
        if account['email'] == email:
            return account
    return None


def select_account_interactive() -> Dict[str, str]:
    """
    Interactive account selection.
    Displays available accounts and prompts user to choose.

    Returns:
        Selected account dictionary

    Raises:
        ValueError: If no accounts configured
        KeyboardInterrupt: If user cancels
    """
    accounts = list_accounts()

    if not accounts:
        raise ValueError(
            "No accounts configured. "
            "Please add accounts to config/accounts.yaml"
        )

    print("\n" + "="*60)
    print("VibeMailing - Account Selection")
    print("="*60 + "\n")

    for idx, account in enumerate(accounts, 1):
        display_name = account.get('display_name', account['email'])
        email = account['email']
        print(f"  {idx}. {display_name}")
        print(f"     Email: {email}")
        print()

    print(f"  {len(accounts) + 1}. Cancel")
    print()

    while True:
        try:
            choice = input(f"Select account (1-{len(accounts) + 1}): ").strip()

            if not choice:
                continue

            choice_idx = int(choice) - 1

            if 0 <= choice_idx < len(accounts):
                selected = accounts[choice_idx]
                logger.info(f"Selected account: {selected['email']}")
                return selected

            elif choice_idx == len(accounts):
                logger.info("Account selection cancelled by user")
                raise KeyboardInterrupt("Account selection cancelled")

            else:
                print(f"Invalid choice. Please enter 1-{len(accounts) + 1}")

        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            raise


def get_profile_path(account: Dict[str, str]) -> str:
    """
    Get absolute path to account's Chrome profile directory.

    Args:
        account: Account dictionary

    Returns:
        Absolute path to profile directory
    """
    from core.config_loader import load_settings

    settings = load_settings()
    profile_base_dir = settings['browser']['profile_base_dir']
    profile_dir = account['profile_dir']

    # Construct full path
    full_path = os.path.join(profile_base_dir, profile_dir)

    # Convert to absolute path
    abs_path = get_absolute_path(full_path)

    return abs_path


def is_first_time_setup(account: Dict[str, str]) -> bool:
    """
    Check if account needs first-time setup.

    Args:
        account: Account dictionary

    Returns:
        True if profile doesn't exist, False otherwise
    """
    profile_path = get_profile_path(account)
    exists = os.path.exists(profile_path)

    logger.debug(
        f"Profile {'exists' if exists else 'does not exist'}: "
        f"{profile_path}"
    )

    return not exists


def initialize_account(account: Dict[str, str]) -> webdriver.Chrome:
    """
    Initialize account and launch browser.
    Ensures user is logged in.

    Args:
        account: Account dictionary

    Returns:
        Chrome WebDriver instance with logged-in session

    Raises:
        Exception: If browser launch or login fails
    """
    from core.config_loader import load_settings

    logger.info(f"Initializing account: {account['email']}")

    # Get settings
    settings = load_settings()
    browser_config = settings['browser']

    # Get profile path
    profile_path = get_profile_path(account)

    # Launch browser
    logger.info(f"Launching browser with profile: {profile_path}")

    driver = create_browser(
        profile_dir=profile_path,
        headless=browser_config.get('headless', False),
        window_size=browser_config.get('window_size', '1920,1080'),
        timeout=browser_config.get('timeout', 30)
    )

    # Ensure logged in
    logger.info("Checking login status...")

    if not ensure_logged_in(driver, account['email']):
        driver.quit()
        raise Exception("Failed to log in to Gmail")

    logger.info(f"✓ Account initialized successfully: {account['email']}")

    return driver


def display_account_info(account: Dict[str, str]) -> None:
    """
    Display account information.

    Args:
        account: Account dictionary
    """
    print("\n" + "="*60)
    print("Selected Account")
    print("="*60)
    print(f"Display Name: {account.get('display_name', 'N/A')}")
    print(f"Email:        {account['email']}")
    print(f"Account ID:   {account['id']}")
    print(f"Profile Dir:  {account['profile_dir']}")
    print("="*60 + "\n")
