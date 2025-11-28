#!/usr/bin/env python3
"""
VibeMailing - Multi-Account Gmail Automation with LLM-Powered Personalization

A side-project email automation tool that generates personalized emails
using LLMs and sends them through Gmail with proper rate limiting.

Author: Shravan Revanna
License: MIT
"""

import argparse
import sys
from pathlib import Path

from core.logger import setup_logger, get_logger
from core.config_loader import load_settings, load_accounts
from workflows.first_time_login import run_first_time_setup
from workflows.run_campaign import run_campaign
from core.account_manager import select_account_interactive, get_account_by_id


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="VibeMailing - LLM-powered Gmail automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # First-time account setup
  python main.py setup

  # Run campaign (interactive)
  python main.py campaign

  # Run campaign with specific CSV
  python main.py campaign --csv contacts.csv

  # Run campaign in autonomous mode
  python main.py campaign --csv contacts.csv --mode autonomous

For more information, see README.md
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Setup command
    setup_parser = subparsers.add_parser(
        'setup',
        help='First-time account setup (creates Chrome profile and logs in)'
    )

    # Campaign command
    campaign_parser = subparsers.add_parser(
        'campaign',
        help='Run email campaign'
    )
    campaign_parser.add_argument(
        '--account',
        help='Account ID to use (e.g., test_account)'
    )
    campaign_parser.add_argument(
        '--csv',
        help='Path to CSV file with contacts'
    )
    campaign_parser.add_argument(
        '--template',
        help='Template name (default: default_outreach)'
    )
    campaign_parser.add_argument(
        '--mode',
        choices=['autonomous', 'semi'],
        help='Operation mode (semi = preview before sending, autonomous = auto-send)'
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    # Parse arguments first to check command
    args = parse_args()

    # Setup logging
    try:
        settings = load_settings()
        logger = setup_logger(
            settings['logging']['log_file'],
            settings['logging']['level']
        )
    except Exception as e:
        print(f"✗ Error loading configuration: {e}")
        print("\nPlease ensure config/settings.yaml exists and is valid.")
        sys.exit(1)

    logger.info("="*60)
    logger.info("VibeMailing Started")
    logger.info("="*60)

    try:
        if args.command == 'setup':
            # ========== FIRST-TIME SETUP WORKFLOW ==========

            print("\n" + "="*60)
            print("VibeMailing - First-Time Account Setup")
            print("="*60)

            # Load accounts
            accounts = load_accounts()
            if not accounts:
                print("\n✗ No accounts configured.")
                print("Please add accounts to config/accounts.yaml first.")
                print("\nExample:")
                print("  accounts:")
                print("    - id: my_account")
                print("      email: your-email@gmail.com")
                print("      profile_dir: profile_your_email")
                print("      display_name: \"My Account\"")
                sys.exit(1)

            # Select account
            account = select_account_interactive()

            # Run setup
            success = run_first_time_setup(account)

            if success:
                print("\n✓ Setup complete! You can now run campaigns with this account.")
                logger.info("Setup completed successfully")
                sys.exit(0)
            else:
                print("\n✗ Setup failed. Please try again.")
                logger.error("Setup failed")
                sys.exit(1)

        elif args.command == 'campaign':
            # ========== CAMPAIGN WORKFLOW ==========

            # Resolve account if provided by ID
            account = None
            if args.account:
                account = get_account_by_id(args.account)
                if not account:
                    print(f"\n✗ Account not found: {args.account}")
                    print("\nAvailable accounts:")
                    accounts = load_accounts()
                    for acc in accounts:
                        print(f"  - {acc['id']} ({acc['email']})")
                    sys.exit(1)

            # Run campaign
            stats = run_campaign(
                account=account,
                csv_path=args.csv,
                template_name=args.template,
                mode=args.mode
            )

            logger.info(f"Campaign completed: {stats}")
            sys.exit(0)

        else:
            # ========== NO COMMAND - SHOW MENU ==========

            show_interactive_menu()

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        logger.warning("User interrupted program")
        sys.exit(130)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


def show_interactive_menu():
    """Display interactive menu when no command specified."""
    print("\n" + "="*60)
    print("VibeMailing - Multi-Account Gmail Automation")
    print("="*60)

    print("\n🚀 LLM-Powered Email Personalization")
    print("    Generate personalized emails using Groq's LLM")
    print("    and send them through Gmail with proper rate limiting.")

    print("\n📝 Commands:")
    print("  python main.py setup")
    print("    └─ First-time account setup (creates Chrome profile)")
    print()
    print("  python main.py campaign")
    print("    └─ Run email campaign (interactive mode)")
    print()
    print("  python main.py campaign --csv contacts.csv")
    print("    └─ Run campaign with specific CSV file")
    print()
    print("  python main.py campaign --mode autonomous")
    print("    └─ Run campaign without preview (auto-send)")

    print("\n📚 For detailed help:")
    print("  python main.py --help")
    print("  python main.py campaign --help")

    print("\n⚙️  Configuration:")
    print(f"  Settings:  config/settings.yaml")
    print(f"  Accounts:  config/accounts.yaml")
    print(f"  Templates: config/prompts.yaml")

    print("\n" + "="*60)

    print("\n💡 Quick Start:")
    print("  1. Add your API key to .env (copy from .env.example)")
    print("  2. Configure accounts in config/accounts.yaml")
    print("  3. Run 'python main.py setup' to set up each account")
    print("  4. Create a CSV with contacts (see tests/sample_contacts.csv)")
    print("  5. Run 'python main.py campaign' to start")

    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()
