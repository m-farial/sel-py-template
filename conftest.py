"""
Enhanced pytest configuration for CI/CD reliability.

Integrates with existing setup while adding:
  - Screenshot capture on test failure (debugging)
  - CI environment detection (GitHub Actions, GitLab CI)
  - Test markers for categorization (ci_critical, slow, flaky)
  - Explicit timeout configuration
  - Better error messages in CI logs

TEMPLATE OWNERS NOTE:
  This file is template-owned. Downstream users should NOT modify it.
  To customise report titles, artifact directories, and ini options,
  edit pytest.ini in your project root instead.
"""

from __future__ import annotations

from collections.abc import Generator
import logging
from pathlib import Path
import sys

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.remote.webdriver import WebDriver

from sel_py_template.utils.artifact_manager import ArtifactConfig, ArtifactManager
from sel_py_template.utils.logger_util import LoggerFactory
from sel_py_template.utils.report_plugin import ReportPlugin

logger: logging.Logger = logging.getLogger(__name__)


def add_stream_handler(
    logger: logging.Logger,
    level: int = logging.INFO,
    stream=sys.stdout,
    fmt: str | None = None,
) -> None:
    """
    Add a StreamHandler to logger if one doesn't already exist for that stream.

    Args:
        logger: Logger instance to add handler to.
        level: Logging level.
        stream: Stream to write to.
        fmt: Log message format string.
    """
    for handler in logger.handlers:
        if (
            isinstance(handler, logging.StreamHandler)
            and getattr(handler, "stream", None) is stream
        ):
            return

    stream_handler = logging.StreamHandler(stream)
    stream_handler.setLevel(level)
    fmt = fmt or "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    stream_handler.setFormatter(logging.Formatter(fmt))
    logger.addHandler(stream_handler)


def _is_ci_environment() -> bool:
    """Detect whether tests are running in a CI environment."""
    import os

    return (
        os.getenv("GITHUB_ACTIONS") == "true"
        or os.getenv("GITLAB_CI") == "true"
        or os.getenv("CI") == "true"
    )


def _build_artifact_manager(config: pytest.Config, browser: str) -> ArtifactManager:
    """Create the artifact manager for the current pytest session.

    Args:
        config: Pytest configuration object.
        browser: Browser label used for naming run artifacts.

    Returns:
        Configured artifact manager with directories created.
    """
    artifact_config = ArtifactConfig(
        base_dir=Path(config.getoption("--artifacts-dir")),
        extra_artifacts=_resolve_extra_artifacts(config),
    )
    artifact_manager = ArtifactManager(
        artifact_config,
        browser=browser,
        a11y_enabled=bool(getattr(config.option, "a11y", False)),
    )
    artifact_manager.create_directories()
    return artifact_manager


def _parse_extra_artifact(value: str) -> tuple[str, str]:
    """Parse a NAME=PATH extra artifact definition."""
    if "=" not in value:
        raise pytest.UsageError(
            f"Invalid --extra-artifact value: {value!r}. Expected NAME=PATH."
        )

    name, raw_path = value.split("=", 1)
    name = name.strip()
    raw_path = raw_path.strip()

    if not name:
        raise pytest.UsageError("Extra artifact name cannot be empty.")
    if not raw_path:
        raise pytest.UsageError("Extra artifact path cannot be empty.")

    return name, raw_path


def _parse_extra_artifacts_from_ini(config: pytest.Config) -> dict[str, str]:
    """Parse extra artifact definitions from pytest.ini."""
    raw_values = config.getini("extra_artifacts")
    extra_artifacts: dict[str, str] = {}

    for raw_value in raw_values:
        name, path = _parse_extra_artifact(raw_value)
        extra_artifacts[name] = path

    return extra_artifacts


def _parse_extra_artifacts_from_cli(config: pytest.Config) -> dict[str, str]:
    """Parse repeatable --extra-artifact values from the command line."""
    raw_values = config.getoption("--extra-artifact") or []
    extra_artifacts: dict[str, str] = {}

    for raw_value in raw_values:
        name, path = _parse_extra_artifact(raw_value)
        extra_artifacts[name] = path

    return extra_artifacts


def _resolve_extra_artifacts(config: pytest.Config) -> dict[str, str]:
    """Merge ini and CLI extra artifact definitions, with CLI taking precedence."""
    ini_artifacts = _parse_extra_artifacts_from_ini(config)
    cli_artifacts = _parse_extra_artifacts_from_cli(config)
    return {**ini_artifacts, **cli_artifacts}


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest at session start."""
    browser: str = config.getoption("--browser") or "generic"
    if config.getoption("--all-browsers"):
        browser = "multi-browser"

    artifact_manager = _build_artifact_manager(config, browser)
    config._artifact_manager = artifact_manager  # type: ignore[attr-defined]

    # Resolved final a11y session directory for this run
    config.a11y_session_dir = artifact_manager.paths.a11y_dir  # type: ignore[attr-defined]

    LoggerFactory.set_browser(browser)
    LoggerFactory.set_log_dir(artifact_manager.paths.run_root)
    LoggerFactory.set_report_dir(artifact_manager.paths.pytest_html_dir)
    LoggerFactory.set_a11y_dir(artifact_manager.paths.a11y_dir)
    LoggerFactory.set_failure_screenshots_dir(
        artifact_manager.paths.failure_screenshots_dir
    )

    plugin = ReportPlugin(
        artifact_manager=artifact_manager,
        browser=browser,
        config=config,
    )
    config.pluginmanager.register(plugin, name=f"test_plugin_{browser}")

    config.addinivalue_line(
        "markers",
        "ci_critical: tests that must pass in CI (failures block deployment)",
    )
    config.addinivalue_line(
        "markers",
        "slow: tests that take >5 seconds (run separately in CI)",
    )
    config.addinivalue_line(
        "markers",
        "flaky: tests that may fail intermittently (require investigation)",
    )

    add_stream_handler(logging.getLogger(), level=logging.INFO, stream=sys.stdout)

    if not hasattr(config, "option"):
        logger.warning(
            "config.option not available - pytest-html-plus / pytest-a11y configuration skipped. "
            "This may indicate a plugin is not installed or not loaded."
        )
    else:
        config.option.html_output = str(artifact_manager.paths.pytest_html_dir)
        config.option.screenshots = str(artifact_manager.paths.failure_screenshots_dir)

    session_logger: logging.Logger | None = getattr(config, "_logger", None)
    if session_logger:
        session_logger.propagate = False
    else:
        logger.debug("config._logger not available")

    logger.info("Pytest configured. Run root: %s", artifact_manager.paths.run_root)
    logger.info("A11y session dir: %s", config.a11y_session_dir)


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom command-line options for test execution."""
    parser.addoption(
        "--browser",
        action="store",
        default="chrome",
        choices=["chrome", "firefox", "edge"],
        help="Browser to use for testing (default: chrome)",
    )
    parser.addoption(
        "--all-browsers",
        action="store_true",
        default=False,
        help="Run tests on all browsers (chrome, firefox, edge)",
    )
    parser.addoption(
        "--headless",
        action="store_true",
        default=True,
        help="Run browsers in headless mode (default: True)",
    )
    parser.addoption(
        "--interactive",
        action="store_true",
        default=False,
        help="Run browsers in interactive mode (visible browser window)",
    )
    parser.addini(
        "report_title",
        "Title shown in the HTML test report. Override this in your pytest.ini.",
        default="Test Report",  # generic default — downstream projects set this in pytest.ini
    )
    parser.addoption(
        "--report-title",
        action="store",
        default=None,
        help="Custom report title (overrides pytest.ini report_title)",
    )
    parser.addoption(
        "--artifacts-dir",
        action="store",
        default="artifacts",
        help="Base directory for all test artifacts.",
    )
    parser.addoption(
        "--extra-artifact",
        action="append",
        default=[],
        metavar="NAME=PATH",
        help=(
            "Register an additional artifact directory. "
            "May be passed multiple times. Example: --extra-artifact downloads=downloads"
        ),
    )
    parser.addini(
        "extra_artifacts",
        type="linelist",
        help="Additional artifact directories in NAME=PATH format.",
        default=[],
    )


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Parametrize tests based on browser-related command-line options."""
    if "browser_name" in metafunc.fixturenames:
        if metafunc.config.getoption("--all-browsers"):
            browsers: list[str] = ["chrome", "firefox", "edge"]
            metafunc.parametrize("browser_name", browsers, scope="function")
        else:
            browser: str = metafunc.config.getoption("--browser")
            metafunc.parametrize("browser_name", [browser], scope="function")


@pytest.fixture(scope="function")
def driver(
    browser_name: str,
    request: pytest.FixtureRequest,
    logger: logging.Logger,
) -> Generator[WebDriver, None, None]:
    """Launch the requested browser and yield the WebDriver instance."""
    is_ci: bool = _is_ci_environment()
    headless: bool = not request.config.getoption("--interactive")

    mode: str = "headless" if headless else "interactive"
    env_info: str = " (CI environment)" if is_ci else " (local)"
    logger.info(
        "Starting %s browser session in %s mode%s", browser_name, mode, env_info
    )

    driver_instance: WebDriver

    if browser_name == "chrome":
        chrome_options: ChromeOptions = ChromeOptions()
        chrome_options.add_argument("--start-maximized")

        if headless:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1400,900")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

        if is_ci:
            chrome_options.add_argument("--blink-settings=imagesEnabled=false")
            logger.debug("CI mode: Disabled images for faster execution")

        driver_instance = webdriver.Chrome(
            service=ChromeService(),
            options=chrome_options,
        )

    elif browser_name == "firefox":
        firefox_options: FirefoxOptions = FirefoxOptions()
        if headless:
            firefox_options.add_argument("--headless")
        firefox_options.add_argument("--width=1400")
        firefox_options.add_argument("--height=900")

        if is_ci:
            firefox_options.set_preference("permissions.default.image", 2)
            logger.debug("CI mode: Disabled images for faster execution")

        driver_instance = webdriver.Firefox(
            service=FirefoxService(),
            options=firefox_options,
        )

    elif browser_name == "edge":
        edge_options: EdgeOptions = EdgeOptions()
        if headless:
            edge_options.add_argument("--headless=new")
            edge_options.add_argument("--disable-gpu")
            edge_options.add_argument("--window-size=1400,900")
        edge_options.add_argument("--start-maximized")

        if is_ci:
            edge_options.add_argument("--blink-settings=imagesEnabled=false")
            logger.debug("CI mode: Disabled images for faster execution")

        driver_instance = webdriver.Edge(service=EdgeService(), options=edge_options)

    else:
        raise ValueError(f"Unsupported browser: {browser_name}")

    driver_instance.implicitly_wait(10)
    driver_instance.set_page_load_timeout(30)
    driver_instance.set_script_timeout(30)

    try:
        yield driver_instance
    finally:
        logger.info("Closing %s browser session", browser_name.title())
        try:
            driver_instance.quit()
        except Exception as error:
            logger.warning("Error closing browser: %s", error)


@pytest.fixture(scope="function", autouse=True)
def _capture_screenshot_on_failure(
    request: pytest.FixtureRequest,
    driver: WebDriver,
) -> Generator[None, None, None]:
    """Capture a screenshot after a test fails when report call info is available."""
    yield

    if hasattr(request.node, "rep_call"):
        call_info: pytest.CallInfo[object] | None = request.node.rep_call
        if call_info is not None and call_info.excinfo is not None:
            try:
                artifact_manager: ArtifactManager = request.config._artifact_manager  # type: ignore[attr-defined]
                screenshot_path = artifact_manager.failure_screenshot_path(
                    request.node.name,
                    "FAILED",
                )
                driver.save_screenshot(str(screenshot_path))
                logger.info("📸 Screenshot saved: %s", screenshot_path)
            except Exception as error:
                logger.warning("⚠️  Failed to capture screenshot: %s", error)


@pytest.fixture(scope="function")
def get_logger(request: pytest.FixtureRequest) -> logging.Logger:
    """Provide a browser-scoped logger for tests."""
    session_logger: logging.Logger = request.config._logger  # type: ignore[attr-defined]
    return session_logger.getChild("tests")


@pytest.fixture(scope="session")
def log_path(pytestconfig: pytest.Config) -> str:
    """Return the run root path for the current pytest session."""
    artifact_manager: ArtifactManager = pytestconfig._artifact_manager  # type: ignore[attr-defined]
    return str(artifact_manager.paths.run_root)
