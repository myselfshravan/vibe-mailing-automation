"""
Main Campaign Workflow for VibeMailing
Orchestrates the complete email campaign process.
"""

import os
from typing import Dict, List, Optional, Tuple, Any
from core.logger import get_logger
from core.config_loader import load_settings
from core.account_manager import (
    select_account_interactive,
    get_account_by_id,
    initialize_account,
    display_account_info
)
from core.csv_loader import (
    select_csv_interactive,
    load_csv,
    display_csv_summary,
    preview_contacts
)
from core.template_manager import (
    select_template_interactive,
    get_template,
    get_default_template
)
from core.checkpoint import (
    load_checkpoint,
    should_resume,
    clear_checkpoint
)
from core.tracker import CampaignTracker
from core.llm_client import generate_email_content
from core.email_preview import preview_email, edit_email_body
from core.email_sender import send_email, compose_email
from core.cooldown import apply_cooldown
from core.browser import close_browser


logger = get_logger()


def run_campaign(
    account: Dict[str, str] = None,
    csv_path: str = None,
    template_name: str = None,
    mode: str = None
) -> Dict[str, Any]:
    """
    Run complete email campaign.

    Args:
        account: Account dictionary (None for interactive selection)
        csv_path: Path to CSV file (None for interactive selection)
        template_name: Template name (None for interactive selection)
        mode: Operation mode - "autonomous" or "semi" (None uses config default)

    Returns:
        Campaign statistics dictionary

    Raises:
        Exception: If campaign fails
        KeyboardInterrupt: If user cancels
    """
    logger.info("="*60)
    logger.info("CAMPAIGN STARTING")
    logger.info("="*60)

    driver = None

    try:
        # ========== PHASE 1: INITIALIZATION ==========

        # Load settings
        settings = load_settings()

        # Determine mode
        if mode is None:
            mode = settings.get('mode', 'semi')

        logger.info(f"Campaign mode: {mode}")

        # Select account
        if account is None:
            account = select_account_interactive()
        else:
            logger.info(f"Using provided account: {account['email']}")

        display_account_info(account)

        # Select CSV
        if csv_path is None:
            csv_path = select_csv_interactive()
        else:
            logger.info(f"Using provided CSV: {csv_path}")

        # Select template
        if template_name is None:
            try:
                template = select_template_interactive()
            except KeyboardInterrupt:
                # Use default template if user cancels
                logger.info("Using default template")
                template = get_default_template()
        else:
            template = get_template(template_name)
            if template is None:
                raise ValueError(f"Template not found: {template_name}")

        logger.info(f"Using template: {template['name']}")

        # ========== PHASE 2: BROWSER SETUP ==========

        logger.info(f"Launching browser for {account['email']}")
        driver = initialize_account(account)

        logger.info("✓ Browser initialized and logged in")

        # ========== PHASE 3: LOAD CAMPAIGN DATA ==========

        # Check for existing checkpoint
        checkpoint = load_checkpoint(csv_path, account['id'])
        start_index = 0

        if checkpoint:
            if should_resume(checkpoint):
                start_index = checkpoint['current_row']
                logger.info(f"Resuming from row {start_index}")
            else:
                clear_checkpoint(csv_path, account['id'])
                logger.info("Starting fresh campaign")

        # Load CSV
        all_contacts = load_csv(csv_path)
        logger.info(f"Loaded {len(all_contacts)} contacts from CSV")

        # Display summary
        display_csv_summary(all_contacts)

        # Apply start index for resume
        if start_index > 0:
            contacts = all_contacts[start_index:]
            logger.info(f"Processing {len(contacts)} remaining contacts")
        else:
            contacts = all_contacts

        # Preview contacts
        preview_contacts(contacts, count=3)

        # ========== PHASE 4: INITIALIZE TRACKER ==========

        tracker = CampaignTracker(
            csv_path=csv_path,
            account_id=account['id'],
            account_email=account['email'],
            template_name=template['name'],
            mode=mode,
            total_rows=len(all_contacts),
            start_index=start_index
        )

        # ========== PHASE 5: DISPLAY CAMPAIGN SUMMARY ==========

        display_campaign_summary(
            account=account,
            csv_path=csv_path,
            template=template,
            mode=mode,
            total_contacts=len(contacts),
            start_index=start_index,
            settings=settings
        )

        # Confirm start
        input("\nPress Enter to start campaign (or Ctrl+C to cancel)...\n")

        # ========== PHASE 6: CAMPAIGN LOOP ==========

        logger.info("Starting campaign loop...")

        campaign_loop(
            driver=driver,
            contacts=contacts,
            template=template,
            tracker=tracker,
            mode=mode,
            settings=settings
        )

        # ========== PHASE 7: CLEANUP & SUMMARY ==========

        logger.info("Campaign completed successfully")

        # Generate summary
        summary_report = tracker.generate_summary_report()
        print(summary_report)

        # Save history
        tracker.save_campaign_history()

        # Clear checkpoint (campaign complete)
        clear_checkpoint(csv_path, account['id'])

        # Close browser
        if driver:
            close_browser(driver)

        logger.info("="*60)
        logger.info("CAMPAIGN COMPLETED")
        logger.info("="*60)

        return tracker.get_statistics()

    except KeyboardInterrupt:
        logger.warning("Campaign interrupted by user")

        print("\n\n⚠️  Campaign interrupted by user")

        # Save checkpoint if tracker exists
        if 'tracker' in locals():
            tracker.update_checkpoint()
            print("✓ Progress saved. You can resume later.")

        # Close browser
        if driver:
            close_browser(driver)

        raise

    except Exception as e:
        logger.error(f"Campaign failed: {e}", exc_info=True)

        # Close browser
        if driver:
            close_browser(driver)

        raise


def campaign_loop(
    driver,
    contacts: List[Dict[str, str]],
    template: Dict[str, Any],
    tracker: CampaignTracker,
    mode: str,
    settings: Dict[str, Any]
) -> None:
    """
    Main loop for processing contacts.

    Args:
        driver: Chrome WebDriver instance
        contacts: List of contact dictionaries
        template: Template dictionary
        tracker: Campaign tracker instance
        mode: Operation mode
        settings: Settings dictionary
    """
    total = len(contacts)
    cooldown_config = settings['campaign']['cooldown']
    email_config = settings.get('email', {})

    # Build list of links from config (supports legacy single-link shape)
    links = email_config.get('links') or []
    if not links:
        legacy_link = email_config.get('link') or {}
        if isinstance(legacy_link, dict) and legacy_link.get('url'):
            links = [{
                'text': legacy_link.get('text') or "My Resume",
                'url': legacy_link.get('url')
            }]

    # Filter out any entries missing URL
    links = [link for link in links if link.get('url')]

    logger.info(f"Processing {total} contacts in {mode} mode")

    for idx, contact in enumerate(contacts, start=1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Contact {idx}/{total}: {contact['email']}")
        logger.info(f"{'='*60}")

        try:
            # Generate email
            logger.debug(f"Generating email for {contact['name']}")

            email = generate_email_content(template, contact, use_llm=True)

            # Send/Compose email based on mode
            if mode == "semi":
                # Browser preview mode - compose and let user send manually
                logger.debug(f"Composing email for browser preview: {contact['email']}")

                # Show brief info in CLI
                print(f"\n{'='*60}")
                print(f"Contact [{idx}/{total}]: {contact['name']} ({contact['company']})")
                print(f"Email: {contact['email']}")
                print(f"{'='*60}")

                success, message = compose_email(
                    driver,
                    to=contact['email'],
                    subject=email['subject'],
                    body=email['body'],
                    links=links,
                    wait_for_user=True  # Wait for user to send manually in browser
                )
            else:
                # Autonomous mode - auto-send
                logger.debug(f"Sending email (autonomous): {contact['email']}")

                success, message = send_email(
                    driver,
                    to=contact['email'],
                    subject=email['subject'],
                    body=email['body'],
                    links=links,
                )

            if success:
                logger.info(f"✓ Email sent to {contact['email']}")
                tracker.log_email_sent(contact, email['subject'])
                print(f"\n✓ [{idx}/{total}] Email sent to {contact['email']}")

            else:
                logger.error(f"✗ Failed to send to {contact['email']}: {message}")
                tracker.log_email_failed(contact, message)
                print(f"\n✗ [{idx}/{total}] Failed: {contact['email']}")
                print(f"   Error: {message}")

            # Update checkpoint after each email
            tracker.update_checkpoint()

            # Apply cooldown (except for last email)
            if idx < total:
                apply_cooldown(
                    min_seconds=cooldown_config['min_seconds'],
                    max_seconds=cooldown_config['max_seconds'],
                    jitter=cooldown_config.get('jitter', True),
                    show_countdown=True
                )

        except KeyboardInterrupt:
            # Propagate interrupt
            raise

        except Exception as e:
            logger.error(f"Error processing {contact['email']}: {e}", exc_info=True)
            tracker.log_email_failed(contact, str(e))
            print(f"\n✗ [{idx}/{total}] Error processing {contact['email']}")
            print(f"   {str(e)}")

            # Update checkpoint
            tracker.update_checkpoint()

            # Continue with next contact (don't crash entire campaign)
            continue

    logger.info("Campaign loop completed")


def display_campaign_summary(
    account: Dict[str, str],
    csv_path: str,
    template: Dict[str, Any],
    mode: str,
    total_contacts: int,
    start_index: int,
    settings: Dict[str, Any]
) -> None:
    """
    Display campaign configuration summary before starting.

    Args:
        account: Account dictionary
        csv_path: Path to CSV file
        template: Template dictionary
        mode: Operation mode
        total_contacts: Total number of contacts
        start_index: Starting row index
        settings: Settings dictionary
    """
    print("\n" + "="*60)
    print("CAMPAIGN CONFIGURATION")
    print("="*60)

    print(f"\nAccount:          {account['email']}")
    print(f"CSV File:         {os.path.basename(csv_path)}")
    print(f"Template:         {template['name']}")
    print(f"Mode:             {mode.upper()}")
    print(f"Total Contacts:   {total_contacts}")

    if start_index > 0:
        print(f"Resuming from:    Row {start_index}")

    # Cooldown info
    cooldown = settings['campaign']['cooldown']
    print(f"\nCooldown:         {cooldown['min_seconds']}-{cooldown['max_seconds']} seconds")
    print(f"Jitter:           {'Enabled' if cooldown.get('jitter') else 'Disabled'}")

    # LLM info
    llm = settings['llm']
    print(f"\nLLM Provider:     Groq")
    print(f"LLM Model:        {llm['model']}")

    print("\n" + "="*60)


def initialize_campaign_params(
    account: Optional[Dict[str, str]],
    csv_path: Optional[str],
    template_name: Optional[str],
    mode: Optional[str]
) -> Tuple[Dict, str, str, str]:
    """
    Initialize campaign parameters (for internal use).

    Returns:
        Tuple of (account, csv_path, template_name, mode)
    """
    settings = load_settings()

    if mode is None:
        mode = settings.get('mode', 'semi')

    if account is None:
        account = select_account_interactive()

    if csv_path is None:
        csv_path = select_csv_interactive()

    if template_name is None:
        template = select_template_interactive()
        template_name = template['name']

    return account, csv_path, template_name, mode
