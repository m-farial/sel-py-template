from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import cast

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import Select

from ..pages.base_page import BasePage

Locator = tuple[str, str]


class ElementType(str, Enum):
    BUTTON = "button"
    LINK = "link"
    TEXT_INPUT = "text_input"
    TEXTAREA = "textarea"
    DROPDOWN = "dropdown"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    TOGGLE = "toggle"
    TAB = "tab"
    MENU_ITEM = "menu_item"
    MODAL = "modal"
    TOAST = "toast"
    PAGINATION = "pagination"


@dataclass(frozen=True)
class UIElementDef:
    element_type: ElementType
    locator: Locator
    name: str
    timeout_s: int = 10


class BoundElement:
    """
    Driver-bound element wrapper that delegates to BasePage primitives.

    Expected BasePage methods used:
      - wait_for(locator, timeout=...)
      - click(locator, timeout=...)
      - send_keys(locator, text, timeout=..., clear_first=...)
      - is_displayed(locator, timeout=...) -> bool
      - get_text(locator) -> str
      - get_attribute(locator, attr) -> str | None
      - scroll_to(locator) -> None
      - wait_for_element_to_disappear(locator, timeout=...) -> None
    """

    def __init__(self, page: BasePage, definition: UIElementDef) -> None:
        self.page = page
        self.defn = definition

    @property
    def locator(self) -> Locator:
        return self.defn.locator

    # ---------- locating / state ----------
    def find(self, timeout: int | None = None) -> WebElement:
        self.page.logger.debug(
            "BoundElement.find name=%s locator=%s timeout=%s",
            self.defn.name,
            self.locator,
            timeout or self.defn.timeout_s,
        )
        return self.page.wait_for(self.locator, timeout=timeout or self.defn.timeout_s)

    def is_visible(self, timeout: int = 5) -> bool:
        self.page.logger.debug(
            "Checking visibility for element name=%s locator=%s timeout=%s",
            self.defn.name,
            self.locator,
            timeout,
        )
        return self.page.is_displayed(self.locator, timeout=timeout)

    def is_enabled(self, timeout: int | None = None) -> bool:
        self.page.logger.debug(
            "Checking enabled state for element name=%s locator=%s timeout=%s",
            self.defn.name,
            self.locator,
            timeout or self.defn.timeout_s,
        )
        return bool(self.find(timeout=timeout).is_enabled())

    def enabled(self, timeout: int | None = None) -> bool:
        return self.is_enabled(timeout=timeout)

    def disabled(self, timeout: int | None = None) -> bool:
        return not self.is_enabled(timeout=timeout)

    # ---------- common interactions ----------
    def scroll_into_view(self) -> BoundElement:
        self.page.logger.debug(
            "Scrolling element into view name=%s locator=%s",
            self.defn.name,
            self.locator,
        )
        self.page.scroll_to(self.locator)
        return self

    def click(self, timeout: int | None = None) -> None:
        self.page.logger.debug(
            "Click requested for element name=%s locator=%s timeout=%s",
            self.defn.name,
            self.locator,
            timeout or self.defn.timeout_s,
        )
        self.page.click(self.locator, timeout=timeout or self.defn.timeout_s)

    def click_retry(self, timeout: int | None = None) -> None:
        """
        Scroll + click; if intercepted, scroll again and retry once.
        """
        self.page.logger.debug(
            "Click retry flow started for element name=%s locator=%s timeout=%s",
            self.defn.name,
            self.locator,
            timeout or self.defn.timeout_s,
        )
        try:
            self.scroll_into_view()
            self.page.click(self.locator, timeout=timeout or self.defn.timeout_s)
            self.page.logger.debug(
                "Click retry flow completed without needing retry for element name=%s locator=%s",
                self.defn.name,
                self.locator,
            )
        except (ElementClickInterceptedException, StaleElementReferenceException):
            self.page.logger.warning(
                "Click intercepted or stale for element name=%s locator=%s. Retrying once.",
                self.defn.name,
                self.locator,
            )
            self.scroll_into_view()
            self.page.click(self.locator, timeout=timeout or self.defn.timeout_s)
            self.page.logger.debug(
                "Click retry succeeded for element name=%s locator=%s",
                self.defn.name,
                self.locator,
            )

    def hover(self) -> None:
        self.page.logger.debug(
            "Hover requested for element name=%s locator=%s",
            self.defn.name,
            self.locator,
        )
        self.scroll_into_view()
        el = self.find()
        ActionChains(self.page.driver).move_to_element(el).perform()
        self.page.logger.debug(
            "Hover completed for element name=%s locator=%s",
            self.defn.name,
            self.locator,
        )

    def wait_until_gone(self, timeout: int | None = None) -> None:
        self.page.logger.debug(
            "Waiting for element to disappear name=%s locator=%s timeout=%s",
            self.defn.name,
            self.locator,
            timeout or self.defn.timeout_s,
        )
        self.page.wait_for_element_to_disappear(
            self.locator, timeout=timeout or self.defn.timeout_s
        )

    # ---------- content ----------
    def text(self) -> str:
        self.page.logger.debug(
            "Reading text for element name=%s locator=%s",
            self.defn.name,
            self.locator,
        )
        return self.page.get_text(self.locator)

    def value(self) -> str:
        self.page.logger.debug(
            "Reading value for element name=%s locator=%s",
            self.defn.name,
            self.locator,
        )
        return self.page.get_attribute(self.locator, "value") or ""

    def attr(self, name: str) -> str:
        self.page.logger.debug(
            "Reading attribute name=%s for element defn_name=%s locator=%s",
            name,
            self.defn.name,
            self.locator,
        )
        return self.page.get_attribute(self.locator, name) or ""

    # ---------- typing / keyboard ----------
    def clear(self, timeout: int | None = None) -> None:
        self.page.logger.debug(
            "Clearing element name=%s locator=%s timeout=%s",
            self.defn.name,
            self.locator,
            timeout or self.defn.timeout_s,
        )
        self.find(timeout=timeout).clear()
        self.page.logger.debug(
            "Clear completed for element name=%s locator=%s",
            self.defn.name,
            self.locator,
        )

    def type(
        self, text: str, *, clear_first: bool = True, timeout: int | None = None
    ) -> None:
        self.page.logger.debug(
            "Typing into element name=%s locator=%s clear_first=%s text_length=%s timeout=%s",
            self.defn.name,
            self.locator,
            clear_first,
            len(text),
            timeout or self.defn.timeout_s,
        )
        if self.defn.element_type not in {
            ElementType.TEXT_INPUT,
            ElementType.TEXTAREA,
        }:
            raise TypeError(f"type() not supported for {self.defn.element_type}")
        self.page.send_keys(
            self.locator,
            text,
            timeout=timeout or self.defn.timeout_s,
            clear_first=clear_first,
        )

    def press_enter(self, timeout: int | None = None) -> None:
        self.page.logger.debug(
            "Sending ENTER to element name=%s locator=%s",
            self.defn.name,
            self.locator,
        )
        self.page.send_keys(
            self.locator,
            Keys.ENTER,
            timeout=timeout or self.defn.timeout_s,
            clear_first=False,
        )

    def press_escape(self, timeout: int | None = None) -> None:
        self.page.logger.debug(
            "Sending ESCAPE to element name=%s locator=%s",
            self.defn.name,
            self.locator,
        )
        self.page.send_keys(
            self.locator,
            Keys.ESCAPE,
            timeout=timeout or self.defn.timeout_s,
            clear_first=False,
        )

    def press_tab(self, timeout: int | None = None) -> None:
        self.page.logger.debug(
            "Sending TAB to element name=%s locator=%s",
            self.defn.name,
            self.locator,
        )
        self.page.send_keys(
            self.locator,
            Keys.TAB,
            timeout=timeout or self.defn.timeout_s,
            clear_first=False,
        )

    # ---------- checkables ----------
    def is_checked(self, timeout: int = 5) -> bool:
        self.page.logger.debug(
            "Checking selected state for element name=%s locator=%s timeout=%s",
            self.defn.name,
            self.locator,
            timeout,
        )
        if self.defn.element_type not in {
            ElementType.CHECKBOX,
            ElementType.RADIO,
            ElementType.TOGGLE,
        }:
            raise TypeError(f"is_checked() not supported for {self.defn.element_type}")
        return bool(self.find(timeout=timeout).is_selected())

    def set_checked(self, checked: bool) -> None:
        self.page.logger.debug(
            "Setting checked state for element name=%s locator=%s target_state=%s",
            self.defn.name,
            self.locator,
            checked,
        )
        if self.defn.element_type not in {ElementType.CHECKBOX, ElementType.TOGGLE}:
            raise TypeError(f"set_checked() not supported for {self.defn.element_type}")
        if self.is_checked() != checked:
            self.page.logger.debug(
                "Checkbox/toggle state change required for element name=%s locator=%s",
                self.defn.name,
                self.locator,
            )
            self.click_retry()
        else:
            self.page.logger.debug(
                "Checkbox/toggle already in desired state for element name=%s locator=%s",
                self.defn.name,
                self.locator,
            )

    def select_radio(self) -> None:
        self.page.logger.debug(
            "Selecting radio element name=%s locator=%s",
            self.defn.name,
            self.locator,
        )
        if self.defn.element_type != ElementType.RADIO:
            raise TypeError("select_radio() only supports RADIO")
        if not self.is_checked():
            self.click_retry()
        else:
            self.page.logger.debug(
                "Radio already selected for element name=%s locator=%s",
                self.defn.name,
                self.locator,
            )

    # ---------- dropdown helpers ----------
    def select_option(
        self, *, value: str | None = None, text: str | None = None
    ) -> None:
        self.page.logger.debug(
            "Selecting dropdown option for element name=%s locator=%s value=%r text=%r",
            self.defn.name,
            self.locator,
            value,
            text,
        )
        """
        Native-first dropdown selection:
          - If the element is a <select>, use selenium.support.ui.Select
          - Otherwise treat as a trigger (click to open), and let the test/page define option elements.
        """
        if self.defn.element_type != ElementType.DROPDOWN:
            raise TypeError("select_option() only supports DROPDOWN")

        self.scroll_into_view()
        el = self.find()
        tag = (el.tag_name or "").lower()
        self.page.logger.debug(
            "Dropdown element name=%s locator=%s resolved tag=%s",
            self.defn.name,
            self.locator,
            tag,
        )

        if tag == "select":
            self.page.logger.debug(
                "Using native Select helper for element name=%s locator=%s",
                self.defn.name,
                self.locator,
            )
            sel = Select(el)
            if value is not None:
                sel.select_by_value(value)
            elif text is not None:
                sel.select_by_visible_text(text)
            else:
                raise ValueError("Provide value= or text=")
            return

        # Custom dropdown: open it; option selection is app-specific.
        self.page.logger.debug(
            "Using custom dropdown click flow for element name=%s locator=%s",
            self.defn.name,
            self.locator,
        )
        self.click_retry()

    # ---------- should assertions ----------
    def should_be_visible(self, timeout: int = 5) -> BoundElement:
        if not self.is_visible(timeout=timeout):
            raise AssertionError(
                f"[{self.defn.name}] expected visible but was not. locator={self.locator}"
            )
        return self

    def should_be_hidden(self, timeout: int = 5) -> BoundElement:
        if self.is_visible(timeout=timeout):
            raise AssertionError(
                f"[{self.defn.name}] expected hidden but was visible. locator={self.locator}"
            )
        return self

    def should_be_enabled(self, timeout: int | None = None) -> BoundElement:
        if not self.is_enabled(timeout=timeout):
            raise AssertionError(
                f"[{self.defn.name}] expected enabled but was disabled. locator={self.locator}"
            )
        return self

    def should_be_disabled(self, timeout: int | None = None) -> BoundElement:
        if self.is_enabled(timeout=timeout):
            raise AssertionError(
                f"[{self.defn.name}] expected disabled but was enabled. locator={self.locator}"
            )
        return self

    def should_contain_text(self, expected: str) -> BoundElement:
        actual = self.text()
        if expected not in actual:
            raise AssertionError(
                f"[{self.defn.name}] expected text to contain {expected!r} but got {actual!r}. locator={self.locator}"
            )
        return self

    def should_equal_text(self, expected: str) -> BoundElement:
        actual = self.text()
        if actual != expected:
            raise AssertionError(
                f"[{self.defn.name}] expected text {expected!r} but got {actual!r}. locator={self.locator}"
            )
        return self

    def should_have_value(self, expected: str) -> BoundElement:
        actual = self.value()
        if actual != expected:
            raise AssertionError(
                f"[{self.defn.name}] expected value {expected!r} but got {actual!r}. locator={self.locator}"
            )
        return self

    def should_have_attr(self, name: str, expected: str) -> BoundElement:
        actual = self.attr(name)
        if actual != expected:
            raise AssertionError(
                f"[{self.defn.name}] expected attr {name}={expected!r} but got {actual!r}. locator={self.locator}"
            )
        return self


class Element:
    def __init__(
        self,
        value: str,
        element_type: ElementType,
        *,
        by: str = By.ID,
        name: str | None = None,
        timeout_s: int = 10,
    ):
        self._by = by
        self._value = value
        self._element_type = element_type
        self._name = name
        self._timeout_s = timeout_s
        self._attr_name: str | None = None

    def __set_name__(self, owner: type, name: str) -> None:
        self._attr_name = name

    def __get__(self, instance: BasePage | None, owner: type) -> BoundElement | Element:
        if instance is None:
            return self

        assert self._attr_name is not None
        instance.logger.debug(
            "Resolving bound element attr=%s locator=%s type=%s",
            self._attr_name,
            (self._by, self._value),
            self._element_type,
        )
        cache_name = f"__bound_el_{self._attr_name}"
        cached = instance.__dict__.get(cache_name)
        if cached is not None:
            cached_el = cast(BoundElement | None, cached)
            if isinstance(cached_el, BoundElement):
                instance.logger.debug(
                    "Returning cached bound element attr=%s locator=%s",
                    self._attr_name,
                    (self._by, self._value),
                )
                return cached_el

        definition = UIElementDef(
            element_type=self._element_type,
            locator=(self._by, self._value),
            name=self._name or self._attr_name,
            timeout_s=self._timeout_s,
        )
        instance.logger.debug(
            "Creating new bound element attr=%s locator=%s type=%s timeout=%s",
            self._attr_name,
            (self._by, self._value),
            self._element_type,
            self._timeout_s,
        )
        bound = BoundElement(instance, definition)
        instance.__dict__[cache_name] = bound
        return bound
