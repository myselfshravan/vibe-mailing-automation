"""
Campaign Progress Tracker for VibeMailing
Tracks email sending progress and generates statistics.
"""

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from core.logger import get_logger
from core.checkpoint import save_checkpoint
from core.config_loader import get_absolute_path


logger = get_logger()


class CampaignTracker:
    """Tracks campaign progress and statistics."""

    def __init__(
        self,
        csv_path: str,
        account_id: str,
        account_email: str,
        template_name: str,
        mode: str,
        total_rows: int,
        start_index: int = 0
    ):
        """
        Initialize campaign tracker.

        Args:
            csv_path: Path to CSV file
            account_id: Account ID
            account_email: Account email address
            template_name: Email template name
            mode: Operation mode
            total_rows: Total number of contacts
            start_index: Starting row index (for resume)
        """
        self.csv_path = os.path.abspath(csv_path)
        self.account_id = account_id
        self.account_email = account_email
        self.template_name = template_name
        self.mode = mode
        self.total_rows = total_rows
        self.start_index = start_index

        # Statistics
        self.sent_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        self.current_row = start_index

        # Timing
        self.started_at = datetime.now()
        self.email_start_times = []  # Track time per email

        logger.info(
            f"Campaign tracker initialized: {total_rows} total rows, "
            f"starting at row {start_index}"
        )

    def log_email_sent(self, contact: Dict[str, str], subject: str) -> None:
        """
        Log successful email send.

        Args:
            contact: Contact dictionary
            subject: Email subject
        """
        self.sent_count += 1
        self.current_row += 1

        logger.info(
            f"✓ Email sent [{self.sent_count}/{self.total_rows}]: "
            f"{contact['email']} - {subject}"
        )

    def log_email_failed(self, contact: Dict[str, str], error: str) -> None:
        """
        Log failed email send.

        Args:
            contact: Contact dictionary
            error: Error message
        """
        self.failed_count += 1
        self.current_row += 1

        logger.error(
            f"✗ Email failed [{self.current_row}/{self.total_rows}]: "
            f"{contact['email']} - {error}"
        )

    def log_email_skipped(self, contact: Dict[str, str], reason: str = "User skipped") -> None:
        """
        Log skipped email.

        Args:
            contact: Contact dictionary
            reason: Reason for skipping
        """
        self.skipped_count += 1
        self.current_row += 1

        logger.info(
            f"⊘ Email skipped [{self.current_row}/{self.total_rows}]: "
            f"{contact['email']} - {reason}"
        )

    def log_email_attempt(
        self,
        contact: Dict[str, str],
        status: str,
        details: Dict[str, Any] = None
    ) -> None:
        """
        Log email attempt (generic).

        Args:
            contact: Contact dictionary
            status: Status (sent, failed, skipped)
            details: Additional details
        """
        if status == "sent":
            self.log_email_sent(contact, details.get('subject', 'N/A') if details else 'N/A')
        elif status == "failed":
            self.log_email_failed(contact, details.get('error', 'Unknown') if details else 'Unknown')
        elif status == "skipped":
            self.log_email_skipped(contact, details.get('reason', 'User skipped') if details else 'User skipped')

    def update_checkpoint(self) -> None:
        """Save current progress to checkpoint."""
        save_checkpoint(
            csv_path=self.csv_path,
            account_id=self.account_id,
            account_email=self.account_email,
            template_name=self.template_name,
            mode=self.mode,
            current_row=self.current_row,
            total_rows=self.total_rows,
            sent_count=self.sent_count,
            failed_count=self.failed_count,
            started_at=self.started_at.isoformat()
        )

        logger.debug(f"Checkpoint updated: row {self.current_row}/{self.total_rows}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get campaign statistics.

        Returns:
            Statistics dictionary
        """
        elapsed_time = (datetime.now() - self.started_at).total_seconds()
        processed = self.sent_count + self.failed_count + self.skipped_count

        success_rate = (
            (self.sent_count / processed * 100)
            if processed > 0
            else 0
        )

        avg_time_per_email = (
            elapsed_time / processed
            if processed > 0
            else 0
        )

        return {
            'total_contacts': self.total_rows,
            'processed': processed,
            'sent': self.sent_count,
            'failed': self.failed_count,
            'skipped': self.skipped_count,
            'remaining': self.total_rows - processed,
            'success_rate': round(success_rate, 1),
            'avg_time_per_email': round(avg_time_per_email, 1),
            'total_duration_seconds': round(elapsed_time, 1),
            'total_duration_minutes': round(elapsed_time / 60, 1),
            'started_at': self.started_at.isoformat(),
            'completed_at': datetime.now().isoformat() if processed >= self.total_rows else None
        }

    def generate_summary_report(self) -> str:
        """
        Generate human-readable summary report.

        Returns:
            Summary report string
        """
        stats = self.get_statistics()

        report = "\n" + "="*60 + "\n"
        report += "CAMPAIGN SUMMARY\n"
        report += "="*60 + "\n\n"

        report += f"Account:          {self.account_email}\n"
        report += f"Template:         {self.template_name}\n"
        report += f"Mode:             {self.mode}\n"
        report += f"CSV File:         {os.path.basename(self.csv_path)}\n\n"

        report += f"Total Contacts:   {stats['total_contacts']}\n"
        report += f"Processed:        {stats['processed']}\n"
        report += f"  ✓ Sent:         {stats['sent']}\n"
        report += f"  ✗ Failed:       {stats['failed']}\n"
        report += f"  ⊘ Skipped:      {stats['skipped']}\n"
        report += f"Remaining:        {stats['remaining']}\n\n"

        report += f"Success Rate:     {stats['success_rate']}%\n"
        report += f"Duration:         {stats['total_duration_minutes']} minutes\n"
        report += f"Avg Time/Email:   {stats['avg_time_per_email']} seconds\n\n"

        report += f"Started:          {stats['started_at']}\n"
        if stats['completed_at']:
            report += f"Completed:        {stats['completed_at']}\n"

        report += "\n" + "="*60 + "\n"

        return report

    def save_campaign_history(self) -> None:
        """Save campaign history to log file."""
        history_dir = get_absolute_path("logs/campaign_history")
        Path(history_dir).mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"campaign_{self.account_id}_{timestamp}.log"
        filepath = os.path.join(history_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.generate_summary_report())
                f.write("\n\nDetailed Statistics:\n")
                f.write("-" * 60 + "\n")

                stats = self.get_statistics()
                for key, value in stats.items():
                    f.write(f"{key}: {value}\n")

            logger.info(f"✓ Campaign history saved: {filepath}")

        except Exception as e:
            logger.error(f"Error saving campaign history: {e}", exc_info=True)

    def display_progress(self) -> None:
        """Display current progress to console."""
        stats = self.get_statistics()

        print(f"\n[Progress: {stats['processed']}/{stats['total_contacts']} | "
              f"Sent: {stats['sent']} | Failed: {stats['failed']} | "
              f"Skipped: {stats['skipped']}]")
