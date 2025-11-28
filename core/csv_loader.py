"""
CSV Loader for VibeMailing
Handles contact list loading and validation.
"""

import csv
import os
import re
from typing import List, Dict, Tuple
from core.logger import get_logger


logger = get_logger()


# Required CSV columns
REQUIRED_COLUMNS = ['name', 'company', 'email', 'linkedin']


def is_valid_email(email: str) -> bool:
    """
    Basic email format validation.

    Args:
        email: Email address to validate

    Returns:
        True if valid format, False otherwise
    """
    if not email:
        return False

    # Basic email regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_csv_structure(file_path: str) -> Tuple[bool, str]:
    """
    Validate CSV file structure and content.

    Args:
        file_path: Path to CSV file

    Returns:
        Tuple of (is_valid, error_message)
    """
    logger.debug(f"Validating CSV: {file_path}")

    try:
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"

        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

            if not headers:
                return False, "CSV file is empty or has no headers"

            # Check required columns
            missing_cols = [col for col in REQUIRED_COLUMNS if col not in headers]
            if missing_cols:
                return False, f"Missing required columns: {', '.join(missing_cols)}"

            # Check at least one row exists
            rows = list(reader)
            if not rows:
                return False, "CSV file has no data rows"

            # Validate first few rows
            for idx, row in enumerate(rows[:5], 1):
                # Check for empty required fields
                for col in REQUIRED_COLUMNS:
                    if not row.get(col, '').strip():
                        return False, f"Row {idx}: Empty value for '{col}'"

                # Validate email format
                email = row.get('email', '').strip()
                if not is_valid_email(email):
                    return False, f"Row {idx}: Invalid email format '{email}'"

            logger.info(f"✓ CSV validation passed: {len(rows)} contacts")
            return True, "Valid"

    except Exception as e:
        logger.error(f"CSV validation error: {e}", exc_info=True)
        return False, f"Error reading CSV: {str(e)}"


def load_csv(file_path: str) -> List[Dict[str, str]]:
    """
    Load contacts from CSV file.

    Args:
        file_path: Path to CSV file

    Returns:
        List of contact dictionaries

    Raises:
        ValueError: If CSV validation fails
        FileNotFoundError: If file doesn't exist
    """
    logger.info(f"Loading CSV: {file_path}")

    # Validate first
    is_valid, error_msg = validate_csv_structure(file_path)
    if not is_valid:
        raise ValueError(f"CSV validation failed: {error_msg}")

    contacts = []

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for idx, row in enumerate(reader, 1):
            contact = {
                'name': row['name'].strip(),
                'company': row['company'].strip(),
                'email': row['email'].strip(),
                'linkedin': row['linkedin'].strip(),
                'row_index': idx  # Track original row number
            }
            contacts.append(contact)

    logger.info(f"✓ Loaded {len(contacts)} contacts from CSV")

    return contacts


def select_csv_interactive() -> str:
    """
    Interactive CSV file selection.

    Returns:
        Path to selected CSV file

    Raises:
        KeyboardInterrupt: If user cancels
        ValueError: If file not found or invalid
    """
    print("\n" + "="*60)
    print("CSV File Selection")
    print("="*60 + "\n")

    while True:
        file_path = input("Enter path to CSV file (or 'cancel' to exit): ").strip()

        if file_path.lower() in ['cancel', 'exit', 'quit']:
            logger.info("CSV selection cancelled by user")
            raise KeyboardInterrupt("CSV selection cancelled")

        # Remove quotes if present
        file_path = file_path.strip('"\'')

        # Validate
        is_valid, error_msg = validate_csv_structure(file_path)

        if is_valid:
            logger.info(f"Selected CSV: {file_path}")
            return file_path
        else:
            print(f"\n✗ Invalid CSV: {error_msg}")
            print("Please try again.\n")


def get_csv_summary(contacts: List[Dict[str, str]]) -> Dict:
    """
    Get summary statistics for contact list.

    Args:
        contacts: List of contact dictionaries

    Returns:
        Summary dictionary
    """
    if not contacts:
        return {
            'total': 0,
            'unique_companies': 0,
            'unique_emails': 0
        }

    emails = [c['email'] for c in contacts]
    companies = [c['company'] for c in contacts]

    return {
        'total': len(contacts),
        'unique_emails': len(set(emails)),
        'unique_companies': len(set(companies)),
        'has_duplicates': len(emails) != len(set(emails))
    }


def display_csv_summary(contacts: List[Dict[str, str]]) -> None:
    """
    Display CSV summary to user.

    Args:
        contacts: List of contact dictionaries
    """
    summary = get_csv_summary(contacts)

    print("\n" + "="*60)
    print("CSV Summary")
    print("="*60)
    print(f"Total contacts:       {summary['total']}")
    print(f"Unique emails:        {summary['unique_emails']}")
    print(f"Unique companies:     {summary['unique_companies']}")

    if summary['has_duplicates']:
        print("\n⚠️  Warning: CSV contains duplicate emails")

    print("="*60 + "\n")


def preview_contacts(contacts: List[Dict[str, str]], count: int = 3) -> None:
    """
    Display preview of first few contacts.

    Args:
        contacts: List of contact dictionaries
        count: Number of contacts to preview
    """
    print("\n" + "="*60)
    print(f"Contact Preview (first {min(count, len(contacts))} contacts)")
    print("="*60 + "\n")

    for idx, contact in enumerate(contacts[:count], 1):
        print(f"{idx}. {contact['name']}")
        print(f"   Company:  {contact['company']}")
        print(f"   Email:    {contact['email']}")
        print(f"   LinkedIn: {contact['linkedin']}")
        print()

    if len(contacts) > count:
        print(f"... and {len(contacts) - count} more contacts")

    print("="*60 + "\n")
