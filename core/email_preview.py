"""
Email Preview for VibeMailing
Handles email preview and user confirmation (semi-auto mode).
"""

from typing import Dict
from core.logger import get_logger


logger = get_logger()


def preview_email(
    recipient: str,
    subject: str,
    body: str,
    contact_index: int,
    total_contacts: int,
    contact: Dict[str, str] = None
) -> str:
    """
    Display email preview and get user decision.

    Args:
        recipient: Email recipient
        subject: Email subject
        body: Email body
        contact_index: Current contact index (1-based)
        total_contacts: Total number of contacts
        contact: Full contact dict (optional, for display)

    Returns:
        User action: "send", "skip", "edit", "abort"
    """
    print("\n" + "━"*60)
    print(f"Email Preview [{contact_index}/{total_contacts}]")
    print("━"*60)

    if contact:
        print(f"\nContact:  {contact.get('name', 'N/A')} ({contact.get('company', 'N/A')})")

    print(f"To:       {recipient}")
    print(f"Subject:  {subject}")
    print("\nBody:")
    print("-" * 60)
    print(body)
    print("-" * 60)

    print("\nOptions:")
    print("  [s] Send this email")
    print("  [k] Skip this contact")
    print("  [e] Edit email body")
    print("  [a] Abort campaign")
    print()

    while True:
        choice = input("Your choice (s/k/e/a): ").lower().strip()

        if choice in ['s', 'send']:
            logger.info(f"User chose to send email to {recipient}")
            return "send"

        elif choice in ['k', 'skip']:
            logger.info(f"User chose to skip email to {recipient}")
            return "skip"

        elif choice in ['e', 'edit']:
            logger.info(f"User chose to edit email for {recipient}")
            return "edit"

        elif choice in ['a', 'abort']:
            # Confirm abort
            confirm = input("\n⚠️  Abort entire campaign? (y/n): ").lower().strip()
            if confirm in ['y', 'yes']:
                logger.warning("User chose to abort campaign")
                return "abort"
            else:
                print("\nContinuing...")
                continue

        else:
            print("Invalid choice. Please enter s, k, e, or a")


def edit_email_body(original_body: str) -> str:
    """
    Simple inline editor for email body.
    User can provide a completely new body.

    Args:
        original_body: Original email body

    Returns:
        Edited email body
    """
    print("\n" + "="*60)
    print("EDIT MODE")
    print("="*60)
    print("\nCurrent body:")
    print("-" * 60)
    print(original_body)
    print("-" * 60)

    print("\nEnter new body below.")
    print("Type 'END' on a new line when done.")
    print("Type 'CANCEL' to keep original.")
    print()

    lines = []
    while True:
        try:
            line = input()

            if line.strip() == 'END':
                break
            elif line.strip() == 'CANCEL':
                logger.info("Edit cancelled, keeping original body")
                return original_body

            lines.append(line)

        except EOFError:
            break
        except KeyboardInterrupt:
            logger.info("Edit interrupted, keeping original body")
            return original_body

    new_body = '\n'.join(lines)

    if new_body.strip():
        logger.info(f"Email body edited: {len(new_body)} characters")
        return new_body
    else:
        logger.warning("Empty body provided, keeping original")
        return original_body


def edit_email_subject(original_subject: str) -> str:
    """
    Edit email subject.

    Args:
        original_subject: Original subject

    Returns:
        Edited subject
    """
    print(f"\nCurrent subject: {original_subject}")
    new_subject = input("Enter new subject (or press Enter to keep): ").strip()

    if new_subject:
        logger.info(f"Subject changed: {original_subject} -> {new_subject}")
        return new_subject
    else:
        return original_subject


def format_preview_display(
    recipient: str,
    subject: str,
    body: str,
    index: int = None,
    total: int = None
) -> str:
    """
    Format email preview for display.

    Args:
        recipient: Email recipient
        subject: Email subject
        body: Email body
        index: Current index (optional)
        total: Total count (optional)

    Returns:
        Formatted preview string
    """
    lines = []

    lines.append("━"*60)

    if index and total:
        lines.append(f"Email Preview [{index}/{total}]")
    else:
        lines.append("Email Preview")

    lines.append("━"*60)
    lines.append(f"\nTo:      {recipient}")
    lines.append(f"Subject: {subject}")
    lines.append("\nBody:")
    lines.append("-" * 60)
    lines.append(body)
    lines.append("-" * 60)

    return "\n".join(lines)


def confirm_send(message: str = "Send this email?") -> bool:
    """
    Simple yes/no confirmation.

    Args:
        message: Confirmation message

    Returns:
        True if confirmed, False otherwise
    """
    while True:
        choice = input(f"\n{message} (y/n): ").lower().strip()

        if choice in ['y', 'yes']:
            return True
        elif choice in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' or 'n'")
