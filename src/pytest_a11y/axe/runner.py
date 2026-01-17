"""
Selenium-bound wrapper for running axe-core accessibility checks.

Provides a clean interface to the axe-selenium-python library with proper
typing and result processing.
"""
from __future__ import annotations

from axe_selenium_python import Axe
from selenium.webdriver.remote.webdriver import WebDriver

from src.pytest_a11y.types import AxeResults, AxeRunnerProtocol, ProcessedResults


class AxeRunner:
    """
    Wrapper for axe-core accessibility checker bound to a Selenium WebDriver.
    
    Manages axe-core injection and execution, providing typed result handling
    and convenience methods for processing violations.
    
    Attributes:
        _axe: Internal Axe instance from axe-selenium-python
        _driver: Selenium WebDriver instance
    """

    def __init__(self, driver: WebDriver) -> None:
        """
        Initialize AxeRunner with a WebDriver instance.
        
        Args:
            driver: Selenium WebDriver bound to the current browser context
        """
        self._driver = driver
        self._axe = Axe(driver)

    def inject(self) -> None:
        """
        Inject axe-core library into the current page.
        
        Must be called before run() to ensure axe-core is available.
        Safe to call multiple times (idempotent).
        
        Raises:
            Exception: If injection fails (e.g., page context lost)
        """
        self._axe.inject()

    def run(self) -> AxeResults:
        """
        Run axe-core accessibility checks against the current page.
        
        Automatically injects axe-core before running to handle full page
        navigations and context changes. Safe to call multiple times on
        different pages without manual injection.
        
        Returns:
            Complete AxeResults with violations, passes, incomplete, inapplicable
            
        Raises:
            Exception: If page context is lost or axe.run() fails
            
        Notes:
            - Injection happens before every run for robustness
            - Results include all check types (violations, passes, etc.)
            - Results are typed as AxeResults TypedDict
        """
        self._axe.inject()
        return self._axe.run()

    def violation_count(self, results: AxeResults) -> int:
        """
        Count the number of violations in axe results.
        
        Args:
            results: AxeResults from a run() call
            
        Returns:
            Total number of violations found
        """
        return len(results.get("violations", []))

    def pass_count(self, results: AxeResults) -> int:
        """
        Count the number of passed checks in axe results.
        
        Args:
            results: AxeResults from a run() call
            
        Returns:
            Total number of passed checks
        """
        return len(results.get("passes", []))

    def incomplete_count(self, results: AxeResults) -> int:
        """
        Count the number of incomplete checks in axe results.
        
        Incomplete checks need manual review to determine if they're violations.
        
        Args:
            results: AxeResults from a run() call
            
        Returns:
            Total number of incomplete checks
        """
        return len(results.get("incomplete", []))

    def has_violations(self, results: AxeResults) -> bool:
        """
        Check if results contain any violations.
        
        Convenience method for conditional checks.
        
        Args:
            results: AxeResults from a run() call
            
        Returns:
            True if any violations found, False otherwise
        """
        return self.violation_count(results) > 0

    def process_results(self, results: AxeResults) -> ProcessedResults:
        """
        Convert raw axe-core results to structured ProcessedResults.
        
        Normalizes and validates all result data, making it easier to work with
        in reports and assertions. All violations and test results are converted
        to their structured dataclass equivalents.
        
        Args:
            results: Raw AxeResults from run()
            
        Returns:
            ProcessedResults with structured, typed data
            
        See Also:
            ProcessedResults.from_axe_results() for the conversion implementation
        """
        return ProcessedResults.from_axe_results(results)