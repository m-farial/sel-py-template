# tests/unit/pages/test_base_page.py
from __future__ import annotations

import os
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.alert import Alert
from template_tests.unit.conftest import (
    BASE_TIMEOUT,
    LOCATOR,
    FakeWebDriver,
    FakeWebElement,
)

from sel_py_template.pages.base_page import (
    BasePage,
    ElementInteractionError,
    ElementNotClickableError,
    ElementNotFoundError,
    PageError,
)

_BASE_PAGE_MODULE = "sel_py_template.pages.base_page"

# ===========================================================================
# CUSTOM EXCEPTIONS
# ===========================================================================


class TestCustomExceptions:
    def test_page_error_is_exception(self) -> None:
        assert issubclass(PageError, Exception)

    def test_element_not_found_error_is_page_error(self) -> None:
        assert issubclass(ElementNotFoundError, PageError)

    def test_element_not_clickable_error_is_page_error(self) -> None:
        assert issubclass(ElementNotClickableError, PageError)

    def test_element_interaction_error_is_page_error(self) -> None:
        assert issubclass(ElementInteractionError, PageError)


# ===========================================================================
# __init__
# ===========================================================================


class TestInit:
    def test_driver_is_stored(
        self, mock_base_page: BasePage, driver: FakeWebDriver
    ) -> None:
        assert mock_base_page.driver is driver

    def test_timeout_is_stored(self, mock_base_page: BasePage) -> None:
        assert mock_base_page.timeout == BASE_TIMEOUT

    def test_logger_is_created(self, driver: FakeWebDriver) -> None:
        # LoggerFactory already patched in conftest; verify call.
        with patch(f"{_BASE_PAGE_MODULE}.LoggerFactory") as mock_factory:
            mock_factory.get_logger.return_value = MagicMock()
            BasePage(driver=driver, browser="firefox", timeout=5)
            mock_factory.get_logger.assert_called_once_with(
                "BasePage", browser="firefox"
            )


# ===========================================================================
# navigate
# ===========================================================================


class TestNavigate:
    def test_calls_driver_get(
        self, mock_base_page: BasePage, driver: FakeWebDriver
    ) -> None:
        mock_base_page.navigate("https://example.com")
        driver.get.assert_called_once_with("https://example.com")


# ===========================================================================
# wait_until_clickable
# ===========================================================================


class TestWaitUntilClickable:
    def test_locator_returns_element(
        self, mock_base_page: BasePage, driver: FakeWebDriver
    ) -> None:
        el = FakeWebElement(displayed=True, enabled=True)
        driver._elements[LOCATOR] = el
        result = mock_base_page.wait_until_clickable(LOCATOR)
        assert result is el

    def test_webelement_returns_same_element(
        self, mock_base_page: BasePage, web_element: MagicMock
    ) -> None:
        result = mock_base_page.wait_until_clickable(web_element, timeout=5)  # type: ignore[arg-type]
        assert result is web_element

    def test_locator_timeout_raises_page_error(
        self, mock_base_page: BasePage, driver: FakeWebDriver
    ) -> None:
        # element exists but not clickable => EC returns False => DummyWait raises TimeoutException => PageError
        driver._elements[LOCATOR] = FakeWebElement(displayed=False, enabled=False)
        with pytest.raises(PageError):
            mock_base_page.wait_until_clickable(LOCATOR)

    def test_webelement_timeout_raises_page_error(
        self, mock_base_page: BasePage, web_element: MagicMock
    ) -> None:
        web_element.is_displayed.return_value = False
        web_element.is_enabled.return_value = False
        with pytest.raises(PageError):
            mock_base_page.wait_until_clickable(web_element)  # type: ignore[arg-type]

    def test_no_such_element_raises_page_error(self, mock_base_page: BasePage) -> None:
        with pytest.raises(PageError):
            mock_base_page.wait_until_clickable(LOCATOR)

    def test_invalid_target_raises_type_error(self, mock_base_page: BasePage) -> None:
        with pytest.raises(TypeError):
            mock_base_page.wait_until_clickable("not-a-valid-target")  # type: ignore[arg-type]


# ===========================================================================
# wait_for
# ===========================================================================


class TestWaitFor:
    def test_returns_element_when_present(
        self, mock_base_page: BasePage, driver: FakeWebDriver
    ) -> None:
        el = FakeWebElement()
        driver._elements[LOCATOR] = el
        result = mock_base_page.wait_for(LOCATOR)
        assert result is el

    def test_raises_element_not_found_on_timeout(
        self, mock_base_page: BasePage
    ) -> None:
        mock_base_page.wait.until = MagicMock(side_effect=TimeoutException())  # type: ignore[method-assign]
        with pytest.raises(ElementNotFoundError):
            mock_base_page.wait_for(LOCATOR)


# ===========================================================================
# wait_for_element_to_disappear
# ===========================================================================


class TestWaitForElementToDisappear:
    def test_returns_true_when_element_disappears(
        self, mock_base_page: BasePage, driver: FakeWebDriver
    ) -> None:
        driver._elements[LOCATOR] = FakeWebElement(displayed=False)
        assert mock_base_page.wait_for_element_to_disappear(LOCATOR) is True

    def test_returns_false_on_timeout(
        self, mock_base_page: BasePage, driver: FakeWebDriver
    ) -> None:
        # displayed True => invisibility condition stays False => DummyWait raises TimeoutException => returns False
        driver._elements[LOCATOR] = FakeWebElement(displayed=True)
        assert mock_base_page.wait_for_element_to_disappear(LOCATOR) is False

    def test_uses_custom_timeout(self, mock_base_page: BasePage) -> None:
        with patch(f"{_BASE_PAGE_MODULE}.WebDriverWait") as wait_cls:
            wait_cls.return_value.until.return_value = True
            mock_base_page.wait_for_element_to_disappear(LOCATOR, timeout=99)
            wait_cls.assert_called_once_with(mock_base_page.driver, 99)

    def test_uses_default_timeout_when_none(self, mock_base_page: BasePage) -> None:
        with patch(f"{_BASE_PAGE_MODULE}.WebDriverWait") as wait_cls:
            wait_cls.return_value.until.return_value = True
            mock_base_page.wait_for_element_to_disappear(LOCATOR, timeout=None)
            wait_cls.assert_called_once_with(
                mock_base_page.driver, mock_base_page.timeout
            )


# ===========================================================================
# click
# ===========================================================================


class TestClick:
    def test_click_by_locator_calls_perform_click(
        self, mock_base_page: BasePage, driver: FakeWebDriver
    ) -> None:
        el = FakeWebElement(displayed=True, enabled=True)
        driver._elements[LOCATOR] = el
        with patch.object(mock_base_page, "_perform_click") as perform:
            mock_base_page.click(LOCATOR)
            perform.assert_called_once_with(el)

    def test_click_by_webelement_calls_perform_click(
        self, mock_base_page: BasePage, web_element: MagicMock
    ) -> None:
        with patch.object(mock_base_page, "_perform_click") as perform:
            mock_base_page.click(web_element)  # type: ignore[arg-type]
            perform.assert_called_once_with(web_element)

    def test_page_error_is_reraised(self, mock_base_page: BasePage) -> None:
        with patch.object(
            mock_base_page, "wait_until_clickable", side_effect=PageError("boom")
        ):
            with pytest.raises(PageError):
                mock_base_page.click(LOCATOR)

    @pytest.mark.parametrize(
        "exception_cls",
        [
            ElementClickInterceptedException,
            ElementNotInteractableException,
            WebDriverException,
        ],
    )
    def test_driver_exceptions_raise_element_interaction_error(
        self,
        mock_base_page: BasePage,
        driver: FakeWebDriver,
        exception_cls: type[Exception],
    ) -> None:
        driver._elements[LOCATOR] = FakeWebElement(displayed=True, enabled=True)
        with patch.object(
            mock_base_page, "_perform_click", side_effect=exception_cls()
        ):
            with pytest.raises(ElementInteractionError):
                mock_base_page.click(LOCATOR)

    def test_invalid_target_raises_type_error(self, mock_base_page: BasePage) -> None:
        with pytest.raises(TypeError):
            mock_base_page.click(42)  # type: ignore[arg-type]

    @patch.object(
        BasePage,
        "_perform_click",
        side_effect=WebDriverException("boom"),
    )
    @patch.object(
        BasePage,
        "wait_until_clickable",
        return_value=MagicMock(),
    )
    def test_click_logs_locator_message_on_webdriver_exception(
        self,
        mock_wait_until_clickable: MagicMock,
        mock_perform_click: MagicMock,
        mock_base_page: BasePage,
    ) -> None:
        error = mock_perform_click.side_effect

        with pytest.raises(ElementInteractionError) as exc_info:
            mock_base_page.click(LOCATOR)

        expected = (
            f"Failed to click element {LOCATOR[0]}={LOCATOR[1]} "
            f"using ActionChains: {error}"
        )

        mock_wait_until_clickable.assert_called_once_with(LOCATOR, timeout=10)
        mock_perform_click.assert_called_once()
        mock_base_page.logger.error.assert_called_once_with(expected)
        assert str(exc_info.value) == expected

    @patch.object(
        BasePage,
        "_perform_click",
        side_effect=WebDriverException("boom"),
    )
    @patch.object(
        BasePage,
        "wait_until_clickable",
        return_value=MagicMock(),
    )
    def test_click_logs_webelement_message_on_webdriver_exception(
        self,
        mock_wait_until_clickable: MagicMock,
        mock_perform_click: MagicMock,
        mock_base_page: BasePage,
        web_element: MagicMock,
    ) -> None:
        error = mock_perform_click.side_effect

        with pytest.raises(ElementInteractionError) as exc_info:
            mock_base_page.click(web_element)

        expected = f"Failed to click WebElement using ActionChains: {error}"

        mock_wait_until_clickable.assert_called_once_with(web_element, timeout=10)
        mock_perform_click.assert_called_once()
        mock_base_page.logger.error.assert_called_once_with(expected)
        assert str(exc_info.value) == expected


# ===========================================================================
# _perform_click
# ===========================================================================


class TestPerformClick:
    def test_action_chain_called(self, mock_base_page: BasePage) -> None:
        el = FakeWebElement()
        with patch(f"{_BASE_PAGE_MODULE}.ActionChains") as ac_cls:
            ac = ac_cls.return_value
            mock_base_page._perform_click(el)  # type: ignore[arg-type]
            ac.move_to_element.assert_called_once()
            ac.click.assert_called_once()
            ac.perform.assert_called_once()

    def test_webdriver_exception_raises_element_interaction_error(
        self, mock_base_page: BasePage
    ) -> None:
        el = FakeWebElement()
        with patch(f"{_BASE_PAGE_MODULE}.ActionChains") as ac_cls:
            ac_cls.return_value.perform.side_effect = WebDriverException()
            with pytest.raises(ElementInteractionError):
                mock_base_page._perform_click(el)  # type: ignore[arg-type]


# ===========================================================================
# click_with_offset, double_click, right_click, click_and_hold
# Parameterized over (locator | WebElement) targets to avoid repetition.
# ===========================================================================


class TestActionChainMethods:
    """
    Groups tests for click_with_offset, double_click, right_click, click_and_hold.

    Each method supports both Locator and WebElement targets, and raises
    ElementInteractionError on driver exceptions — we parametrize over these axes.
    """

    @pytest.mark.parametrize("target_fixture", ["locator", "web_element"])
    def test_click_with_offset_calls_action_chains(
        self, mock_base_page: BasePage, web_element: MagicMock, target_fixture: str
    ) -> None:
        target: Any = LOCATOR if target_fixture == "locator" else web_element
        with (
            patch.object(
                mock_base_page, "wait_until_clickable", return_value=web_element
            ),
            patch(f"{_BASE_PAGE_MODULE}.ActionChains") as mock_ac_cls,
        ):
            mock_ac = mock_ac_cls.return_value
            mock_base_page.click_with_offset(target, x_offset=5, y_offset=10)
            mock_ac.move_to_element_with_offset.assert_called_once_with(
                web_element, 5, 10
            )
            mock_ac.click.assert_called_once()
            mock_ac.perform.assert_called_once()

    @pytest.mark.parametrize("target_fixture", ["locator", "web_element"])
    def test_double_click_calls_action_chains(
        self, mock_base_page: BasePage, web_element: MagicMock, target_fixture: str
    ) -> None:
        target: Any = LOCATOR if target_fixture == "locator" else web_element
        with (
            patch.object(
                mock_base_page, "wait_until_clickable", return_value=web_element
            ),
            patch(f"{_BASE_PAGE_MODULE}.ActionChains") as mock_ac_cls,
        ):
            mock_ac = mock_ac_cls.return_value
            mock_base_page.double_click(target)
            mock_ac.double_click.assert_called_once_with(web_element)
            mock_ac.perform.assert_called_once()

    @pytest.mark.parametrize("target_fixture", ["locator", "web_element"])
    def test_right_click_calls_action_chains(
        self, mock_base_page: BasePage, web_element: MagicMock, target_fixture: str
    ) -> None:
        target: Any = LOCATOR if target_fixture == "locator" else web_element
        with (
            patch.object(
                mock_base_page, "wait_until_clickable", return_value=web_element
            ),
            patch(f"{_BASE_PAGE_MODULE}.ActionChains") as mock_ac_cls,
        ):
            mock_ac = mock_ac_cls.return_value
            mock_base_page.right_click(target)
            mock_ac.context_click.assert_called_once_with(web_element)
            mock_ac.perform.assert_called_once()

    @pytest.mark.parametrize("target_fixture", ["locator", "web_element"])
    def test_click_and_hold_calls_action_chains(
        self, mock_base_page: BasePage, web_element: MagicMock, target_fixture: str
    ) -> None:
        target: Any = LOCATOR if target_fixture == "locator" else web_element
        with (
            patch.object(
                mock_base_page, "wait_until_clickable", return_value=web_element
            ),
            patch(f"{_BASE_PAGE_MODULE}.ActionChains") as mock_ac_cls,
            patch(f"{_BASE_PAGE_MODULE}.time") as mock_time,
        ):
            mock_ac = mock_ac_cls.return_value
            mock_base_page.click_and_hold(target, duration=1.5)
            mock_ac.click_and_hold.assert_called_once_with(web_element)
            mock_time.sleep.assert_called_once_with(1.5)

    @pytest.mark.parametrize(
        "method_name, extra_kwargs",
        [
            ("click_with_offset", {"x_offset": 0, "y_offset": 0}),
            ("double_click", {}),
            ("right_click", {}),
            ("click_and_hold", {}),
        ],
    )
    def test_invalid_target_raises_type_error(
        self, mock_base_page: BasePage, method_name: str, extra_kwargs: dict[str, Any]
    ) -> None:
        method = getattr(mock_base_page, method_name)
        # Patch wait_until_clickable so the type check raises immediately
        # without triggering a real WebDriverWait (which would wait up to 10s).
        with patch.object(
            mock_base_page, "wait_until_clickable", side_effect=TypeError
        ):
            with pytest.raises(TypeError):
                method("invalid-target", **extra_kwargs)  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        "method_name, extra_kwargs",
        [
            ("click_with_offset", {"x_offset": 0, "y_offset": 0}),
            ("double_click", {}),
            ("right_click", {}),
            ("click_and_hold", {}),
        ],
    )
    @pytest.mark.parametrize(
        "exception_cls",
        [
            ElementClickInterceptedException,
            ElementNotInteractableException,
            WebDriverException,
        ],
    )
    def test_driver_exceptions_raise_element_interaction_error(
        self,
        mock_base_page: BasePage,
        web_element: MagicMock,
        method_name: str,
        extra_kwargs: dict[str, Any],
        exception_cls: type[Exception],
    ) -> None:
        method = getattr(mock_base_page, method_name)
        with (
            patch.object(
                mock_base_page, "wait_until_clickable", return_value=web_element
            ),
            patch(f"{_BASE_PAGE_MODULE}.ActionChains") as mock_ac_cls,
        ):
            mock_ac_cls.return_value.perform.side_effect = exception_cls()
            with pytest.raises(ElementInteractionError):
                method(LOCATOR, **extra_kwargs)


# ===========================================================================
# find
# ===========================================================================


class TestFind:
    def test_returns_element(
        self, mock_base_page: BasePage, driver: FakeWebDriver
    ) -> None:
        el = FakeWebElement()
        driver._elements[LOCATOR] = el
        assert mock_base_page.find(LOCATOR) is el

    def test_raises_element_not_found_error(self, mock_base_page: BasePage) -> None:
        with pytest.raises(ElementNotFoundError):
            mock_base_page.find(LOCATOR)


# ===========================================================================
# finds
# ===========================================================================


class TestFinds:
    def test_returns_list_of_elements(self, mock_base_page: BasePage) -> None:
        # finds() currently relies on self.wait.until(ec.presence_of_all_elements_located)
        # easiest: monkeypatch wait.until to return a list
        mock_base_page.wait.until = MagicMock(
            return_value=[FakeWebElement(), FakeWebElement()]
        )  # type: ignore[method-assign]
        result = mock_base_page.finds(LOCATOR)
        assert len(result) == 2

    def test_returns_empty_list_on_timeout(self, mock_base_page: BasePage) -> None:
        mock_base_page.wait.until = MagicMock(side_effect=TimeoutException())  # type: ignore[method-assign]
        assert mock_base_page.finds(LOCATOR) == []


# ===========================================================================
# send_keys
# ===========================================================================


class TestSendKeys:
    def test_clears_and_sends_text(self, mock_base_page: BasePage) -> None:
        el = FakeWebElement(text="start")
        with patch.object(mock_base_page, "wait_for", return_value=el):
            mock_base_page.send_keys(LOCATOR, "hello")
            assert "hello" in el.text

    def test_skips_clear_when_clear_first_false(self, mock_base_page: BasePage) -> None:
        el = FakeWebElement(text="start")
        with patch.object(mock_base_page, "wait_for", return_value=el):
            mock_base_page.send_keys(LOCATOR, "hello", clear_first=False)
            assert el.text.startswith("start")

    def test_reraises_page_error(self, mock_base_page: BasePage) -> None:
        with patch.object(
            mock_base_page, "wait_for", side_effect=ElementNotFoundError("not found")
        ):
            with pytest.raises(PageError):
                mock_base_page.send_keys(LOCATOR, "hello")

    def test_webdriver_exception_raises_element_interaction_error(
        self, mock_base_page: BasePage
    ) -> None:
        el = FakeWebElement()
        with patch.object(mock_base_page, "wait_for", return_value=el):
            with patch.object(el, "send_keys", side_effect=WebDriverException()):
                with pytest.raises(ElementInteractionError):
                    mock_base_page.send_keys(LOCATOR, "hello")


# ===========================================================================
# get_text
# ===========================================================================


class TestGetText:
    def test_returns_element_text(self, mock_base_page: BasePage) -> None:
        el = FakeWebElement(text="My Text")
        with patch.object(mock_base_page, "find", return_value=el):
            assert mock_base_page.get_text(LOCATOR) == "My Text"


# ===========================================================================
# is_displayed
# ===========================================================================


class TestIsDisplayed:
    def test_returns_true_when_visible(self, mock_base_page: BasePage) -> None:
        el = FakeWebElement(displayed=True)
        mock_base_page.wait.until = MagicMock(return_value=el)  # type: ignore[method-assign]
        assert mock_base_page.is_displayed(LOCATOR) is True

    def test_returns_false_on_timeout(self, mock_base_page: BasePage) -> None:
        mock_base_page.wait.until = MagicMock(side_effect=TimeoutException())  # type: ignore[method-assign]
        assert mock_base_page.is_displayed(LOCATOR) is False

    def test_returns_false_on_webdriver_exception(
        self, mock_base_page: BasePage
    ) -> None:
        mock_base_page.wait.until = MagicMock(side_effect=WebDriverException())  # type: ignore[method-assign]
        assert mock_base_page.is_displayed(LOCATOR) is False


# ===========================================================================
# get_attribute
# ===========================================================================


class TestGetAttribute:
    def test_returns_attribute_value(self, mock_base_page: BasePage) -> None:
        el = FakeWebElement()
        with patch.object(mock_base_page, "find", return_value=el):
            assert mock_base_page.get_attribute(LOCATOR, "class") == "attr-class"

    def test_returns_none_when_attribute_missing(
        self, mock_base_page: BasePage
    ) -> None:
        el = FakeWebElement()
        with patch.object(el, "get_attribute", return_value=None):
            with patch.object(mock_base_page, "find", return_value=el):
                assert mock_base_page.get_attribute(LOCATOR, "data-missing") is None


# ===========================================================================
# get_current_url / get_title / refresh_page
# ===========================================================================


class TestPageUtils:
    def test_get_current_url(
        self, mock_base_page: BasePage, driver: FakeWebDriver
    ) -> None:
        driver.current_url = "https://example.com/mock_page"
        assert mock_base_page.get_current_url() == "https://example.com/mock_page"

    def test_get_title(self, mock_base_page: BasePage, driver: FakeWebDriver) -> None:
        driver.title = "My Page"
        assert mock_base_page.get_title() == "My Page"

    def test_refresh_page_calls_driver(
        self, mock_base_page: BasePage, driver: FakeWebDriver
    ) -> None:
        mock_base_page.refresh_page()
        driver.refresh.assert_called_once()


# ===========================================================================
# scroll_to
# ===========================================================================


class TestScrollTo:
    def test_executes_scroll_script(
        self, mock_base_page: BasePage, driver: FakeWebDriver
    ) -> None:
        el = FakeWebElement()
        with patch.object(mock_base_page, "find", return_value=el):
            mock_base_page.scroll_to(LOCATOR)
            driver.execute_script.assert_called_once_with(
                "arguments[0].scrollIntoView(true);", el
            )


# ===========================================================================
# execute_script
# ===========================================================================


class TestExecuteScript:
    def test_delegates_to_driver(
        self, mock_base_page: BasePage, driver: FakeWebDriver
    ) -> None:
        driver.execute_script.return_value = 42
        assert mock_base_page.execute_script("return 1+1;") == 42

    def test_passes_extra_args(
        self, mock_base_page: BasePage, driver: FakeWebDriver
    ) -> None:
        el = FakeWebElement()
        mock_base_page.execute_script("arguments[0].click();", el)
        driver.execute_script.assert_called_once_with("arguments[0].click();", el)


# ===========================================================================
# switch_to_frame / switch_to_default_content
# ===========================================================================


class TestFrameSwitching:
    @pytest.mark.parametrize("frame_reference", [0, "my-frame"])
    def test_switch_to_frame(
        self,
        mock_base_page: BasePage,
        driver: FakeWebDriver,
        frame_reference: int | str,
    ) -> None:
        mock_base_page.switch_to_frame(frame_reference)
        driver.switch_to.frame.assert_called_once_with(frame_reference)

    def test_switch_to_default_content(
        self, mock_base_page: BasePage, driver: FakeWebDriver
    ) -> None:
        mock_base_page.switch_to_default_content()
        driver.switch_to.default_content.assert_called_once()


# ===========================================================================
# take_screenshot
# ===========================================================================


class TestTakeScreenshot:
    def test_saves_screenshot_and_returns_path(
        self, mock_base_page: BasePage, driver: FakeWebDriver, tmp_path: Any
    ) -> None:
        with patch(
            f"{_BASE_PAGE_MODULE}.LoggerFactory.get_log_dir", return_value=str(tmp_path)
        ):
            result = mock_base_page.take_screenshot(
                file_path="screenshots", filename="test.png"
            )

        expected = os.path.join(str(tmp_path), "screenshots", "test.png")
        assert result == expected
        driver.save_screenshot.assert_called_once_with(expected)

    def test_falls_back_to_cwd_when_log_dir_is_none(
        self, mock_base_page: BasePage, driver: FakeWebDriver, tmp_path: Any
    ) -> None:
        with (
            patch(f"{_BASE_PAGE_MODULE}.LoggerFactory.get_log_dir", return_value=None),
            patch("os.getcwd", return_value=str(tmp_path)),
        ):
            result = mock_base_page.take_screenshot(
                file_path="shots", filename="fallback.png"
            )

        expected = os.path.join(str(tmp_path), "shots", "fallback.png")
        assert result == expected


# ===========================================================================
# get_alert
# ===========================================================================


class TestGetAlert:
    def test_returns_alert_when_present(
        self, mock_base_page: BasePage, driver: FakeWebDriver
    ) -> None:
        fake_alert = MagicMock(spec=Alert)
        driver.switch_to._alert = fake_alert

        # alert_is_present returns driver.switch_to.alert (not necessarily Alert instance),
        # BasePage checks isinstance(alert, Alert) so patch Alert to match our fake type.
        with patch(f"{_BASE_PAGE_MODULE}.Alert", type(fake_alert)):
            assert mock_base_page.get_alert(timeout=1) is fake_alert

    def test_returns_none_on_timeout(self, mock_base_page: BasePage) -> None:
        with patch(f"{_BASE_PAGE_MODULE}.WebDriverWait") as wait_cls:
            wait_cls.return_value.until.side_effect = TimeoutException()
            assert mock_base_page.get_alert(timeout=1) is None

    def test_returns_none_when_not_alert_instance(
        self, mock_base_page: BasePage
    ) -> None:
        with patch(f"{_BASE_PAGE_MODULE}.WebDriverWait") as wait_cls:
            wait_cls.return_value.until.return_value = "not-an-alert"
            assert mock_base_page.get_alert(timeout=1) is None


# ===========================================================================
# is_alert_present
# ===========================================================================


class TestIsAlertPresent:
    def test_returns_true_with_timeout_when_alert_present(
        self, mock_base_page: BasePage
    ) -> None:
        with patch.object(mock_base_page, "get_alert", return_value=MagicMock()):
            assert mock_base_page.is_alert_present(timeout=5) is True

    def test_returns_false_with_timeout_when_no_alert(
        self, mock_base_page: BasePage
    ) -> None:
        with patch.object(mock_base_page, "get_alert", return_value=None):
            assert mock_base_page.is_alert_present(timeout=5) is False

    def test_returns_true_immediate_check_when_alert_present(
        self, mock_base_page: BasePage, driver: FakeWebDriver
    ) -> None:
        driver.switch_to._alert = MagicMock()
        assert mock_base_page.is_alert_present(timeout=0) is True

    def test_returns_false_immediate_check_when_no_alert(
        self, mock_base_page: BasePage, driver: FakeWebDriver
    ) -> None:
        driver.switch_to._alert = None
        assert mock_base_page.is_alert_present(timeout=0) is False


# ===========================================================================
# accept_alert
# ===========================================================================


class TestAcceptAlert:
    def test_accepts_alert_and_returns_text(self, mock_base_page: BasePage) -> None:
        mock_alert = MagicMock()
        mock_alert.text = "Are you sure?"
        with patch.object(mock_base_page, "get_alert", return_value=mock_alert):
            assert mock_base_page.accept_alert() == "Are you sure?"
        mock_alert.accept.assert_called_once()

    def test_returns_none_when_no_alert(self, mock_base_page: BasePage) -> None:
        with patch.object(mock_base_page, "get_alert", return_value=None):
            assert mock_base_page.accept_alert() is None
