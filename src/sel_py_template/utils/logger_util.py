from __future__ import annotations

import logging
from pathlib import Path


class LoggerFactory:
    """Factory for creating browser-specific loggers and sharing artifact paths.

    The factory preserves the existing logger hierarchy while also exposing the resolved
    artifact locations so that the rest of the framework can read them from one place.
    """

    _current_browser: str | None = None
    _log_dir: str | None = None
    _report_dir: str | None = None
    _a11y_dir: str | None = None
    _failure_screenshots_dir: str | None = None

    @classmethod
    def set_browser(cls, browser: str) -> None:
        """Set the current browser context for logging."""
        cls._current_browser = browser

    @classmethod
    def get_browser(cls) -> str | None:
        """Return the current browser context for logging."""
        return cls._current_browser

    @classmethod
    def set_log_dir(cls, path: str | Path) -> None:
        """Store the current run root directory."""
        cls._log_dir = str(Path(path))

    @classmethod
    def get_log_dir(cls) -> str | None:
        """Return the current run root directory."""
        return cls._log_dir

    @classmethod
    def set_report_dir(cls, path: str | Path) -> None:
        """Store the current pytest HTML artifact directory."""
        cls._report_dir = str(Path(path))

    @classmethod
    def get_report_dir(cls) -> str | None:
        """Return the current pytest HTML artifact directory."""
        return cls._report_dir

    @classmethod
    def set_a11y_dir(cls, path: str | Path) -> None:
        """Store the current accessibility artifact directory."""
        cls._a11y_dir = str(Path(path))

    @classmethod
    def get_a11y_dir(cls) -> str | None:
        """Return the current accessibility artifact directory."""
        return cls._a11y_dir

    @classmethod
    def set_failure_screenshots_dir(cls, path: str | Path) -> None:
        """Store the current failure screenshot directory."""
        cls._failure_screenshots_dir = str(Path(path))

    @classmethod
    def get_failure_screenshots_dir(cls) -> str | None:
        """Return the current failure screenshot directory."""
        return cls._failure_screenshots_dir

    @classmethod
    def get_logger(cls, name: str, browser: str | None = None) -> logging.Logger:
        """Get a logger with browser-specific hierarchy.

        Args:
            name: Logger name, typically a class or module name.
            browser: Browser name. Uses the current browser if not provided.

        Returns:
            Logger instance under the ``app.{browser}`` hierarchy.
        """
        resolved_browser = browser or cls._current_browser or "default"

        name_lower = name.lower()
        if "page" in name_lower:
            logger_name = f"app.{resolved_browser}.pages.{name}"
        elif "test" in name_lower:
            logger_name = f"app.{resolved_browser}.tests.{name}"
        else:
            logger_name = f"app.{resolved_browser}.{name}"

        logger = logging.getLogger(logger_name)

        # Keep child loggers attached to the session logger hierarchy so they inherit
        # the handlers configured by ReportPlugin on ``app`` / ``app.<browser>``.
        logger.propagate = True

        # Leave the logger level unset so the effective level is inherited from the
        # configured browser/session logger.
        logger.setLevel(logging.NOTSET)

        return logger


def get_logger(name: str, browser: str | None = None) -> logging.Logger:
    """Return a logger from :class:`LoggerFactory`.

    Args:
        name: Logger name, typically a class or module name.
        browser: Optional browser name.

    Returns:
        Configured logger instance.
    """
    return LoggerFactory.get_logger(name, browser)
