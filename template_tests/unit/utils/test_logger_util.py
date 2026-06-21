from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

from sel_py_template.utils.logger_util import LoggerFactory, get_logger


def test_setters_and_getters_store_paths_and_browser(tmp_path: Path) -> None:
    """Store and return browser and artifact path values."""
    LoggerFactory.set_browser("chrome")
    LoggerFactory.set_log_dir(tmp_path / "run")
    LoggerFactory.set_report_dir(tmp_path / "pytest_html")
    LoggerFactory.set_a11y_dir(tmp_path / "a11y")
    LoggerFactory.set_failure_screenshots_dir(tmp_path / "shots")

    assert LoggerFactory.get_browser() == "chrome"
    assert LoggerFactory.get_log_dir() == str(tmp_path / "run")
    assert LoggerFactory.get_report_dir() == str(tmp_path / "pytest_html")
    assert LoggerFactory.get_a11y_dir() == str(tmp_path / "a11y")
    assert LoggerFactory.get_failure_screenshots_dir() == str(tmp_path / "shots")


@patch("sel_py_template.utils.logger_util.logging.getLogger")
def test_get_logger_uses_page_hierarchy(mock_get_logger: logging.Logger) -> None:
    """Create page loggers under the page-specific hierarchy."""
    logger = logging.getLogger("placeholder")
    mock_get_logger.return_value = logger
    LoggerFactory.set_browser("firefox")

    result = LoggerFactory.get_logger("BasePage")

    assert result is logger
    assert logger.propagate is True


@patch("sel_py_template.utils.logger_util.logging.getLogger")
def test_get_logger_uses_test_hierarchy(mock_get_logger: logging.Logger) -> None:
    """Create test loggers under the test-specific hierarchy."""
    logger = MagicMock(spec=logging.Logger)
    mock_get_logger.return_value = logger

    LoggerFactory.set_browser("edge")
    result = LoggerFactory.get_logger("TestLogin")

    mock_get_logger.assert_called_once_with("app.edge.tests.TestLogin")
    assert result is logger


@patch("sel_py_template.utils.logger_util.logging.getLogger")
def test_get_logger_uses_default_hierarchy(mock_get_logger: logging.Logger) -> None:
    """Create generic loggers under the browser root hierarchy."""
    logger = MagicMock(spec=logging.Logger)
    mock_get_logger.return_value = logger

    LoggerFactory.set_browser("chrome")
    result = LoggerFactory.get_logger("helpers")

    mock_get_logger.assert_called_once_with("app.chrome.helpers")
    assert result is logger


@patch("sel_py_template.utils.logger_util.LoggerFactory.get_logger")
def test_module_get_logger_delegates_to_factory(
    mock_get_logger: logging.Logger,
) -> None:
    """Delegate the top-level helper to the logger factory."""
    sentinel = logging.getLogger("sentinel")
    mock_get_logger.return_value = sentinel

    result = get_logger("BasePage", browser="chrome")

    mock_get_logger.assert_called_once_with("BasePage", "chrome")
    assert result is sentinel


@patch("sel_py_template.utils.logger_util.logging.getLogger")
def test_get_logger_uses_default_browser_when_unset(
    mock_get_logger: logging.Logger,
) -> None:
    """Fall back to the default browser label when no browser has been configured."""
    logger = MagicMock(spec=logging.Logger)
    mock_get_logger.return_value = logger
    LoggerFactory._current_browser = None

    LoggerFactory.get_logger("utility")

    mock_get_logger.assert_called_once_with("app.default.utility")
