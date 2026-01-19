"""
Pytest plugin for accessibility testing with axe-core.

Provides CLI options, fixtures, and report generation for accessibility checks.
Integrates with pytest configuration and supports easy a11y directory customization.
"""
from __future__ import annotations

import hashlib
import os
from collections.abc import Callable
from pathlib import Path

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from src.pytest_axe_a11y.assertions import assert_no_axe_violations
from src.pytest_axe_a11y.reporting.html_report import generate_a11y_report
from src.pytest_axe_a11y.reporting.json_report import write_a11y_json_report
from src.pytest_axe_a11y.types import A11YRunResults, AxeResults, AxeRunnerProtocol
from src.pytest_axe_a11y.visual.axe_overlay import capture_all_violations_individually


# ============================================================================
# Pytest hooks and configuration
# ============================================================================

def pytest_addoption(parser: pytest.Parser) -> None:
    """
    Register CLI options for the a11y plugin.
    
    Adds the following options:
        --a11y: Enable accessibility checks
        --a11y-dir: Directory to save reports (default: .a11y)
    
    Can also be configured via:
        - pytest.ini: [pytest] a11y_reports = /path/to/reports
        - conftest.py: config.option.a11y_reports = Path("/path/to/reports")
    
    Args:
        parser: pytest argument parser
    """
    group = parser.getgroup("a11y", "Accessibility testing options")
    
    group.addoption(
        "--a11y",
        action="store_true",
        default=False,
        help="Run axe-core accessibility checks (and generate reports).",
    )
    
    group.addoption(
        "--a11y-dir",
        type=str,
        default=".a11y",
        help="Directory to save a11y reports (default: .a11y)",
    )
    
    # Add INI file option for pytest.ini configuration
    parser.addini(
        "a11y_reports",
        type="string",
        default=".a11y",
        help="Directory to save a11y reports (can also use --a11y-dir CLI option)",
    )


def pytest_configure(config: pytest.Config) -> None:
    """
    Configure pytest with a11y plugin settings.
    
    Called after command line options are parsed.
    Sets up the a11y directory if accessibility testing is enabled.
    
    Configuration priority (highest to lowest):
        1. conftest.py: config.option.a11y_reports = Path(...)
        2. CLI: --a11y-dir /path/to/reports
        3. pytest.ini: a11y_reports = /path/to/reports
        4. Environment: A11Y_DIR=/path/to/reports
        5. Default: .a11y
    
    Args:
        config: pytest configuration object
    """
    # Store a11y settings in config for access in fixtures
    config.a11y_enabled = config.getoption("--a11y")  # type: ignore[attr-defined]
    
    # Resolve a11y directory with priority order
    a11y_dir = _resolve_a11y_dir(config)
    config.a11y_dir = a11y_dir  # type: ignore[attr-defined]
    
    # Create directory if it doesn't exist
    if config.a11y_enabled:  # type: ignore[attr-defined]
        config.a11y_dir.mkdir(parents=True, exist_ok=True)  # type: ignore[attr-defined]


# ============================================================================
# Utility functions
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


def _resolve_a11y_dir(config: pytest.Config) -> Path:
    """
    Resolve a11y reports directory from all configuration sources.
    
    Checks multiple configuration sources in priority order:
        1. conftest.py: config.option.a11y_reports (if set programmatically)
        2. CLI: --a11y-dir /path/to/reports
        3. pytest.ini: a11y_reports = /path/to/reports
        4. Environment: A11Y_DIR=/path/to/reports
        5. Default: .a11y
    
    Args:
        config: pytest configuration object
    
    Returns:
        Resolved Path object for the a11y reports directory
    """
    # Priority 1: Check if config.option.a11y_reports was set programmatically
    if hasattr(config.option, "a11y_reports") and config.option.a11y_reports:  # type: ignore[attr-defined]
        return Path(config.option.a11y_reports)  # type: ignore[attr-defined]
    
    # Priority 2: Check CLI --a11y-dir (only if not default)
    cli_dir = config.getoption("--a11y-dir")  # type: ignore[union-attr]
    if cli_dir and cli_dir != ".a11y":  # type: ignore[comparison-overlap]
        return Path(cli_dir)
    
    # Priority 3: Check pytest.ini a11y_reports setting
    ini_dir = config.getini("a11y_reports")  # type: ignore[union-attr]
    if ini_dir and ini_dir != ".a11y":  # type: ignore[comparison-overlap]
        return Path(ini_dir)
    
    # Priority 4: Check environment variable
    env_dir = os.environ.get("A11Y_DIR")
    if env_dir:
        return Path(env_dir)
    
    # Priority 5: Return default
    return Path(".a11y_reports")


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
    
    Configuration:
        - Use --a11y flag to enable checks
        - Use --a11y-dir <path> to specify report directory (default: .a11y)
        - Or set A11Y_DIR environment variable
    
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
        
    Example:
        >>> def test_homepage_a11y(check_a11y):
        ...     results = check_a11y()
        ...     # Reports auto-generated in .a11y directory
    """
    # Check if a11y testing is enabled
    enabled: bool = bool(request.config.getoption("--a11y"))  # type: ignore[union-attr]
    if not enabled:
        def _skipped() -> A11YRunResults:
            pytest.skip("Accessibility checks not enabled (use --a11y)")
            raise RuntimeError("unreachable")  # for type checkers
        return _skipped

    # Resolve output directory (uses config settings from pytest_configure)
    a11y_dir = request.config.a11y_dir  # type: ignore[attr-defined]

    # Generate xdist-safe filenames
    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "master")
    nodeid = request.node.nodeid
    name = _safe_slug(request.node.name)
    h = _nodeid_hash(nodeid)

    base = f"{name}__{worker_id}__{h}"
    html_path = a11y_dir / f"{base}.html"
    json_path = a11y_dir / f"{base}.json"
    screenshot_dir = a11y_dir / "violation_screenshots"

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
            screenshot_dir=screenshot_dir,
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
            "html_report": str(html_path),
            "json_report": str(json_path),
            "screenshot_dir": str(screenshot_dir),
        }

    return _run