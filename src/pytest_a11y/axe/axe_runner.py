from __future__ import annotations

from axe_selenium_python import Axe
from selenium.webdriver.remote.webdriver import WebDriver

from src.pytest_a11y.types import AxeResults


class AxeRunner:
    """Selenium-bound wrapper for running axe-core in the current page context."""

    def __init__(self, driver: WebDriver) -> None:
        self._axe = Axe(driver)

    def inject(self) -> None:
        """Inject axe-core into the current page."""
        self._axe.inject()

    def run(self) -> AxeResults:
        """
        Run axe-core against the current page.

        Notes:
            We inject before running to handle full page navigations.
        """
        self._axe.inject()
        return self._axe.run()

    def violation_count(self, results: AxeResults) -> int:
        """Return the number of violations in an axe result payload."""
        return len(results.get("violations", []))
