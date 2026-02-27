"""Base Page Object Model with common methods for all pages."""

import os
import time
from typing import Any, overload

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    NoAlertPresentException,
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from ..utils.logger_util import LoggerFactory

Locator = tuple[str, str]


class PageError(Exception):
    """Base exception for page interaction errors."""


class ElementNotFoundError(PageError):
    pass


class ElementNotClickableError(PageError):
    pass


class ElementInteractionError(PageError):
    pass


class BasePage:
    """Base class for all Page Object Models."""

    def __init__(self, driver: WebDriver, browser: str, timeout: int = 10) -> None:
        """
        Initialize the base page.

        Args:
            driver: Selenium WebDriver instance
            timeout: Default timeout for waits in seconds
        """
        self.driver: WebDriver = driver
        self.timeout: int = timeout
        self.wait: WebDriverWait[WebDriver] = WebDriverWait(self.driver, self.timeout)
        # Create browser-specific logger
        self.logger = LoggerFactory.get_logger(self.__class__.__name__, browser=browser)
        self.logger.debug(
            "Initialized InventoryPage with driver: %s", type(driver).__name__
        )

    def navigate(self, url: str) -> None:
        """
        Navigate to a specific URL.

        Args:
            url: URL to navigate to
        """
        self.logger.info(f"Navigating to: {url}")
        self.driver.get(url)

    # ============================================================================
    # OVERLOADED WAIT METHODS
    # ============================================================================

    @overload
    def wait_until_clickable(self, target: Locator, timeout: int = 10) -> WebElement:
        """Wait for an element to be clickable by locator."""
        ...

    @overload
    def wait_until_clickable(self, target: WebElement, timeout: int = 10) -> WebElement:
        """Wait for a WebElement to be clickable."""
        ...

    def wait_until_clickable(
        self, target: Locator | WebElement, timeout: int = 10
    ) -> WebElement:
        """
        Wait for an element to be clickable (overloaded).

        Supports waiting for an element by locator or by WebElement reference.
        Waits until the element is both displayed and enabled.

        Args:
            target: Either a locator tuple (By, value) or a WebElement object.
            timeout: Maximum wait time in seconds. Default is 10.

        Returns:
            WebElement once it's clickable.

        Raises:
            PageError: If wait times out or element is not found.

        Example:
            >>> # Wait by locator
            >>> element = page.wait_until_clickable((By.ID, "submit"))
            >>> # Wait by element
            >>> el = driver.find_element(By.ID, "submit")
            >>> same_element = page.wait_until_clickable(el, timeout=5)
        """
        try:
            # Create a typed wait once to avoid redeclaration issues
            wait: WebDriverWait[WebDriver] = WebDriverWait(self.driver, timeout)

            # Handle Locator tuple
            if isinstance(target, tuple) and len(target) == 2:
                self.logger.debug(
                    f"Waiting for element {target} to be clickable (timeout={timeout}s)"
                )
                element = wait.until(ec.element_to_be_clickable(target))
                self.logger.debug(f"Element {target} is now clickable")
                return element

            # Handle WebElement
            elif isinstance(target, WebElement):
                self.logger.debug(
                    f"Waiting for WebElement to be clickable (timeout={timeout}s)"
                )
                wait.until(lambda d: target.is_displayed() and target.is_enabled())
                self.logger.debug("WebElement is now clickable")
                return target

            else:
                raise TypeError(
                    f"target must be a Locator tuple or WebElement, got {type(target)}"
                )

        except TimeoutException as e:
            if isinstance(target, tuple):
                msg = f"Element {target} not clickable within {timeout}s: {e}"
            else:
                msg = f"WebElement not clickable within {timeout}s: {e}"
            self.logger.error(msg)
            raise PageError(msg) from e

        except NoSuchElementException as e:
            msg = f"Element {target} not found: {e}"
            self.logger.error(msg)
            raise PageError(msg) from e

    def wait_for(self, locator: Locator, timeout: int = 10) -> WebElement:
        """Wait until the element is present in the DOM and return it."""
        self.logger.debug(f"Waiting for element {locator} (timeout={timeout})")
        try:
            return self.wait.until(ec.presence_of_element_located(locator))
        except TimeoutException as e:
            msg = f"Timed out waiting for element {locator[0]}={locator[1]} after {timeout}s"
            self.logger.error(msg)
            raise ElementNotFoundError(msg) from e

    def wait_for_element_to_disappear(
        self, locator: Locator, timeout: int | None = None
    ) -> bool:
        """
        Wait for an element to disappear.

        Args:
            locator: Tuple of (By, value)
            timeout: Custom timeout (uses default if None)

        Returns:
            True if element disappeared, False otherwise
        """
        try:
            self.logger.debug(
                f"Waiting for element to disappear: {locator} (timeout={timeout})"
            )
            wait_time = timeout if timeout is not None else self.timeout
            wait: WebDriverWait[WebDriver] = WebDriverWait(self.driver, wait_time)
            wait.until(ec.invisibility_of_element_located(locator))
            return True
        except TimeoutException:
            return False

    # ============================================================================
    # OVERLOADED CLICK METHOD - Using ActionChains.perform()
    # ============================================================================

    @overload
    def click(self, target: Locator, timeout: int = 10) -> None:
        """Click an element by locator using ActionChains."""
        ...

    @overload
    def click(self, target: WebElement, timeout: int = 10) -> None:
        """Click a WebElement using ActionChains."""
        ...

    def click(
        self,
        target: Locator | WebElement,
        timeout: int = 10,
    ) -> None:
        """
        Click an element using ActionChains.perform().

        Uses Selenium's ActionChains to perform a more realistic click that
        simulates user behavior. This is useful for elements that might be
        intercepted by overlays or require hover actions.

        Supports clicking by locator or by WebElement. Waits for the element
        to be clickable before attempting the click action.

        Args:
            target: Either a locator tuple (By, value) or a WebElement object.
            timeout: Maximum time to wait for element to be clickable in seconds.
                    Default is 10.

        Raises:
            PageError: If page-level error occurs during waiting.
            ElementInteractionError: If click action fails due to interception,
                                    non-interactable state, or WebDriver error.

        Example:
            >>> page = BasePage(driver)
            >>> # Click by locator
            >>> page.click((By.ID, "submit-button"))
            >>> page.click((By.XPATH, "//button[@class='submit']"), timeout=5)
            >>> # Click by element
            >>> element = driver.find_element(By.ID, "submit-button")
            >>> page.click(element)
            >>> page.click(element, timeout=15)
        """
        try:
            # Handle WebElement
            if isinstance(target, WebElement):
                self.logger.debug(
                    f"Clicking WebElement using ActionChains with timeout={timeout}s"
                )
                el = self.wait_until_clickable(target, timeout=timeout)
                self._perform_click(el)

            # Handle Locator tuple
            elif isinstance(target, tuple) and len(target) == 2:
                self.logger.debug(
                    f"Clicking element: {target} using ActionChains with timeout={timeout}s"
                )
                el = self.wait_until_clickable(target, timeout=timeout)
                self._perform_click(el)

            else:
                raise TypeError(
                    f"target must be a Locator tuple or WebElement, got {type(target)}"
                )

        except PageError:
            # Re-raise our clearer PageError
            self.logger.error(f"Page error occurred while clicking {target}")
            raise

        except (
            ElementClickInterceptedException,
            ElementNotInteractableException,
            WebDriverException,
        ) as e:
            if isinstance(target, WebElement):
                msg = f"Failed to click WebElement using ActionChains: {e}"
            else:
                msg = f"Failed to click element {target[0]}={target[1]} using ActionChains: {e}"

            self.logger.error(msg)
            raise ElementInteractionError(msg) from e

        except TypeError:
            # Re-raise type errors
            raise

    # ============================================================================
    # ACTIONCHAINS CLICK
    # ============================================================================

    def click_with_offset(
        self,
        target: Locator | WebElement,
        x_offset: int = 0,
        y_offset: int = 0,
        timeout: int = 10,
    ) -> None:
        """
        Click an element at a specific offset using ActionChains.

        Useful for clicking specific parts of an element or avoiding
        interceptions by clicking away from the element center.

        Args:
            target: Locator tuple or WebElement to click.
            x_offset: Horizontal offset from element's center in pixels.
            y_offset: Vertical offset from element's center in pixels.
            timeout: Maximum wait time in seconds.

        Example:
            >>> page.click_with_offset((By.ID, "button"), x_offset=10, y_offset=5)
        """
        try:
            if isinstance(target, WebElement):
                self.logger.debug(
                    f"Clicking WebElement with offset ({x_offset}, {y_offset})"
                )
                el = self.wait_until_clickable(target, timeout=timeout)
            elif isinstance(target, tuple):
                self.logger.debug(
                    f"Clicking {target} with offset ({x_offset}, {y_offset})"
                )
                el = self.wait_until_clickable(target, timeout=timeout)
            else:
                raise TypeError(f"Invalid target type: {type(target)}")

            actions = ActionChains(self.driver)
            actions.move_to_element_with_offset(el, x_offset, y_offset)
            actions.click()
            actions.perform()

        except (
            ElementClickInterceptedException,
            ElementNotInteractableException,
            WebDriverException,
        ) as e:
            msg = f"Failed to click with offset: {e}"
            self.logger.error(msg)
            raise ElementInteractionError(msg) from e

    def double_click(
        self,
        target: Locator | WebElement,
        timeout: int = 10,
    ) -> None:
        """
        Double-click an element using ActionChains.

        Args:
            target: Locator tuple or WebElement to double-click.
            timeout: Maximum wait time in seconds.

        Example:
            >>> page.double_click((By.ID, "text-input"))
        """
        try:
            if isinstance(target, WebElement):
                self.logger.debug("Double-clicking WebElement")
                el = self.wait_until_clickable(target, timeout=timeout)
            elif isinstance(target, tuple):
                self.logger.debug(f"Double-clicking element: {target}")
                el = self.wait_until_clickable(target, timeout=timeout)
            else:
                raise TypeError(f"Invalid target type: {type(target)}")

            actions = ActionChains(self.driver)
            actions.double_click(el)
            actions.perform()

        except (
            ElementClickInterceptedException,
            ElementNotInteractableException,
            WebDriverException,
        ) as e:
            msg = f"Failed to double-click element: {e}"
            self.logger.error(msg)
            raise ElementInteractionError(msg) from e

    def right_click(
        self,
        target: Locator | WebElement,
        timeout: int = 10,
    ) -> None:
        """
        Right-click (context menu) on an element using ActionChains.

        Args:
            target: Locator tuple or WebElement to right-click.
            timeout: Maximum wait time in seconds.

        Example:
            >>> page.right_click((By.ID, "element"))
        """
        try:
            if isinstance(target, WebElement):
                self.logger.debug("Right-clicking WebElement")
                el = self.wait_until_clickable(target, timeout=timeout)
            elif isinstance(target, tuple):
                self.logger.debug(f"Right-clicking element: {target}")
                el = self.wait_until_clickable(target, timeout=timeout)
            else:
                raise TypeError(f"Invalid target type: {type(target)}")

            actions = ActionChains(self.driver)
            actions.context_click(el)
            actions.perform()

        except (
            ElementClickInterceptedException,
            ElementNotInteractableException,
            WebDriverException,
        ) as e:
            msg = f"Failed to right-click element: {e}"
            self.logger.error(msg)
            raise ElementInteractionError(msg) from e

    def click_and_hold(
        self,
        target: Locator | WebElement,
        duration: float = 1.0,
        timeout: int = 10,
    ) -> None:
        """
        Click and hold an element for a specified duration using ActionChains.

        Args:
            target: Locator tuple or WebElement to click and hold.
            duration: Time to hold the click in seconds.
            timeout: Maximum wait time in seconds.

        Example:
            >>> page.click_and_hold((By.ID, "slider"), duration=2.0)
        """
        try:
            if isinstance(target, WebElement):
                self.logger.debug(f"Click and hold WebElement for {duration}s")
                el = self.wait_until_clickable(target, timeout=timeout)
            elif isinstance(target, tuple):
                self.logger.debug(f"Click and hold {target} for {duration}s")
                el = self.wait_until_clickable(target, timeout=timeout)
            else:
                raise TypeError(f"Invalid target type: {type(target)}")

            actions = ActionChains(self.driver)
            actions.click_and_hold(el)
            actions.perform()
            time.sleep(duration)
            actions.release()
            actions.perform()

        except (
            ElementClickInterceptedException,
            ElementNotInteractableException,
            WebDriverException,
        ) as e:
            msg = f"Failed to click and hold element: {e}"
            self.logger.error(msg)
            raise ElementInteractionError(msg) from e

    def _perform_click(self, element: WebElement) -> None:
        """
        Perform the actual click action using ActionChains.

        Args:
            element: WebElement to click.

        Raises:
            WebDriverException: If click action fails.
        """
        try:
            actions = ActionChains(self.driver)
            actions.move_to_element(element)
            actions.click(element)
            actions.perform()
            self.logger.debug("Click action performed successfully")
        except WebDriverException as e:
            raise ElementInteractionError(f"ActionChains click failed: {e}") from e

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    def find(self, locator: Locator) -> WebElement:
        """
        Find a single element with wait.

        Args:
            locator: Tuple of (By, value)

        Returns:
            WebElement if found

        Raises:
            TimeoutException: If element not found within timeout
        """
        try:
            self.logger.debug(f"Finding element: {locator}")
            return self.driver.find_element(*locator)
        except NoSuchElementException as e:
            msg = f"Element not found: {locator[0]}={locator[1]}"
            self.logger.error(msg)
            raise ElementNotFoundError(msg) from e

    def finds(self, locator: Locator) -> list[WebElement]:
        """
        Find multiple elements with wait.

        Args:
            locator: Tuple of (By, value)

        Returns:
            List of WebElements
        """
        try:
            elements = self.wait.until(ec.presence_of_all_elements_located(locator))
            self.logger.debug(f"Found {len(elements)} elements: {locator}")
            return elements
        except TimeoutException:
            self.logger.warning(f"No elements found: {locator}")
            return []

    def send_keys(
        self, locator: Locator, text: str, timeout: int = 10, clear_first: bool = True
    ) -> None:
        """
        Send keys to an input element.

        Args:
            locator: Tuple of (By, value)
            text: Text to send
            clear_first: Whether to clear the field first
        """
        try:
            self.logger.debug(
                f"Sending keys to element: {locator} (text='{text}', clear_first={clear_first})"
            )
            el = self.wait_for(locator, timeout=timeout)
            if clear_first:
                el.clear()
            el.send_keys(text)
        except PageError:
            raise
        except (WebDriverException, Exception) as e:
            msg = f"Failed to fill element {locator[0]}={locator[1]} with value '{text}': {e}"
            self.logger.error(msg)
            raise ElementInteractionError(msg) from e

    def get_text(self, locator: Locator) -> str:
        """
        Get text from an element.

        Args:
            locator: Tuple of (By, value)

        Returns:
            Element text
        """
        self.logger.debug(f"Getting text from element: {locator}")
        element = self.find(locator)
        text = element.text
        self.logger.debug(f"Got text from {locator}: {text}")
        return text

    def is_displayed(self, locator: Locator, timeout: int | None = 5) -> bool:
        """
        Check if element is displayed.

        Args:
            locator: Tuple of (By, value)
            timeout: Custom timeout (uses default if None)

        Returns:
            True if element is displayed, False otherwise
        """
        try:
            self.logger.debug(
                f"Checking visibility for element: {locator} (timeout={timeout})"
            )
            el = self.wait.until(ec.visibility_of_element_located(locator))
            return el.is_displayed()
        except TimeoutException:
            self.logger.debug(f"Element not visible: {locator[0]}={locator[1]}")
            return False
        except WebDriverException as e:
            self.logger.error(f"Error checking visibility for {locator}: {e}")
            return False

    def get_attribute(self, locator: Locator, attribute: str) -> str | None:
        """
        Get attribute value from an element.

        Args:
            locator: Tuple of (By, value)
            attribute: Attribute name

        Returns:
            Attribute value (may be None)
        """
        element = self.find(locator)
        value = element.get_attribute(attribute)
        self.logger.debug(f"Got attribute '{attribute}' from {locator}: {value}")
        return value

    def get_current_url(self) -> str:
        """
        Get current page URL.

        Returns:
            Current URL
        """
        return self.driver.current_url

    def get_title(self) -> str:
        """
        Get page title.

        Returns:
            Page title
        """
        return self.driver.title

    def refresh_page(self) -> None:
        """Refresh the current page."""
        self.logger.info("Refreshing page")
        self.driver.refresh()

    def scroll_to(self, locator: Locator) -> None:
        """
        Scroll to make an element visible.

        Args:
            locator: Tuple of (By, value)
        """
        element = self.find(locator)
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        self.logger.debug(f"Scrolled to element: {locator}")

    def execute_script(self, script: str, *args: Any) -> Any:
        """
        Execute JavaScript on the page.

        Args:
            script: JavaScript code to execute
            *args: Arguments to pass to the script

        Returns:
            Script return value
        """
        return self.driver.execute_script(script, *args)

    def switch_to_frame(self, frame_reference: int | str | WebElement) -> None:
        """
        Switch to an iframe.

        Args:
            frame_reference: Frame index, name, or WebElement
        """
        self.driver.switch_to.frame(frame_reference)
        self.logger.info(f"Switched to frame: {frame_reference}")

    def switch_to_default_content(self) -> None:
        """Switch back to default content from iframe."""
        self.driver.switch_to.default_content()
        self.logger.info("Switched to default content")

    def take_screenshot(self, file_path: str, filename: str) -> str:
        """
        Take a screenshot of the current page.

        Args:
            filename: Name for the screenshot file

        Returns:
            Path to saved screenshot
        """
        log_dir = LoggerFactory.get_log_dir() or os.getcwd()
        target_dir = os.path.join(log_dir, file_path)
        os.makedirs(target_dir, exist_ok=True)
        screenshot_path = os.path.join(target_dir, filename)
        self.driver.save_screenshot(screenshot_path)
        self.logger.info(f"Screenshot saved: {screenshot_path}")
        return screenshot_path

    def get_alert(self, timeout: int = 5) -> Alert | None:
        try:
            alert = WebDriverWait(self.driver, timeout).until(ec.alert_is_present())
            if isinstance(alert, Alert):
                return alert
            return None
        except TimeoutException:
            return None

    def is_alert_present(self, timeout: int = 0) -> bool:
        """Quick check: if timeout>0 wait, otherwise check immediately."""
        try:
            if timeout:
                return bool(self.get_alert(timeout))
            # immediate check (no wait)
            _ = self.driver.switch_to.alert
            return True
        except (NoAlertPresentException, TimeoutException):
            return False

    def accept_alert(self, timeout: int = 5) -> str | None:
        """Accept alert if present and return its text, else None."""
        alert = self.get_alert(timeout)
        if alert:
            text = str(alert.text)
            alert.accept()
            self.logger.info("Accepted alert: %s", text)
            return text
        return None
