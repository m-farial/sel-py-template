# tests/unit/ui/test_elements.py
from __future__ import annotations

import dataclasses
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from tests.unit.conftest import DEFAULT_TIMEOUT, LOCATOR

_MODULE = "sel_py_template.ui.elements"

with patch("sel_py_template.pages.base_page.LoggerFactory"):
    from sel_py_template.ui.elements import (
        BoundElement,
        Element,
        ElementType,
        UIElementDef,
    )


def make_defn(
    element_type: ElementType = ElementType.BUTTON,
    locator: tuple[str, str] = LOCATOR,
    name: str = "my-button",
    timeout_s: int = DEFAULT_TIMEOUT,
) -> UIElementDef:
    """Create a UIElementDef with sensible defaults."""
    return UIElementDef(
        element_type=element_type, locator=locator, name=name, timeout_s=timeout_s
    )


@pytest.fixture()
def bound(page_spy: Any) -> BoundElement:
    """BoundElement using a real page with wrapped methods for delegation assertions."""
    return BoundElement(page=page_spy, definition=make_defn())


@pytest.fixture()
def bound_mock(mock_page: MagicMock) -> BoundElement:
    return BoundElement(page=mock_page, definition=make_defn())


# ===========================================================================
# ElementType
# ===========================================================================


class TestElementType:
    @pytest.mark.parametrize(
        "member, expected_value",
        [
            (ElementType.BUTTON, "button"),
            (ElementType.TEXT_INPUT, "text_input"),
            (ElementType.DROPDOWN, "dropdown"),
            (ElementType.CHECKBOX, "checkbox"),
            (ElementType.RADIO, "radio"),
            (ElementType.TOGGLE, "toggle"),
        ],
    )
    def test_enum_values(self, member: ElementType, expected_value: str) -> None:
        assert member.value == expected_value

    def test_is_str_subclass(self) -> None:
        assert isinstance(ElementType.BUTTON, str)


# ===========================================================================
# UIElementDef
# ===========================================================================


class TestUIElementDef:
    def test_stores_fields(self) -> None:
        defn = make_defn()
        assert defn.element_type == ElementType.BUTTON
        assert defn.locator == LOCATOR
        assert defn.name == "my-button"
        assert defn.timeout_s == DEFAULT_TIMEOUT

    def test_is_frozen(self) -> None:
        defn = make_defn()
        with pytest.raises(dataclasses.FrozenInstanceError):
            defn.name = "changed"  # type: ignore[misc]


# ===========================================================================
# BoundElement — state / locating
# ===========================================================================


class TestBoundElementState:
    def test_find_delegates_to_page_wait_for(
        self, bound_mock: BoundElement, mock_page: MagicMock
    ) -> None:
        result = bound_mock.find()
        mock_page.wait_for.assert_called_once_with(LOCATOR, timeout=DEFAULT_TIMEOUT)
        assert result is mock_page.wait_for.return_value

    def test_is_visible_delegates_to_page_is_displayed(
        self, bound_mock: BoundElement, mock_page: MagicMock
    ) -> None:
        assert bound_mock.is_visible(timeout=7) is True
        mock_page.is_displayed.assert_called_once_with(LOCATOR, timeout=7)

    def test_find_uses_custom_timeout(
        self,
        bound_mock: BoundElement,
        mock_page: MagicMock,
        web_element: MagicMock,
    ) -> None:
        mock_page.wait_for.return_value = web_element
        bound_mock.find(timeout=3)
        mock_page.wait_for.assert_called_once_with(LOCATOR, timeout=3)

    def test_is_enabled_returns_true_when_element_enabled(
        self,
        bound_mock: BoundElement,
        mock_page: MagicMock,
        web_element: MagicMock,
    ) -> None:
        mock_page.wait_for.return_value = web_element
        assert bound_mock.is_enabled() is True

    def test_is_enabled_returns_false_when_element_disabled(
        self,
        bound_mock: BoundElement,
        mock_page: MagicMock,
        web_element: MagicMock,
    ) -> None:
        mock_page.wait_for.return_value = web_element
        web_element.is_enabled.return_value = False
        assert bound_mock.is_enabled() is False

    def test_enabled_delegates_to_is_enabled(self, bound_mock: BoundElement) -> None:
        with patch.object(
            bound_mock, "is_enabled", return_value=True
        ) as mock_is_enabled:
            assert bound_mock.enabled() is True
            mock_is_enabled.assert_called_once()

    def test_disabled_is_inverse_of_is_enabled(self, bound_mock: BoundElement) -> None:
        with patch.object(bound_mock, "is_enabled", return_value=True):
            assert bound_mock.disabled() is False
        with patch.object(bound_mock, "is_enabled", return_value=False):
            assert bound_mock.disabled() is True


# ===========================================================================
# BoundElement — interactions
# ===========================================================================


class TestBoundElementInteractions:
    def test_scroll_into_view_calls_page_scroll_to(
        self, bound_mock: BoundElement, mock_page: MagicMock
    ) -> None:

        result = bound_mock.scroll_into_view()
        assert isinstance(mock_page, MagicMock)
        mock_page.scroll_to.assert_called_once_with(LOCATOR)
        # scroll_into_view returns self for chaining
        assert result is bound_mock

    def test_click_delegates_to_page_click(
        self, bound_mock: BoundElement, mock_page: MagicMock
    ) -> None:
        bound_mock.click()
        mock_page.click.assert_called_once_with(LOCATOR, timeout=DEFAULT_TIMEOUT)

    def test_click_uses_custom_timeout(
        self, bound_mock: BoundElement, mock_page: MagicMock
    ) -> None:
        bound_mock.click(timeout=3)
        mock_page.click.assert_called_once_with(LOCATOR, timeout=3)

    def test_click_retry_succeeds_on_first_attempt(
        self, bound_mock: BoundElement, mock_page: MagicMock
    ) -> None:
        bound_mock.click_retry()
        assert mock_page.click.call_count == 1

    @pytest.mark.parametrize(
        "exception_cls",
        [ElementClickInterceptedException, StaleElementReferenceException],
    )
    def test_click_retry_retries_once_on_interception(
        self,
        bound_mock: BoundElement,
        mock_page: MagicMock,
        exception_cls: type[Exception],
    ) -> None:
        # First call raises, second succeeds
        mock_page.click.side_effect = [exception_cls(), None]
        bound_mock.click_retry()
        assert mock_page.click.call_count == 2

    def test_hover_moves_to_element(
        self,
        mock_page: MagicMock,
        web_element: MagicMock,
    ) -> None:
        bound = BoundElement(page=mock_page, definition=make_defn())
        mock_page.wait_for.return_value = web_element
        with patch(f"{_MODULE}.ActionChains") as mock_ac_cls:
            mock_ac = mock_ac_cls.return_value
            mock_ac.move_to_element.return_value = mock_ac
            bound.hover()
            mock_ac.move_to_element.assert_called_once_with(web_element)
            mock_ac.perform.assert_called_once()

    def test_wait_until_gone_delegates_to_page(
        self, bound_mock: BoundElement, mock_page: MagicMock
    ) -> None:
        bound_mock.wait_until_gone()
        mock_page.wait_for_element_to_disappear.assert_called_once_with(
            LOCATOR, timeout=DEFAULT_TIMEOUT
        )

    def test_wait_until_gone_uses_custom_timeout(
        self, bound_mock: BoundElement, mock_page: MagicMock
    ) -> None:
        bound_mock.wait_until_gone(timeout=3)
        mock_page.wait_for_element_to_disappear.assert_called_once_with(
            LOCATOR, timeout=3
        )


# ===========================================================================
# BoundElement — content
# ===========================================================================


class TestBoundElementContent:
    def test_text_delegates_to_page_get_text(
        self, bound_mock: BoundElement, mock_page: MagicMock
    ) -> None:
        mock_page.get_text.return_value = "Hello World"
        assert bound_mock.text() == "Hello World"
        mock_page.get_text.assert_called_once_with(LOCATOR)

    def test_value_returns_attribute_value(
        self, bound_mock: BoundElement, mock_page: MagicMock
    ) -> None:
        mock_page.get_attribute.return_value = "my-value"
        assert bound_mock.value() == "my-value"
        mock_page.get_attribute.assert_called_once_with(LOCATOR, "value")

    def test_value_returns_empty_string_when_attribute_is_none(
        self, bound_mock: BoundElement, mock_page: MagicMock
    ) -> None:
        mock_page.get_attribute.return_value = None
        assert bound_mock.value() == ""

    def test_attr_returns_attribute_value(
        self, bound_mock: BoundElement, mock_page: MagicMock
    ) -> None:
        mock_page.get_attribute.return_value = "btn-primary"
        assert bound_mock.attr("class") == "btn-primary"
        mock_page.get_attribute.assert_called_once_with(LOCATOR, "class")

    def test_attr_returns_empty_string_when_attribute_is_none(
        self, bound_mock: BoundElement, mock_page: MagicMock
    ) -> None:
        mock_page.get_attribute.return_value = None
        assert bound_mock.attr("data-missing") == ""


# ===========================================================================
# BoundElement — keyboard
# ===========================================================================


class TestBoundElementKeyboard:
    def test_clear_calls_element_clear(
        self,
        mock_page: MagicMock,
        web_element: MagicMock,
    ) -> None:
        bound_mock = BoundElement(page=mock_page, definition=make_defn())
        mock_page.wait_for.return_value = web_element
        bound_mock.clear()
        web_element.clear.assert_called_once()

    @pytest.mark.parametrize(
        "element_type",
        [ElementType.TEXT_INPUT, ElementType.TEXTAREA],
    )
    def test_type_sends_keys_for_valid_types(
        self,
        mock_page: MagicMock,
        element_type: ElementType,
    ) -> None:
        bound_mock = BoundElement(
            page=mock_page, definition=make_defn(element_type=element_type)
        )
        bound_mock.type("hello")
        mock_page.send_keys.assert_called_once_with(
            LOCATOR, "hello", timeout=DEFAULT_TIMEOUT, clear_first=True
        )

    def test_type_raises_type_error_for_non_input_elements(
        self, mock_page: MagicMock
    ) -> None:
        bound_mock = BoundElement(
            page=mock_page, definition=make_defn(element_type=ElementType.BUTTON)
        )
        with pytest.raises(TypeError, match="type\\(\\) not supported"):
            bound_mock.type("hello")

    def test_type_respects_clear_first_false(self, mock_page: MagicMock) -> None:
        bound_mock = BoundElement(
            page=mock_page,
            definition=make_defn(element_type=ElementType.TEXT_INPUT),
        )
        bound_mock.type("hello", clear_first=False)
        mock_page.send_keys.assert_called_once_with(
            LOCATOR, "hello", timeout=DEFAULT_TIMEOUT, clear_first=False
        )

    @pytest.mark.parametrize(
        "method_name, expected_key",
        [
            ("press_enter", Keys.ENTER),
            ("press_escape", Keys.ESCAPE),
            ("press_tab", Keys.TAB),
        ],
    )
    def test_press_keys_send_correct_key(
        self,
        bound_mock: BoundElement,
        mock_page: MagicMock,
        method_name: str,
        expected_key: str,
    ) -> None:
        mock_page.send_keys = MagicMock()
        getattr(bound_mock, method_name)()

        mock_page.send_keys.assert_called_once_with(
            LOCATOR, expected_key, timeout=DEFAULT_TIMEOUT, clear_first=False
        )


# ===========================================================================
# BoundElement — checkables
# ===========================================================================


class TestBoundElementCheckables:
    @pytest.mark.parametrize(
        "element_type",
        [ElementType.CHECKBOX, ElementType.RADIO, ElementType.TOGGLE],
    )
    def test_is_checked_returns_true_when_selected(
        self,
        mock_page: MagicMock,
        web_element: MagicMock,
        element_type: ElementType,
    ) -> None:
        bound_mock = BoundElement(
            page=mock_page, definition=make_defn(element_type=element_type)
        )
        mock_page.wait_for.return_value = web_element
        assert bound_mock.is_checked() is True

    @pytest.mark.parametrize(
        "element_type",
        [ElementType.BUTTON, ElementType.LINK, ElementType.TEXT_INPUT],
    )
    def test_is_checked_raises_type_error_for_unsupported_types(
        self, mock_page: MagicMock, element_type: ElementType
    ) -> None:
        bound_mock = BoundElement(
            page=mock_page, definition=make_defn(element_type=element_type)
        )
        with pytest.raises(TypeError, match="is_checked\\(\\) not supported"):
            bound_mock.is_checked()

    @pytest.mark.parametrize(
        "element_type",
        [ElementType.CHECKBOX, ElementType.TOGGLE],
    )
    def test_set_checked_clicks_when_state_differs(
        self,
        mock_page: MagicMock,
        web_element: MagicMock,
        element_type: ElementType,
    ) -> None:
        bound_mock = BoundElement(
            page=mock_page, definition=make_defn(element_type=element_type)
        )
        mock_page.wait_for.return_value = web_element
        web_element.is_selected.return_value = False  # currently unchecked
        bound_mock.set_checked(True)  # want checked → should click
        mock_page.click.assert_called()

    @pytest.mark.parametrize(
        "element_type",
        [ElementType.CHECKBOX, ElementType.TOGGLE],
    )
    def test_set_checked_does_not_click_when_state_matches(
        self,
        mock_page: MagicMock,
        web_element: MagicMock,
        element_type: ElementType,
    ) -> None:
        bound_mock = BoundElement(
            page=mock_page, definition=make_defn(element_type=element_type)
        )
        mock_page.wait_for.return_value = web_element
        bound_mock.set_checked(True)  # want checked → no click needed
        mock_page.click.assert_not_called()

    def test_set_checked_raises_type_error_for_unsupported_type(
        self, mock_page: MagicMock
    ) -> None:
        bound_mock = BoundElement(
            page=mock_page, definition=make_defn(element_type=ElementType.RADIO)
        )
        with pytest.raises(TypeError, match="set_checked\\(\\) not supported"):
            bound_mock.set_checked(True)

    def test_select_radio_clicks_when_not_checked(
        self,
        mock_page: MagicMock,
        web_element: MagicMock,
    ) -> None:
        bound_mock = BoundElement(
            page=mock_page, definition=make_defn(element_type=ElementType.RADIO)
        )
        mock_page.wait_for.return_value = web_element
        web_element.is_selected.return_value = False
        bound_mock.select_radio()
        mock_page.click.assert_called()

    def test_select_radio_does_not_click_when_already_selected(
        self,
        mock_page: MagicMock,
        web_element: MagicMock,
    ) -> None:
        bound_mock = BoundElement(
            page=mock_page, definition=make_defn(element_type=ElementType.RADIO)
        )
        mock_page.wait_for.return_value = web_element
        bound_mock.select_radio()
        mock_page.click.assert_not_called()

    def test_select_radio_raises_type_error_for_non_radio(
        self, mock_page: MagicMock
    ) -> None:
        bound_mock = BoundElement(
            page=mock_page, definition=make_defn(element_type=ElementType.CHECKBOX)
        )
        with pytest.raises(TypeError, match="select_radio\\(\\) only supports RADIO"):
            bound_mock.select_radio()


# ===========================================================================
# BoundElement — dropdown
# ===========================================================================


class TestBoundElementDropdown:
    def _make_dropdown(self, mock_page: MagicMock) -> BoundElement:
        return BoundElement(
            page=mock_page, definition=make_defn(element_type=ElementType.DROPDOWN)
        )

    def test_select_option_raises_type_error_for_non_dropdown(
        self, mock_page: MagicMock
    ) -> None:
        bound_mock = BoundElement(
            page=mock_page, definition=make_defn(element_type=ElementType.BUTTON)
        )
        with pytest.raises(
            TypeError, match="select_option\\(\\) only supports DROPDOWN"
        ):
            bound_mock.select_option(value="x")

    def test_select_option_by_value_uses_select_class(
        self,
        mock_page: MagicMock,
        web_element: MagicMock,
    ) -> None:
        web_element.tag_name = "select"
        mock_page.wait_for.return_value = web_element
        bound_mock = self._make_dropdown(mock_page)

        with patch(f"{_MODULE}.Select") as mock_select_cls:
            mock_sel = mock_select_cls.return_value
            bound_mock.select_option(value="opt1")
            mock_select_cls.assert_called_once_with(web_element)
            mock_sel.select_by_value.assert_called_once_with("opt1")

    def test_select_option_by_text_uses_select_class(
        self,
        mock_page: MagicMock,
        web_element: MagicMock,
    ) -> None:
        web_element.tag_name = "select"
        mock_page.wait_for.return_value = web_element
        bound_mock = self._make_dropdown(mock_page)

        with patch(f"{_MODULE}.Select") as mock_select_cls:
            mock_sel = mock_select_cls.return_value
            bound_mock.select_option(text="Option One")
            mock_sel.select_by_visible_text.assert_called_once_with("Option One")

    def test_select_option_raises_value_error_when_neither_given(
        self,
        mock_page: MagicMock,
        web_element: MagicMock,
    ) -> None:
        web_element.tag_name = "select"
        mock_page.wait_for.return_value = web_element
        bound_mock = self._make_dropdown(mock_page)

        with patch(f"{_MODULE}.Select"):
            with pytest.raises(ValueError, match="Provide value= or text="):
                bound_mock.select_option()

    def test_select_option_clicks_for_custom_dropdown(
        self,
        mock_page: MagicMock,
        web_element: MagicMock,
    ) -> None:
        web_element.tag_name = "div"  # not a <select>
        mock_page.wait_for.return_value = web_element
        bound_mock = self._make_dropdown(mock_page)
        bound_mock.select_option(value="irrelevant")
        mock_page.click.assert_called()


# ===========================================================================
# BoundElement — should assertions
# ===========================================================================


class TestBoundElementShouldAssertions:
    def test_should_be_visible_returns_self_when_visible(
        self, bound_mock: BoundElement, mock_page: MagicMock
    ) -> None:
        assert bound_mock.should_be_visible() is bound_mock

    def test_should_be_visible_raises_assertion_error_when_hidden(
        self, bound_mock: BoundElement, mock_page: MagicMock
    ) -> None:
        mock_page.is_displayed.return_value = False
        with pytest.raises(AssertionError, match="expected visible"):
            bound_mock.should_be_visible()

    def test_should_be_hidden_returns_self_when_hidden(
        self, bound_mock: BoundElement, mock_page: MagicMock
    ) -> None:
        mock_page.is_displayed.return_value = False
        assert bound_mock.should_be_hidden() is bound_mock

    def test_should_be_hidden_raises_assertion_error_when_visible(
        self, bound_mock: BoundElement, mock_page: MagicMock
    ) -> None:

        with pytest.raises(AssertionError, match="expected hidden"):
            bound_mock.should_be_hidden()

    def test_should_be_enabled_returns_self_when_enabled(
        self,
        bound_mock: BoundElement,
        mock_page: MagicMock,
        web_element: MagicMock,
    ) -> None:
        mock_page.wait_for.return_value = web_element
        assert bound_mock.should_be_enabled() is bound_mock

    def test_should_be_enabled_raises_assertion_error_when_disabled(
        self,
        bound_mock: BoundElement,
        mock_page: MagicMock,
        web_element: MagicMock,
    ) -> None:
        mock_page.wait_for.return_value = web_element
        web_element.is_enabled.return_value = False
        with pytest.raises(AssertionError, match="expected enabled"):
            bound_mock.should_be_enabled()

    def test_should_be_disabled_returns_self_when_disabled(
        self,
        bound_mock: BoundElement,
        mock_page: MagicMock,
        web_element: MagicMock,
    ) -> None:
        mock_page.wait_for.return_value = web_element
        web_element.is_enabled.return_value = False
        assert bound_mock.should_be_disabled() is bound_mock

    def test_should_be_disabled_raises_assertion_error_when_enabled(
        self,
        bound_mock: BoundElement,
        mock_page: MagicMock,
        web_element: MagicMock,
    ) -> None:
        mock_page.wait_for.return_value = web_element
        with pytest.raises(AssertionError, match="expected disabled"):
            bound_mock.should_be_disabled()

    @pytest.mark.parametrize(
        "actual, expected, should_pass",
        [
            ("Hello World", "Hello", True),  # substring match
            ("Hello World", "missing", False),
        ],
    )
    def test_should_contain_text(
        self,
        bound_mock: BoundElement,
        mock_page: MagicMock,
        actual: str,
        expected: str,
        should_pass: bool,
    ) -> None:
        mock_page.get_text.return_value = actual
        if should_pass:
            assert bound_mock.should_contain_text(expected) is bound_mock
        else:
            with pytest.raises(AssertionError, match="expected text to contain"):
                bound_mock.should_contain_text(expected)

    @pytest.mark.parametrize(
        "actual, expected, should_pass",
        [
            ("Exact", "Exact", True),
            ("Exact", "Different", False),
        ],
    )
    def test_should_equal_text(
        self,
        bound_mock: BoundElement,
        mock_page: MagicMock,
        actual: str,
        expected: str,
        should_pass: bool,
    ) -> None:
        mock_page.get_text.return_value = actual
        if should_pass:
            assert bound_mock.should_equal_text(expected) is bound_mock
        else:
            with pytest.raises(AssertionError, match="expected text"):
                bound_mock.should_equal_text(expected)

    @pytest.mark.parametrize(
        "actual, expected, should_pass",
        [
            ("correct-value", "correct-value", True),
            ("wrong-value", "correct-value", False),
        ],
    )
    def test_should_have_value(
        self,
        bound_mock: BoundElement,
        mock_page: MagicMock,
        actual: str,
        expected: str,
        should_pass: bool,
    ) -> None:
        mock_page.get_attribute.return_value = actual
        if should_pass:
            assert bound_mock.should_have_value(expected) is bound_mock
        else:
            with pytest.raises(AssertionError, match="expected value"):
                bound_mock.should_have_value(expected)

    @pytest.mark.parametrize(
        "actual, expected, should_pass",
        [
            ("primary", "primary", True),
            ("secondary", "primary", False),
        ],
    )
    def test_should_have_attr(
        self,
        bound_mock: BoundElement,
        mock_page: MagicMock,
        actual: str,
        expected: str,
        should_pass: bool,
    ) -> None:
        mock_page.get_attribute.return_value = actual
        if should_pass:
            assert bound_mock.should_have_attr("class", expected) is bound_mock
        else:
            with pytest.raises(AssertionError, match="expected attr"):
                bound_mock.should_have_attr("class", expected)


# ===========================================================================
# Element descriptor
# ===========================================================================


class TestElementDescriptor:
    """
    Tests for the Element descriptor class.

    A descriptor is a class that implements __get__ / __set_name__ to control
    how attribute access works on another class. Here, Element is used as a
    class-level attribute on a Page class, and accessing it on an instance
    returns a BoundElement.
    """

    def _make_page_class(self, **element_kwargs: Any) -> type:
        """
        Dynamically creates a fake page class with one Element descriptor.

        Using type() here avoids polluting the test module's namespace and
        ensures __set_name__ is called correctly (as it would be in real usage).
        """
        return type(
            "fake_page",
            (object,),
            {
                "submit_btn": Element(
                    "submit",
                    ElementType.BUTTON,
                    **element_kwargs,
                )
            },
        )

    def test_set_name_stores_attribute_name(self) -> None:
        fake_page = self._make_page_class()
        assert fake_page.submit_btn._attr_name == "submit_btn"  # type: ignore[union-attr]

    def test_class_access_returns_element_itself(self) -> None:
        fake_page = self._make_page_class()
        result = fake_page.submit_btn
        assert isinstance(result, Element)

    def test_instance_access_returns_bound_element(self, mock_page: MagicMock) -> None:
        fake_page = self._make_page_class()
        # Attach the descriptor's __get__ to mock_page by injecting into its class
        descriptor = fake_page.__dict__["submit_btn"]
        result = descriptor.__get__(mock_page, type(mock_page))
        assert isinstance(result, BoundElement)

    def test_bound_element_is_cached_on_second_access(
        self, mock_page: MagicMock
    ) -> None:
        fake_page = self._make_page_class()
        descriptor = fake_page.__dict__["submit_btn"]
        first = descriptor.__get__(mock_page, type(mock_page))
        second = descriptor.__get__(mock_page, type(mock_page))
        assert first is second
        assert isinstance(first, BoundElement)

    def test_bound_element_uses_attr_name_as_fallback_name(
        self, mock_page: MagicMock
    ) -> None:
        """When name= is not provided, defn.name should fall back to the attribute name."""
        fake_page = self._make_page_class()  # no name= kwarg
        descriptor = fake_page.__dict__["submit_btn"]
        bound_mock = descriptor.__get__(mock_page, type(mock_page))
        assert bound_mock.defn.name == "submit_btn"

    def test_bound_element_uses_explicit_name_when_provided(
        self, mock_page: MagicMock
    ) -> None:
        fake_page = self._make_page_class(name="Submit Button")
        descriptor = fake_page.__dict__["submit_btn"]
        bound_mock = descriptor.__get__(mock_page, type(mock_page))
        assert bound_mock.defn.name == "Submit Button"

    def test_bound_element_locator_uses_by_and_value(
        self, mock_page: MagicMock
    ) -> None:
        fake_page = self._make_page_class(by=By.CSS_SELECTOR)
        descriptor = fake_page.__dict__["submit_btn"]
        bound_mock = descriptor.__get__(mock_page, type(mock_page))
        assert bound_mock.defn.locator == (By.CSS_SELECTOR, "submit")

    def test_bound_element_uses_custom_timeout(self, mock_page: MagicMock) -> None:
        fake_page = self._make_page_class(timeout_s=30)
        descriptor = fake_page.__dict__["submit_btn"]
        bound_mock = descriptor.__get__(mock_page, type(mock_page))
        assert bound_mock.defn.timeout_s == 30

    def test_instance_access_returns_cached_bound_element(
        self,
        mock_page: MagicMock,
    ) -> None:
        fake_page = self._make_page_class()
        descriptor = fake_page.__dict__["submit_btn"]

        cached = BoundElement(
            page=mock_page,
            definition=make_defn(name="cached"),
        )
        mock_page.__dict__["__bound_el_submit_btn"] = cached

        result = descriptor.__get__(mock_page, type(mock_page))

        assert result is cached

    def test_instance_access_rebuilds_when_cached_value_is_not_bound_element(
        self,
        mock_page: MagicMock,
    ) -> None:
        fake_page = self._make_page_class(timeout_s=DEFAULT_TIMEOUT)
        descriptor = fake_page.__dict__["submit_btn"]

        # Simulate bad/stale cache value
        mock_page.__dict__["__bound_el_submit_btn"] = "not-a-bound-element"

        result = descriptor.__get__(mock_page, type(mock_page))

        assert isinstance(result, BoundElement)
        assert result.defn.element_type == ElementType.BUTTON
        assert result.defn.locator == (By.ID, "submit")
        assert result.defn.name == "submit_btn"
        assert result.defn.timeout_s == DEFAULT_TIMEOUT

        # Confirm the bad cache was replaced with the new BoundElement
        assert mock_page.__dict__["__bound_el_submit_btn"] is result
