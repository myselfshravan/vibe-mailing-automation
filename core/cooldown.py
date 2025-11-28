"""
Cooldown Manager for VibeMailing
Implements rate limiting with random cooldown between emails.
"""

import random
import time
import sys
from core.logger import get_logger


logger = get_logger()


def calculate_cooldown(
    min_seconds: int,
    max_seconds: int,
    jitter: bool = True
) -> float:
    """
    Calculate random cooldown duration with optional jitter.

    Args:
        min_seconds: Minimum cooldown time
        max_seconds: Maximum cooldown time
        jitter: Add random jitter (±10%)

    Returns:
        Cooldown duration in seconds
    """
    # Base random wait
    base_wait = random.uniform(min_seconds, max_seconds)

    if jitter:
        # Add ±10% random jitter
        jitter_amount = base_wait * 0.1
        jitter_value = random.uniform(-jitter_amount, jitter_amount)
        base_wait += jitter_value

    # Ensure we don't go below minimum
    wait_time = max(min_seconds, base_wait)

    logger.debug(f"Calculated cooldown: {wait_time:.1f} seconds")

    return wait_time


def apply_cooldown(
    min_seconds: int,
    max_seconds: int,
    jitter: bool = True,
    show_countdown: bool = True
) -> None:
    """
    Apply cooldown with optional visual countdown.

    Args:
        min_seconds: Minimum cooldown time
        max_seconds: Maximum cooldown time
        jitter: Add random jitter
        show_countdown: Display countdown timer
    """
    wait_time = calculate_cooldown(min_seconds, max_seconds, jitter)

    logger.info(f"Applying cooldown: {wait_time:.1f} seconds")

    if show_countdown:
        display_countdown(wait_time)
    else:
        time.sleep(wait_time)


def display_countdown(total_seconds: float) -> None:
    """
    Display live countdown timer in terminal.

    Args:
        total_seconds: Total countdown time in seconds
    """
    total = int(total_seconds)

    print(f"\n⏳ Cooling down for {total} seconds...", end="")
    sys.stdout.flush()

    remaining = total
    while remaining > 0:
        # Clear line and display countdown
        print(f"\r⏳ Cooling down: {remaining} seconds remaining...  ", end="")
        sys.stdout.flush()

        time.sleep(1)
        remaining -= 1

    # Clear line and show completion
    print(f"\r✓ Cooldown complete" + " " * 40)
    sys.stdout.flush()


def format_countdown(seconds: int) -> str:
    """
    Format seconds as human-readable time.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted string (e.g., "1m 30s")
    """
    if seconds < 60:
        return f"{seconds}s"

    minutes = seconds // 60
    secs = seconds % 60

    if minutes < 60:
        return f"{minutes}m {secs}s"

    hours = minutes // 60
    mins = minutes % 60

    return f"{hours}h {mins}m {secs}s"


def apply_cooldown_with_context(
    min_seconds: int,
    max_seconds: int,
    current_index: int,
    total_count: int,
    jitter: bool = True
) -> None:
    """
    Apply cooldown with context information.

    Args:
        min_seconds: Minimum cooldown time
        max_seconds: Maximum cooldown time
        current_index: Current email index
        total_count: Total email count
        jitter: Add random jitter
    """
    wait_time = calculate_cooldown(min_seconds, max_seconds, jitter)

    logger.info(
        f"Cooldown [{current_index}/{total_count}]: "
        f"{wait_time:.1f} seconds"
    )

    print(f"\n[{current_index}/{total_count}] ", end="")
    display_countdown(wait_time)


def estimate_remaining_time(
    remaining_emails: int,
    avg_cooldown: int,
    avg_processing_time: int = 10
) -> str:
    """
    Estimate remaining campaign time.

    Args:
        remaining_emails: Number of remaining emails
        avg_cooldown: Average cooldown time in seconds
        avg_processing_time: Average time per email (generation + sending)

    Returns:
        Formatted time estimate
    """
    total_time_per_email = avg_cooldown + avg_processing_time
    total_seconds = remaining_emails * total_time_per_email

    return format_countdown(total_seconds)


def wait_with_interrupt(seconds: float, check_interval: float = 1.0) -> bool:
    """
    Wait with ability to interrupt.

    Args:
        seconds: Total wait time
        check_interval: How often to check for interrupt

    Returns:
        True if completed normally, False if interrupted
    """
    elapsed = 0.0

    while elapsed < seconds:
        try:
            sleep_time = min(check_interval, seconds - elapsed)
            time.sleep(sleep_time)
            elapsed += sleep_time
        except KeyboardInterrupt:
            logger.warning("Cooldown interrupted by user")
            return False

    return True
