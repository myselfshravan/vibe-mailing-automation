"""
Logging System for VibeMailing
Provides centralized logging with file and console handlers.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


_logger_instance: Optional[logging.Logger] = None


def setup_logger(log_file: str, level: str = "INFO") -> logging.Logger:
    """
    Sets up the main logger with file and console handlers.

    Args:
        log_file: Path to log file
        level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger instance
    """
    global _logger_instance

    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir:
        Path(log_dir).mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger("VibeMailing")
    logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    logger.handlers.clear()

    # File handler with rotation (max 10MB, keep 5 backups)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, level.upper()))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Console shows INFO and above

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    _logger_instance = logger

    logger.info("="*60)
    logger.info("VibeMailing Logger Initialized")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Log level: {level}")
    logger.info("="*60)

    return logger


def get_logger(name: str = "VibeMailing") -> logging.Logger:
    """
    Gets the logger instance.

    Args:
        name: Logger name (default: VibeMailing)

    Returns:
        Logger instance
    """
    if _logger_instance is None:
        # If not initialized, create a basic logger
        return logging.getLogger(name)
    return _logger_instance


def log_info(message: str) -> None:
    """Log info message"""
    get_logger().info(message)


def log_warning(message: str) -> None:
    """Log warning message"""
    get_logger().warning(message)


def log_error(message: str, exc: Optional[Exception] = None) -> None:
    """Log error message with optional exception"""
    if exc:
        get_logger().error(message, exc_info=True)
    else:
        get_logger().error(message)


def log_debug(message: str) -> None:
    """Log debug message"""
    get_logger().debug(message)
