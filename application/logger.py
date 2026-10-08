"""
Production Logging & Log Rotation System for CourtVision.
Logs application lifecycle events, stream state changes, AI model events, and exceptions
to logs/courtvision.log using rotating file handlers and credential sanitization.
"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler

from application.paths import get_logs_dir
from application.video_input import sanitize_url
from application.version import get_version_string

_logger_instance = None


def setup_logger(log_filename="courtvision.log", max_bytes=5 * 1024 * 1024, backup_count=3):
    """
    Initialize and return global CourtVision rotating logger.
    """
    global _logger_instance
    if _logger_instance is not None:
        return _logger_instance

    logs_dir = get_logs_dir()
    log_path = os.path.join(logs_dir, log_filename)

    logger = logging.getLogger("CourtVision")
    logger.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Rotating File Handler
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console Handler for stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    _logger_instance = logger
    logger.info(f"--- Started {get_version_string()} ---")
    return logger


def get_logger():
    """Get initialized logger instance."""
    global _logger_instance
    if _logger_instance is None:
        return setup_logger()
    return _logger_instance


def log_info(msg):
    get_logger().info(sanitize_url(str(msg)))


def log_warning(msg):
    get_logger().warning(sanitize_url(str(msg)))


def log_error(msg, exc_info=False):
    get_logger().error(sanitize_url(str(msg)), exc_info=exc_info)
