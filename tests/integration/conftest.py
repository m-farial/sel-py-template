from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
import re

from _pytest.tmpdir import rmtree, tmppath_result_key
import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from sel_py_template.pages.base_page import BasePage


@pytest.fixture(autouse=True)
def _skip_a11y_tests_when_flag_missing(request: pytest.FixtureRequest) -> None:
    if request.node.get_closest_marker("a11y") and not getattr(
        request.config.option, "a11y", False
    ):
        pytest.skip("skipping a11y tests without --a11y")


# ============================================================================
# LOGGER STUB
# ============================================================================


@pytest.fixture(autouse=True)
def stub_logger_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Stub out LoggerFactory for every test so real log files are never written
    during the test suite.

    This fixture is ``autouse=True``, meaning pytest applies it automatically
    to every test in the project without needing to declare it explicitly.
    ``monkeypatch`` is a built-in pytest fixture that temporarily replaces an
    object during a test and restores the original afterward.

    The ``try/except ImportError`` guard means the stub is quietly skipped if
    the framework package is not installed (e.g. in a stripped-down CI job).
    """
    try:
        import sel_py_template.pages.base_page as base_page_module
    except ImportError:
        return

    class _Logger:
        def debug(self, *args: object, **kwargs: object) -> None:
            pass

        def info(self, *args: object, **kwargs: object) -> None:
            pass

        def warning(self, *args: object, **kwargs: object) -> None:
            pass

        def error(self, *args: object, **kwargs: object) -> None:
            pass

    class _LoggerFactory:
        @staticmethod
        def get_logger(*args: object, **kwargs: object) -> _Logger:
            return _Logger()

        @staticmethod
        def get_log_dir() -> None:
            return None

    monkeypatch.setattr(base_page_module, "LoggerFactory", _LoggerFactory, raising=True)


# ============================================================================
# BROWSER NAME
# ============================================================================


@pytest.fixture()
def browser_name(driver: WebDriver) -> str:
    """
    Return the lowercase browser name for the active WebDriver session.

    Rather than hardcoding ``"chrome"`` in every test, we read the name
    directly from the driver's capabilities dict at runtime.  This means
    the value is always correct even when running with ``--browser firefox``
    or ``--all-browsers``.

    ``capabilities`` is a dictionary that Selenium populates after the browser
    session is created.  The ``"browserName"`` key is part of the W3C
    WebDriver standard and is present for Chrome, Firefox, and Edge.

    Args:
        driver: The active Selenium WebDriver instance (provided by the
                existing ``driver`` fixture in your framework).

    Returns:
        Lowercase browser name, e.g. ``"chrome"``, ``"firefox"``, ``"msedge"``.
    """
    return driver.capabilities["browserName"].lower()


# ============================================================================
# RESILIENT PAGE FACTORY
# ============================================================================


@pytest.fixture()
def resilient_page(driver: WebDriver, browser_name: str) -> BasePage:
    """
    Return a ``BasePage`` instance wired to the active driver and browser.

    This fixture replaces the repeated boilerplate that appeared in every
    resilience test::

        page = ResilientPage(driver, browser="chrome")

    Because ``browser_name`` is resolved at runtime (see above), the page
    object is always constructed with the correct browser string regardless
    of which browser the test suite is running against.

    The return type is annotated as ``BasePage`` here because ``conftest.py``
    does not import ``ResilientPage`` (that class lives in the resilience test
    file itself).  Pytest still resolves the concrete subclass at runtime, so
    all ``ResilientPage``-specific attributes are accessible on the returned
    object.  If you prefer stricter typing you can import ``ResilientPage``
    directly and change the return annotation.

    Usage in a test::

        def test_something(resilient_page: BasePage, tmp_path: Path) -> None:
            url = write_html(tmp_path, "page.html", SOME_HTML)
            resilient_page.navigate(url)
            resilient_page.button.click()

    Args:
        driver: The active Selenium WebDriver instance.
        browser_name: Lowercase browser name resolved by the ``browser_name``
                      fixture above.

    Returns:
        A ``BasePage`` (or subclass) instance ready for navigation.
    """
    # Import is deferred to keep conftest lightweight and avoid a hard
    # dependency on the resilience test module at collection time.
    from tests.integration.test_framework_resilience import ResilientPage

    return ResilientPage(driver, browser=browser_name)


@pytest.fixture(scope="function")
def tmp_path(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
) -> Generator[Path, None, None]:
    """
    Return a temporary directory named after the full test node name.

    This overrides pytest's default ``tmp_path`` naming so the directory
    remains human-readable and is not truncated to 30 characters.
    """
    name = re.sub(r"[\W]", "_", request.node.name)
    path = tmp_path_factory.mktemp(name, numbered=True)
    yield path

    policy = tmp_path_factory._retention_policy
    result_dict = request.node.stash[tmppath_result_key]

    if policy == "failed" and result_dict.get("call", True):
        rmtree(path, ignore_errors=True)
