"""
Enhanced pytest configuration for CI/CD reliability.

Integrates with existing setup while adding:
  - Screenshot capture on test failure (debugging)
  - CI environment detection (GitHub Actions, GitLab CI)
  - Test markers for categorization (ci_critical, slow, flaky)
  - Explicit timeout configuration
  - Better error messages in CI logs
"""

from collections.abc import Generator
from datetime import datetime
import logging
import os
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

from sel_py_template.utils.logger_util import LoggerFactory
from sel_py_template.utils.report_plugin import ReportPlugin

date_str: str = datetime.now().strftime("%m-%d-%Y")
LOG_PATH: str = os.path.join(os.getcwd(), "logs", date_str)
REPORT_DIR: str = os.path.join(LOG_PATH, "reports")
A11Y_DIR: str = os.path.join(LOG_PATH, "a11y_reports")
SCREENSHOTS_DIR: str = os.path.join(LOG_PATH, "screenshots")

LoggerFactory.set_log_dir(LOG_PATH)
LoggerFactory.set_report_dir(REPORT_DIR)
LoggerFactory.set_a11y_dir(A11Y_DIR)
logger: logging.Logger = logging.getLogger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def add_stream_handler(
    logger: logging.Logger,
    level: int = logging.INFO,
    stream=sys.stdout,
    fmt: str | None = None,
) -> None:
    """
    Add a StreamHandler to logger if one doesn't already exist for that stream.

    Args:
        logger: Logger instance to add handler to
        level: Logging level (default: INFO)
        stream: Stream to write to (default: stdout)
        fmt: Log message format string (default: standard format)
    """
    # Avoid adding duplicates pointing to the same stream
    for h in logger.handlers:
        if (
            isinstance(h, logging.StreamHandler)
            and getattr(h, "stream", None) is stream
        ):
            return

    handler: logging.StreamHandler = logging.StreamHandler(stream)
    handler.setLevel(level)
    fmt = fmt or "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    handler.setFormatter(logging.Formatter(fmt))
    logger.addHandler(handler)


def _is_ci_environment() -> bool:
    """
    Detect if tests are running in CI environment.

    **Type hints explanation**:
      - -> bool means function returns a bool value
      - os.getenv() returns str | None (string or nothing)
      - == "true" converts that to a boolean check

    Returns:
        True if running in CI (GitHub Actions, GitLab CI, generic CI)
    """
    return (
        os.getenv("GITHUB_ACTIONS") == "true"
        or os.getenv("GITLAB_CI") == "true"
        or os.getenv("CI") == "true"
    )


# ============================================================================
# PYTEST CONFIGURATION HOOKS
# ============================================================================


def pytest_configure(config: pytest.Config) -> None:
    """
    Configure pytest at session start.

    This hook runs once per test session, before any tests run.
    Used to:
      - Create output directories
      - Register plugins
      - Register custom markers
      - Configure logging

    Args:
        config: Pytest config object (manages command-line options, plugins, etc.)
    """
    # Create output directories
    os.makedirs(LOG_PATH, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)
    os.makedirs(A11Y_DIR, exist_ok=True)
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    # Determine browser for plugin registration
    browser: str = config.getoption("--browser") or "generic"
    if config.getoption("--all-browsers"):
        browser = "multi-browser"

    # Register report plugin
    plugin: ReportPlugin = ReportPlugin(
        logs_dir=LOG_PATH, browser=browser, config=config
    )
    config.pluginmanager.register(plugin, name=f"test_plugin_{browser}")

    # Register custom markers for test categorization
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

    # Configure logging
    add_stream_handler(logging.getLogger(), level=logging.INFO, stream=sys.stdout)

    # Configure pytest-html-plus screenshots
    final_report_json_report_path: str = os.path.join(REPORT_DIR, "final_report.json")

    if not hasattr(config, "option"):
        logger.warning(
            "config.option not available - pytest-html-plus configuration skipped. "
            "This may indicate pytest-html-plus plugin is not installed or not loaded."
        )
    else:
        # Set pytest-html-plus output folders
        # Put HTML output in a subfolder so the JSON report isn't copied onto itself
        config.option.html_output = os.path.join(REPORT_DIR, "html")
        # Use the dedicated screenshots folder under logs (not the reports folder)
        config.option.screenshots = SCREENSHOTS_DIR
        config.option.a11y_reports = A11Y_DIR
        config.option.json_report = final_report_json_report_path

    # Configure session logger
    sess_logger: logging.Logger | None = getattr(config, "_logger", None)
    if sess_logger:
        sess_logger.propagate = True
    else:
        logger.debug("config._logger not available")

    logger.info(f"Pytest configured. Logs: {LOG_PATH}")
    logger.info(f"CI environment detected: {_is_ci_environment()}")


def pytest_addoption(parser: pytest.Parser) -> None:
    """
    Add custom command-line options for test execution.

    Allows users to control browser choice, headless mode, etc. via command line.
    Example: pytest tests/ --all-browsers --headless -v

    Args:
        parser: Pytest command-line parser
    """
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
        "report_title", "Default report title", default="Sauce demo tests report"
    )
    parser.addoption(
        "--report-title",
        action="store",
        default=None,
        help="Custom report title (overrides pytest.ini)",
    )


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """
    Parametrize tests based on command-line options.

    If a test has a `browser_name` fixture, this hook will:
      - Run on all 3 browsers if --all-browsers is set
      - Run on single browser if --browser is set

    **Type hints**:
      - metafunc: pytest.Metafunc provides test parametrization
      - if "browser_name" in metafunc.fixturenames: checks if test needs this fixture
      - metafunc.parametrize(): runs test multiple times with different values

    Args:
        metafunc: Pytest metafunc object (used for dynamic parametrization)

    Example:
        @pytest.mark.parametrize("browser_name", ["chrome", "firefox", "edge"])
        def test_something(browser_name): ...
    """
    if "browser_name" in metafunc.fixturenames:
        if metafunc.config.getoption("--all-browsers"):
            # Run on all browsers
            browsers: list[str] = ["chrome", "firefox", "edge"]
            metafunc.parametrize("browser_name", browsers, scope="function")
        else:
            # Run on single specified browser
            browser: str = metafunc.config.getoption("--browser")
            metafunc.parametrize("browser_name", [browser], scope="function")


# def pytest_runtest_makereport(
#     item: pytest.Item, call: pytest.CallInfo
# ) -> None | pytest.TestReport:
#     """
#     Hook: Called after each test phase (setup, call, teardown).

#     Used to capture metadata about test execution. We use this to:
#       - Detect test failures
#       - Attach failure info so screenshot fixture can find it
#       - Track test outcomes

#     **Advanced concept**: Hooks let pytest plugins/tests integrate into pytest's lifecycle.

#     Args:
#         item: Test item being run (pytest.Item contains test metadata)
#         call: Result of the test phase (pytest.CallInfo has outcome, duration, etc.)
#     """
#     # Initialize attribute if not present
#     if not hasattr(item, "rep_call"):
#         item.rep_call = None

#     # Store the call info for the actual test execution phase
#     # (not setup or teardown)
#     if call.when == "call":
#         item.rep_call = call


# ============================================================================
# PYTEST FIXTURES (Reusable setup/teardown for tests)
# ============================================================================


@pytest.fixture(scope="function")
def driver(
    browser_name: str, request: pytest.FixtureRequest, logger: logging.Logger
) -> Generator[WebDriver, None, None]:
    """
    Launch the requested browser and yield the WebDriver instance.

    **Scope: function** (new driver per test - safest for CI isolation)

    **Type hints**:
      - Generator[WebDriver, None, None]:
        - Yields: WebDriver instance
        - Receives: None (no values sent back to test)
        - Returns: None (no final value after cleanup)
      - browser_name: str from pytest_generate_tests parametrization
      - request: pytest.FixtureRequest gives access to config options
      - logger: logging.Logger fixture from get_logger()

    **How it works**:
      1. Setup: Configure browser options, create WebDriver
      2. yield: Pause here, run the test
      3. Cleanup: Always runs (even if test fails), closes browser

    Args:
        browser_name: Name of the browser to launch (chrome, firefox, or edge)
        request: Pytest request object to access config options
        logger: Logger instance for logging browser events

    Yields:
        WebDriver: Selenium WebDriver instance for the specified browser

    Raises:
        ValueError: If an unsupported browser name is provided
    """
    # Detect if running in CI to apply optimizations
    is_ci: bool = _is_ci_environment()

    # Determine if headless mode should be used
    # --interactive flag takes precedence over --headless
    headless: bool = not request.config.getoption("--interactive")

    mode: str = "headless" if headless else "interactive"
    env_info: str = " (CI environment)" if is_ci else " (local)"
    logger.info(f"Starting {browser_name} browser session in {mode} mode{env_info}")

    driver_instance: WebDriver

    if browser_name == "chrome":
        chrome_options: ChromeOptions = ChromeOptions()
        chrome_options.add_argument("--start-maximized")

        if headless:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1400,900")

        # Common optimizations for all environments
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

        # CI-specific optimizations: faster execution
        if is_ci:
            # Disable images to speed up test execution
            chrome_options.add_argument("--blink-settings=imagesEnabled=false")
            logger.debug("CI mode: Disabled images for faster execution")

        driver_instance = webdriver.Chrome(
            service=ChromeService(), options=chrome_options
        )

    elif browser_name == "firefox":
        firefox_options: FirefoxOptions = FirefoxOptions()
        if headless:
            firefox_options.add_argument("--headless")
        firefox_options.add_argument("--width=1400")
        firefox_options.add_argument("--height=900")

        # CI-specific: disable images
        if is_ci:
            firefox_options.set_preference("permissions.default.image", 2)
            logger.debug("CI mode: Disabled images for faster execution")

        driver_instance = webdriver.Firefox(
            service=FirefoxService(), options=firefox_options
        )

    elif browser_name == "edge":
        edge_options: EdgeOptions = EdgeOptions()
        if headless:
            edge_options.add_argument("--headless=new")
            edge_options.add_argument("--disable-gpu")
            edge_options.add_argument("--window-size=1400,900")
        edge_options.add_argument("--start-maximized")

        # CI-specific: disable images
        if is_ci:
            edge_options.add_argument("--blink-settings=imagesEnabled=false")
            logger.debug("CI mode: Disabled images for faster execution")

        driver_instance = webdriver.Edge(service=EdgeService(), options=edge_options)

    else:
        raise ValueError(f"Unsupported browser: {browser_name}")

    # Configure timeouts (critical for CI reliability)
    driver_instance.implicitly_wait(10)  # Implicit wait for element finding
    driver_instance.set_page_load_timeout(30)  # Page load timeout
    driver_instance.set_script_timeout(30)  # JavaScript execution timeout

    try:
        yield driver_instance
    finally:
        # Cleanup: always runs, even if test fails
        logger.info(f"Closing {browser_name.title()} browser session")
        try:
            driver_instance.quit()
        except Exception as e:
            # Log but don't raise - cleanup failures shouldn't fail the test
            logger.warning(f"Error closing browser: {e}")


@pytest.fixture(scope="function", autouse=True)
def _capture_screenshot_on_failure(
    request: pytest.FixtureRequest, driver: WebDriver
) -> Generator[None, None, None]:
    """
    Fixture: Automatically capture a screenshot if a test fails.

    **Scope: function** (per test)
    **autouse: True** (automatically applied to all tests)

    **Type hints**:
      - request: pytest.FixtureRequest gives access to test metadata
      - driver: WebDriver injected from driver fixture
      - Generator[None, None, None]: yields nothing, just runs side effect

    **How it works**:
      1. yield pauses here (before test runs)
      2. Test runs
      3. After test, resumes and captures screenshot if failed

    **Why separate from driver fixture**:
      - Single Responsibility Principle: driver = setup/teardown
      - This fixture = side effects (screenshots)
      - Easier to disable if needed: @pytest.mark.no_screenshot

    Args:
        request: Pytest request object to check if test failed
        driver: WebDriver to capture screenshot with

    Yields:
        None (side effect only)
    """
    yield

    # After test completes, check if it failed
    # Check for stored call info that has an exception
    if hasattr(request.node, "rep_call"):
        call_info: pytest.CallInfo = request.node.rep_call
        # Test failed if call has exception info
        if call_info is not None and call_info.excinfo is not None:
            try:
                # Generate filename: test_name_FAILED.png
                test_name: str = request.node.name
                screenshot_filename: str = f"{test_name}_FAILED.png"
                screenshot_path: str = os.path.join(
                    SCREENSHOTS_DIR, screenshot_filename
                )

                # Capture screenshot
                driver.save_screenshot(screenshot_path)
                logger.info(f"📸 Screenshot saved: {screenshot_path}")

            except Exception as e:
                # Don't fail the test if screenshot fails
                logger.warning(f"⚠️  Failed to capture screenshot: {e}")


@pytest.fixture(scope="function")
def get_logger() -> logging.Logger:
    """
    Provide a logger instance for tests.

    **Scope: function** (new logger per test)

    **Type hints**:
      - -> logging.Logger means returns a Logger instance

    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(f"app.{__name__}")


@pytest.fixture(scope="session")
def log_path() -> str:
    """
    Return the current log directory path.

    **Scope: session** (same logger path for entire test run)

    Returns:
        str: Path to the logs directory for this test session
    """
    return LOG_PATH
