# utils/logging_utils.py
import logging
from pathlib import Path


class LoggerFactory:
    """Factory for creating browser-specific loggers."""

    _current_browser: str | None = None
    _log_dir: str | None = None
    _report_dir: str | None = None

    @classmethod
    def set_browser(cls, browser: str) -> None:
        """Set the current browser context for logging."""
        cls._current_browser = browser

    @classmethod
    def set_log_dir(cls, path: str | Path) -> None:
        cls._log_dir = str(Path(path))

    @classmethod
    def get_log_dir(cls) -> str | None:
        return cls._log_dir

    @classmethod
    def set_report_dir(cls, path: str | Path) -> None:
        cls._report_dir = str(Path(path))

    @classmethod
    def get_report_dir(cls) -> str | None:
        return cls._report_dir

    @classmethod
    def get_logger(cls, name: str, browser: str | None = None) -> logging.Logger:
        """
        Get a logger with browser-specific hierarchy.

        Args:
            name: Logger name (typically class name)
            browser: Browser name (uses current browser if not specified)

        Returns:
            Logger instance under 'app.{browser}' hierarchy

        Example:
            >>> logger = LoggerFactory.get_logger("InventoryPage", browser="chrome")
            >>> # Returns logger named "app.chrome.pages.InventoryPage"
        """
        browser = browser or cls._current_browser or "default"

        # Build hierarchical name
        name_lower = name.lower()
        if "page" in name_lower:
            logger_name = f"app.{browser}.pages.{name}"
        elif "test" in name_lower:
            logger_name = f"app.{browser}.tests.{name}"
        else:
            logger_name = f"app.{browser}.{name}"

        return logging.getLogger(logger_name)


def get_logger(name: str, browser: str | None = None) -> logging.Logger:
    """
    Convenience function to get a logger.

    Args:
        name: Logger name (typically class name)
        browser: Browser name (optional)

    Returns:
        Logger instance
    """
    return LoggerFactory.get_logger(name, browser)
