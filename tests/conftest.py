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

from src.utils.report_plugin import ReportPlugin

date_folder = datetime.now().strftime("%m-%d-%Y")
LOG_PATH1 = os.path.join("logs", date_folder)
LOG_PATH = os.path.join(os.getcwd(), "logs", date_folder)
logger = logging.getLogger(__name__)


def add_stream_handler(
    logger: logging.Logger,
    level: int = logging.INFO,
    stream=sys.stdout,
    fmt: str | None = None,
) -> None:
    """Add a StreamHandler writing to `stream` if one doesn't already exist."""
    # avoid adding duplicates pointing to the same stream
    for h in logger.handlers:
        if (
            isinstance(h, logging.StreamHandler)
            and getattr(h, "stream", None) is stream
        ):
            return

    handler = logging.StreamHandler(stream)
    handler.setLevel(level)
    fmt = fmt or "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    handler.setFormatter(logging.Formatter(fmt))
    logger.addHandler(handler)


def pytest_configure(config):
    """Register ReportPlugin only after pytest-html is available."""
    os.makedirs(LOG_PATH, exist_ok=True)

    # Determine browser for plugin registration
    browser: str = config.getoption("--browser") or "generic"
    if config.getoption("--all-browsers"):
        browser = "multi-browser"
    # Register report plugin
    plugin: ReportPlugin = ReportPlugin(
        logs_dir=LOG_PATH, browser=browser, config=config
    )
    config.pluginmanager.register(plugin, name=f"test_plugin_{browser}")
    # Configure logging
    add_stream_handler(logging.getLogger(), level=logging.INFO, stream=sys.stdout)
    # Configure pytest-html report location
    report_file: str = os.path.join(LOG_PATH, "report.html")
    config.option.htmlpath = report_file
    # Configure pytest-html-plus (if available)
    screenshots_dir: str = os.path.join(LOG_PATH, "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)

    if not hasattr(config, "option"):
        logger.warning(
            "config.option not available - pytest-html-plus configuration skipped. "
            "This may indicate pytest-html-plus plugin is not installed or not loaded."
        )
    else:
        # Set pytest-html-plus output folder so it writes assets/json into the same date folder
        # pytest-html-plus registers the CLI option as "--html-output" with dest `html_output`
        config.option.html_output = LOG_PATH
        config.option.screenshots = screenshots_dir
        logger.info("pytest-html-plus screenshots directory: %s", screenshots_dir)
    # Configure session logger
    sess_logger: logging.Logger | None = getattr(config, "_logger", None)
    if sess_logger:
        sess_logger.propagate = True
    else:
        logger.debug("config._logger not available")


def pytest_addoption(parser: pytest.Parser) -> None:
    """
    Add custom command-line options for browser selection.

    Args:
        parser: Pytest command-line option parser
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


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """
    Parametrize browser_name fixture based on command-line options.

    If --all-browsers is set, tests will run on all three browsers.
    Otherwise, tests run on the single browser specified by --browser.

    Args:
        metafunc: Pytest metafunc object for test parametrization
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


@pytest.fixture(scope="function")
def driver(
    browser_name: str, request: pytest.FixtureRequest, logger: logging.Logger
) -> Generator[WebDriver, None, None]:
    """
    Launch the requested browser and yield the WebDriver instance.

    Args:
        browser_name: Name of the browser to launch (chrome, firefox, or edge)
        request: Pytest request object to access config options
        logger: Logger instance for logging browser events

    Yields:
        WebDriver: Selenium WebDriver instance for the specified browser

    Raises:
        ValueError: If an unsupported browser name is provided
    """
    # Determine if headless mode should be used
    # --interactive flag takes precedence over --headless
    headless: bool = not request.config.getoption("--interactive")

    mode: str = "headless" if headless else "interactive"
    logger.info(f"Starting {browser_name} browser session in {mode} mode")

    driver_instance: WebDriver

    if browser_name == "chrome":
        chrome_options: ChromeOptions = ChromeOptions()
        chrome_options.add_argument("--start-maximized")
        if headless:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
        driver_instance = webdriver.Chrome(
            service=ChromeService(), options=chrome_options
        )

    elif browser_name == "firefox":
        firefox_options: FirefoxOptions = FirefoxOptions()
        if headless:
            firefox_options.add_argument("--headless")
        firefox_options.add_argument("--width=1920")
        firefox_options.add_argument("--height=1080")
        driver_instance = webdriver.Firefox(
            service=FirefoxService(), options=firefox_options
        )

    elif browser_name == "edge":
        edge_options: EdgeOptions = EdgeOptions()
        if headless:
            edge_options.add_argument("--headless=new")
            edge_options.add_argument("--disable-gpu")
        edge_options.add_argument("--start-maximized")
        driver_instance = webdriver.Edge(service=EdgeService(), options=edge_options)

    else:
        raise ValueError(f"Unsupported browser: {browser_name}")

    # Set implicit wait for all browsers
    driver_instance.implicitly_wait(10)

    yield driver_instance

    logger.info(f"Closing {browser_name.title()} browser session")
    driver_instance.quit()


@pytest.fixture(scope="function")
def get_logger() -> logging.Logger:
    """
    Provide a logger instance for tests.

    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(f"app.{__name__}")


@pytest.fixture(scope="session")
def log_path() -> str:
    """
    Return the current log directory path.

    Returns:
        str: Path to the logs directory for this test session
    """
    return LOG_PATH
