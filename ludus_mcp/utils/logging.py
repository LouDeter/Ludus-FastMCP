"""Logging configuration."""

import logging
import sys
from pathlib import Path
from typing import Any

from .config import get_settings

LOG_FILE = Path.home() / ".ludus-fastmcp" / "ludus-fastmcp.log"


class UserFriendlyFormatter(logging.Formatter):
    """Formatter that produces clean, user-friendly log messages."""

    # Simplified format for INFO and below
    SIMPLE_FORMAT = "%(message)s"
    # Detailed format for WARNING and above
    DETAILED_FORMAT = "%(levelname)s: %(message)s"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record based on level."""
        if record.levelno <= logging.INFO:
            formatter = logging.Formatter(self.SIMPLE_FORMAT)
        else:
            formatter = logging.Formatter(self.DETAILED_FORMAT)
        return formatter.format(record)


def setup_logging(quiet: bool = False, log_to_file: bool = True) -> None:
    """Configure application logging with user-friendly output.

    Args:
        quiet: Suppress most logs regardless of configured level.
        log_to_file: Also write logs to LOG_FILE. Should be False in daemon
            mode, where stderr is already redirected to that same file at
            the OS level (os.dup2), to avoid writing each line twice.
    """
    settings = get_settings()
    configured_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    # In quiet mode, suppress stderr output regardless of configured level,
    # but the log file (if enabled) still honors the configured level so
    # DEBUG/INFO logs remain available for troubleshooting even when the
    # server was launched quietly by an MCP client.
    stderr_level = logging.WARNING if quiet else configured_level

    # Create handler with user-friendly formatter
    handler = logging.StreamHandler(sys.stderr)  # Use stderr for logs
    handler.setFormatter(UserFriendlyFormatter())
    handler.setLevel(stderr_level)

    handlers: list[logging.Handler] = [handler]
    root_level = stderr_level

    if log_to_file:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
        )
        file_handler.setLevel(configured_level)
        handlers.append(file_handler)
        root_level = min(root_level, configured_level)

    # Configure root logger. setup_logging() may be called more than once in
    # the same process (e.g. once at import time, again after CLI args are
    # parsed) - close prior handlers so file handles from an earlier call
    # aren't leaked.
    root_logger = logging.getLogger()
    for old_handler in root_logger.handlers:
        old_handler.close()
    root_logger.setLevel(root_level)
    root_logger.handlers = handlers

    # Suppress verbose logs from dependencies
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module."""
    return logging.getLogger(name)

