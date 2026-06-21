# tests/unit/conftest.py
from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock

import pytest
from selenium.common.exceptions import (
    NoAlertPresentException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from sel_py_template.pages.base_page import BasePage

# ---------------------------------------------------------------------------
# Patch path constants
# ---------------------------------------------------------------------------
_BASE_PAGE_MODULE = "sel_py_template.pages.base_page"
_LOGGER_PATCH = "sel_py_template.pages.base_page.LoggerFactory"

Locator = tuple[str, str]

LOCATOR: Locator = (By.ID, "my-element")
DEFAULT_TIMEOUT: int = 2
BASE_TIMEOUT: int = 5

# ---------------------------------------------------------------------------
# Helper classes/fixtures
# ---------------------------------------------------------------------------


@dataclass
class FakeWebElement:
    """Small fake WebElement that satisfies expected_conditions + BasePage usage."""

    text: str = "Hello"
    displayed: bool = True
    enabled: bool = True
    selected: bool = False
    tag_name: str = "div"

    def is_displayed(self) -> bool:
        return self.displayed

    def is_enabled(self) -> bool:
        return self.enabled

    def is_selected(self) -> bool:
        return self.selected

    def clear(self) -> None:
        self.text = ""

    def send_keys(self, value: str) -> None:
        self.text += value

    def get_attribute(self, name: str) -> str | None:
        return f"attr-{name}"


class FakeSwitchTo:
    """Imitates driver.switch_to.* for alert/frame APIs."""

    def __init__(self) -> None:
        self._alert: Any | None = None
        self.frame = MagicMock()
        self.default_content = MagicMock()

    @property
    def alert(self) -> Any:
        if self._alert is None:
            raise NoAlertPresentException()
        return self._alert


class FakeWebDriver:
    """Minimal fake WebDriver supporting BasePage + expected_conditions."""

    def __init__(self) -> None:
        self.current_url: str = "https://example.com"
        self.title: str = "Example"
        self._elements: dict[Locator, FakeWebElement] = {}
        self.switch_to: FakeSwitchTo = FakeSwitchTo()

        # standard webdriver methods used by BasePage
        self.get = MagicMock()
        self.refresh = MagicMock()
        self.execute_script = MagicMock(return_value="executed")
        self.save_screenshot = MagicMock(return_value=True)

    def find_element(self, by: str, value: str) -> FakeWebElement:
        key: Locator = (by, value)
        if key not in self._elements:
            raise NoSuchElementException(f"{key} not found")
        return self._elements[key]


class DummyWebDriverWait:
    """
    WebDriverWait substitute:
    - Calls the EC/callback once
    - Raises TimeoutException if result is falsy
    """

    def __init__(
        self,
        driver: Any,
        timeout: int,
        poll_frequency: float | None = None,
        ignored_exceptions: tuple[type[Exception], ...] | None = None,
    ) -> None:
        self.driver = driver
        self.timeout = timeout

    def until(self, method: Callable[[Any], Any], message: str = "") -> Any:
        result = method(self.driver)
        if not result:
            raise TimeoutException(message or "Condition not met")
        return result

    def until_not(self, method: Callable[[Any], Any], message: str = "") -> bool:
        result = method(self.driver)
        if result:
            raise TimeoutException(message or "Condition still true")
        return True


# ===========================================================================
# FIXTURES
# ===========================================================================


@pytest.fixture(autouse=True)
def _patch_wait_and_logger(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Globally patch waits + logger for unit tests (fast + no IO)."""
    # patch WebDriverWait in the module under test
    monkeypatch.setattr(
        f"{_BASE_PAGE_MODULE}.WebDriverWait", DummyWebDriverWait, raising=True
    )

    # patch LoggerFactory.get_logger to return a MagicMock logger
    logger_factory = MagicMock()
    logger_factory.get_logger.return_value = MagicMock()
    monkeypatch.setattr(_LOGGER_PATCH, logger_factory, raising=True)

    yield


@pytest.fixture()
def driver() -> FakeWebDriver:
    return FakeWebDriver()


@pytest.fixture()
def web_element() -> MagicMock:
    """Return a MagicMock that mimics a Selenium WebElement."""
    web_element = MagicMock(spec=WebElement)
    web_element.is_selected.return_value = True
    web_element.is_enabled.return_value = True
    web_element.is_displayed.return_value = True
    return web_element


@pytest.fixture()
def mock_page() -> MagicMock:
    """
    Return a MagicMock page.
    """
    page = MagicMock(spec=BasePage)
    page.logger = MagicMock()
    page.driver = MagicMock()

    page.wait_for.return_value = MagicMock()
    page.get_text.return_value = ""
    page.get_attribute.return_value = None
    page.wait_for_element_to_disappear.return_value = True
    page.is_displayed.return_value = True
    return page


@pytest.fixture()
def mock_base_page(driver: MagicMock) -> BasePage:
    """
    Return a MagicMock that mimics BasePage.

    All methods return sensible defaults so tests only need to override
    what they care about.
    """
    return BasePage(driver=driver, browser="chrome", timeout=BASE_TIMEOUT)


@pytest.fixture()
def page_spy(mock_base_page: BasePage) -> BasePage:
    for name in dir(mock_base_page):
        if name.startswith("_"):
            continue

        attr = getattr(mock_base_page, name)

        if callable(attr):
            setattr(mock_base_page, name, MagicMock(wraps=attr))

    return mock_base_page
