"""
Pytest plugin for accessibility testing with axe-core.

Provides the check_a11y fixture which runs accessibility checks,
generates reports, captures screenshots, and asserts on violations.
"""
from __future__ import annotations

import hashlib
import os
from collections.abc import Callable
from pathlib import Path

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from src.pytest_a11y.assertions import assert_no_axe_violations
from src.pytest_a11y.reporting.html_report import generate_a11y_report
from src.pytest_a11y.reporting.json_report import write_a11y_json_report
from src.pytest_a11y.types import A11YRunResults, AxeResults, AxeRunnerProtocol
from src.pytest_a11y.visual.axe_overlay import capture_all_violations_individually
from src.utils.logger_util import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


# ============================================================================
# Pytest hooks
# ============================================================================

def pytest_addoption(parser: pytest.Parser) -> None:
    """
    Register CLI options for the a11y plugin.
    
    Adds --a11y flag to enable accessibility testing.
    
    Args:
        parser: pytest argument parser
    """
    parser.addoption(
        "--a11y",
        action="store_true",
        default=False,
        help="Run axe-core accessibility checks (and generate reports).",
    )


# ============================================================================
# Utilities
# ============================================================================

def _safe_slug(text: str, max_len: int = 10) -> str:
    """
    Convert a string into a filesystem-friendly slug.
    
    Replaces invalid characters with underscores and truncates to max length.
    
    Args:
        text: Input text (typically pytest test name)
        max_len: Maximum length of the output slug
    
    Returns:
        Filesystem-safe slug string
    """
    keep: list[str] = []
    for ch in text:
        if ch.isalnum() or ch in ("-", "_", "."):
            keep.append(ch)
        else:
            keep.append("_")
    slug = "".join(keep)
    return slug[:max_len].strip("_") or "a11y"


def _nodeid_hash(nodeid: str, length: int = 10) -> str:
    """
    Generate a stable hash for pytest nodeid.
    
    Creates a unique identifier for test variations (parameters, xdist workers).
    Uses blake2b for speed and security compliance.
    
    Args:
        nodeid: pytest nodeid (file::test_name[params])
        length: Length of hex string to return
    
    Returns:
        Hex digest string truncated to requested length
    """
    digest_size = max(4, length // 2 + 1)
    return hashlib.blake2b(
        nodeid.encode("utf-8"),
        digest_size=digest_size,
    ).hexdigest()[:length]


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def check_a11y(
    driver: WebDriver,
    request: pytest.FixtureRequest,
    axe: AxeRunnerProtocol,
) -> Callable[[], A11YRunResults]:
    """
    Run axe-core accessibility checks on demand.
    
    This fixture provides a callable that executes a11y checks and generates
    HTML/JSON reports and individual violation screenshots. Reports are only
    generated when --a11y CLI flag is provided.
    
    Behavior:
        - Without --a11y: fixture skips when invoked
        - With --a11y: runs checks, captures screenshots, generates reports
    
    Report locations (when --a11y enabled):
        - HTML: <a11y_dir>/<test_name>__<worker>__<hash>.html
        - JSON: <a11y_dir>/<test_name>__<worker>__<hash>.json
        - Screenshots: <a11y_dir>/violation_screenshots/<index>_<rule_id>.png
    
    File naming is xdist-safe (includes worker_id and nodeid hash).
    
    Args:
        driver: Selenium WebDriver fixture
        request: pytest request fixture (provides test metadata)
        axe: AxeRunnerProtocol fixture (implements axe.run())
    
    Returns:
        Callable that executes checks and returns A11YRunResults dict
        
    Raises:
        pytest.skip: When --a11y flag not provided
        AssertionError: When violations found (if assertions enabled)
    """
    enabled: bool = bool(request.config.getoption("--a11y"))
    if not enabled:
        def _skipped() -> A11YRunResults:
            pytest.skip("Accessibility checks not enabled (use --a11y)")
            raise RuntimeError("unreachable")  # for type checkers
        return _skipped

    # Resolve a11y report directory
    try:
        a11y_dir = LoggerFactory.get_a11y_dir()
    except Exception:
        a11y_dir = os.getcwd()

    # Generate xdist-safe filenames
    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "master")
    nodeid = request.node.nodeid
    name = _safe_slug(request.node.name)
    h = _nodeid_hash(nodeid)

    base = f"{name}__{worker_id}__{h}"
    html_path = os.path.join(a11y_dir, f"{base}.html")
    json_path = os.path.join(a11y_dir, f"{base}.json")
    screenshot_dir = os.path.join(a11y_dir, "violation_screenshots")

    def _run() -> A11YRunResults:
        """
        Execute accessibility checks and generate reports.
        
        Steps:
            1. Run axe-core checks
            2. Capture individual violation screenshots
            3. Generate HTML report with screenshots
            4. Generate JSON report for CI/archival
            5. Assert on violations (writes reports first)
        
        Returns:
            Dictionary with paths to generated reports and results
        """
        # Run axe-core checks
        axe_results: AxeResults | None = axe.run()
        
        # Capture individual violation screenshots (mutates axe_results in-place)
        if axe_results:
            capture_all_violations_individually(
                driver,
                axe_results,
                screenshot_dir=screenshot_dir,
            )
        
        # Always write reports (even if no violations)
        generate_a11y_report(
            axe_results=axe_results,
            page_url=driver.current_url,
            output_path=html_path,
        )
        write_a11y_json_report(
            axe_results=axe_results,
            page_url=driver.current_url,
            output_path=json_path,
        )

        # Assert last (so reports/screenshots written first for debugging)
        if axe_results is not None:
            assert_no_axe_violations(axe_results)

        return {
            "axe": axe_results,
            "html_report": html_path,
            "json_report": json_path,
            "screenshot_dir": screenshot_dir,
        }

    return _run