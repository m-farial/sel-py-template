from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path

from selenium.webdriver.remote.webdriver import WebDriver

from src.utils.logger_util import LoggerFactory


def save_violation_screenshot(driver, test_name, violation_id, impact):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    a11y_dir = LoggerFactory.get_a11y_dir() or os.getcwd()
    filename = f"{test_name}_{violation_id}_{impact}_{timestamp}.png"
    path = a11y_dir / filename

    try:
        driver.save_screenshot(str(path))
        return str(path)
    except Exception:
        return None


def save_screenshot(driver: WebDriver, path: Path | str) -> Path:
    """
    Save a PNG screenshot to the given path.

    Args:
        driver: Selenium WebDriver instance.
        path: Output path (Path or str).

    Returns:
        The resolved Path to the saved screenshot.
    """
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    driver.save_screenshot(str(out))
    return out
