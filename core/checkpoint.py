"""
Checkpoint Manager for VibeMailing
Handles campaign progress checkpointing for resume capability.
"""

import json
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
from core.logger import get_logger
from core.config_loader import get_absolute_path


logger = get_logger()


CHECKPOINT_DIR = "checkpoints"


def get_checkpoint_filename(csv_path: str, account_id: str) -> str:
    """
    Generate checkpoint filename from CSV path and account ID.

    Args:
        csv_path: Path to CSV file
        account_id: Account ID

    Returns:
        Checkpoint filename
    """
    # Create hash of CSV path for unique filename
    csv_hash = hashlib.md5(csv_path.encode()).hexdigest()[:8]
    return f"checkpoint_{account_id}_{csv_hash}.json"


def get_checkpoint_path(csv_path: str, account_id: str) -> str:
    """
    Get full path to checkpoint file.

    Args:
        csv_path: Path to CSV file
        account_id: Account ID

    Returns:
        Absolute path to checkpoint file
    """
    filename = get_checkpoint_filename(csv_path, account_id)
    checkpoint_dir = get_absolute_path(CHECKPOINT_DIR)

    # Ensure checkpoint directory exists
    Path(checkpoint_dir).mkdir(parents=True, exist_ok=True)

    return os.path.join(checkpoint_dir, filename)


def load_checkpoint(csv_path: str, account_id: str) -> Optional[Dict[str, Any]]:
    """
    Load checkpoint for campaign.

    Args:
        csv_path: Path to CSV file
        account_id: Account ID

    Returns:
        Checkpoint dictionary if exists, None otherwise
    """
    checkpoint_path = get_checkpoint_path(csv_path, account_id)

    if not os.path.exists(checkpoint_path):
        logger.debug(f"No checkpoint found: {checkpoint_path}")
        return None

    try:
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)

        logger.info(f"✓ Loaded checkpoint: {checkpoint_path}")
        logger.debug(f"Checkpoint data: {checkpoint}")

        return checkpoint

    except Exception as e:
        logger.error(f"Error loading checkpoint: {e}", exc_info=True)
        return None


def save_checkpoint(
    csv_path: str,
    account_id: str,
    account_email: str,
    template_name: str,
    mode: str,
    current_row: int,
    total_rows: int,
    sent_count: int,
    failed_count: int,
    started_at: str = None,
    metadata: Dict[str, Any] = None
) -> None:
    """
    Save checkpoint for campaign.

    Args:
        csv_path: Path to CSV file
        account_id: Account ID
        account_email: Account email address
        template_name: Email template name
        mode: Operation mode (autonomous/semi)
        current_row: Current row index
        total_rows: Total number of rows
        sent_count: Number of emails sent
        failed_count: Number of emails failed
        started_at: Campaign start timestamp (optional)
        metadata: Additional metadata (optional)
    """
    checkpoint_path = get_checkpoint_path(csv_path, account_id)

    # Load existing checkpoint for started_at if present
    existing = load_checkpoint(csv_path, account_id)
    if existing and not started_at:
        started_at = existing.get('started_at')

    checkpoint = {
        'csv_path': os.path.abspath(csv_path),
        'account_id': account_id,
        'account_email': account_email,
        'template_name': template_name,
        'mode': mode,
        'current_row': current_row,
        'total_rows': total_rows,
        'sent_count': sent_count,
        'failed_count': failed_count,
        'started_at': started_at or datetime.now().isoformat(),
        'last_updated': datetime.now().isoformat(),
        'metadata': metadata or {}
    }

    try:
        # Atomic write: write to temp file then rename
        temp_path = checkpoint_path + '.tmp'

        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, indent=2)

        # Rename (atomic on most filesystems)
        os.replace(temp_path, checkpoint_path)

        logger.debug(f"Checkpoint saved: {checkpoint_path}")

    except Exception as e:
        logger.error(f"Error saving checkpoint: {e}", exc_info=True)


def should_resume(checkpoint: Dict[str, Any]) -> bool:
    """
    Interactive prompt to resume campaign from checkpoint.

    Args:
        checkpoint: Checkpoint dictionary

    Returns:
        True if user wants to resume, False otherwise
    """
    print("\n" + "="*60)
    print("⚠️  PREVIOUS CAMPAIGN DETECTED")
    print("="*60 + "\n")

    print(f"CSV File:     {os.path.basename(checkpoint['csv_path'])}")
    print(f"Account:      {checkpoint['account_email']}")
    print(f"Template:     {checkpoint['template_name']}")
    print(f"Mode:         {checkpoint['mode']}")
    print(f"\nProgress:     {checkpoint['current_row']}/{checkpoint['total_rows']} rows")
    print(f"Sent:         {checkpoint['sent_count']}")
    print(f"Failed:       {checkpoint['failed_count']}")
    print(f"\nStarted:      {checkpoint['started_at']}")
    print(f"Last updated: {checkpoint['last_updated']}")

    print("\n" + "="*60 + "\n")

    while True:
        choice = input("Resume this campaign? (y/n): ").lower().strip()

        if choice in ['y', 'yes']:
            logger.info("User chose to resume campaign")
            return True
        elif choice in ['n', 'no']:
            logger.info("User chose not to resume campaign")
            return False
        else:
            print("Please enter 'y' or 'n'")


def clear_checkpoint(csv_path: str, account_id: str) -> None:
    """
    Delete checkpoint file.

    Args:
        csv_path: Path to CSV file
        account_id: Account ID
    """
    checkpoint_path = get_checkpoint_path(csv_path, account_id)

    if os.path.exists(checkpoint_path):
        try:
            os.remove(checkpoint_path)
            logger.info(f"✓ Checkpoint cleared: {checkpoint_path}")
        except Exception as e:
            logger.error(f"Error clearing checkpoint: {e}", exc_info=True)
    else:
        logger.debug(f"No checkpoint to clear: {checkpoint_path}")


def list_checkpoints() -> list:
    """
    List all available checkpoints.

    Returns:
        List of checkpoint file paths
    """
    checkpoint_dir = get_absolute_path(CHECKPOINT_DIR)

    if not os.path.exists(checkpoint_dir):
        return []

    checkpoints = [
        os.path.join(checkpoint_dir, f)
        for f in os.listdir(checkpoint_dir)
        if f.startswith('checkpoint_') and f.endswith('.json')
    ]

    return checkpoints
