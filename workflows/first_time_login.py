"""
First-Time Account Setup Workflow for VibeMailing
Guides user through initial profile setup and Gmail login.
"""

import os
import shutil
from typing import Dict
from core.logger import get_logger
from core.account_manager import get_profile_path
from core.browser import create_browser, close_browser
from core.login_checker import ensure_logged_in
from core.config_loader import load_settings


logger = get_logger()


def run_first_time_setup(account: Dict[str, str]) -> bool:
    """
    Run first-time setup workflow for account.
    Launches browser and guides user through Gmail login.

    Args:
        account: Account dictionary

    Returns:
        True if setup successful, False otherwise
    """
    logger.info(f"Starting first-time setup for {account['email']}")

    print("\n" + "="*60)
    print(f"First-Time Setup: {account.get('display_name', account['email'])}")
    print("="*60)

    profile_path = get_profile_path(account)

    # Check if profile already exists
    if os.path.exists(profile_path):
        print(f"\n⚠️  Profile already exists at: {profile_path}")
        print("\nOptions:")
        print("  1. Delete and recreate (fresh start)")
        print("  2. Keep existing (skip setup)")
        print("  3. Cancel")

        while True:
            choice = input("\nYour choice (1/2/3): ").strip()

            if choice == '1':
                logger.info("User chose to delete and recreate profile")
                try:
                    shutil.rmtree(profile_path)
                    logger.info(f"Deleted existing profile: {profile_path}")
                except Exception as e:
                    logger.error(f"Error deleting profile: {e}")
                    print(f"\n✗ Error deleting profile: {e}")
                    return False
                break

            elif choice == '2':
                logger.info("User chose to keep existing profile")
                print("\n✓ Keeping existing profile. Setup skipped.")
                return True

            elif choice == '3':
                logger.info("Setup cancelled by user")
                return False

            else:
                print("Invalid choice. Please enter 1, 2, or 3")

    # Get settings
    settings = load_settings()
    browser_config = settings.get('browser', {})

    # Launch browser
    print("\n1. Launching Chrome browser...")
    logger.info(f"Launching browser with profile: {profile_path}")

    try:
        driver = create_browser(
            profile_dir=profile_path,
            headless=False,  # Always visible for first-time setup
            window_size=browser_config.get('window_size', '1920,1080'),
            timeout=browser_config.get('timeout', 30)
        )

    except Exception as e:
        logger.error(f"Failed to launch browser: {e}")
        print(f"\n✗ Failed to launch browser: {e}")
        return False

    # Guide user through login
    print("\n2. Please log in to Gmail...")
    print("\n" + "-"*60)
    print("NEXT STEPS:")
    print("-"*60)
    print("1. The browser should now be open")
    print("2. You will be prompted to log in to Gmail")
    print("3. Complete 2FA (two-factor authentication) if prompted")
    print("4. Wait for your Gmail inbox to load")
    print("5. Return here once you see your inbox")
    print("-"*60)

    # Ensure logged in
    logger.info("Waiting for user to log in...")

    try:
        success = ensure_logged_in(driver, account['email'])

        if success:
            print("\n✓ Login successful!")
            print(f"✓ Profile saved at: {profile_path}")
            print("\nYou can now use this account for email campaigns.")
            print("The browser will remember your login for future sessions.")

            logger.info(f"✓ First-time setup completed for {account['email']}")

            # Close browser
            input("\nPress Enter to close the browser...")
            close_browser(driver)

            return True

        else:
            print("\n✗ Login verification failed.")
            print("Please try the setup again.")

            logger.error("Login verification failed during setup")

            close_browser(driver)
            return False

    except KeyboardInterrupt:
        logger.warning("Setup interrupted by user")
        print("\n\n⚠️  Setup interrupted")
        close_browser(driver)
        return False

    except Exception as e:
        logger.error(f"Setup error: {e}", exc_info=True)
        print(f"\n✗ Setup error: {e}")
        close_browser(driver)
        return False


def setup_new_profile(account: Dict[str, str]) -> bool:
    """
    Set up new Chrome profile for account.
    Alias for run_first_time_setup for compatibility.

    Args:
        account: Account dictionary

    Returns:
        True if setup successful, False otherwise
    """
    return run_first_time_setup(account)


def verify_profile_working(account: Dict[str, str]) -> bool:
    """
    Verify that account profile works.

    Args:
        account: Account dictionary

    Returns:
        True if profile works, False otherwise
    """
    logger.info(f"Verifying profile for {account['email']}")

    profile_path = get_profile_path(account)

    if not os.path.exists(profile_path):
        logger.error(f"Profile does not exist: {profile_path}")
        return False

    settings = load_settings()
    browser_config = settings.get('browser', {})

    try:
        driver = create_browser(
            profile_dir=profile_path,
            headless=browser_config.get('headless', False),
            window_size=browser_config.get('window_size', '1920,1080'),
            timeout=browser_config.get('timeout', 30)
        )

        success = ensure_logged_in(driver, account['email'])

        close_browser(driver)

        if success:
            logger.info(f"✓ Profile verification successful for {account['email']}")
        else:
            logger.error(f"✗ Profile verification failed for {account['email']}")

        return success

    except Exception as e:
        logger.error(f"Profile verification error: {e}", exc_info=True)
        return False
