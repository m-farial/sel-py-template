"""Base Page Object Model with common methods for all pages."""

import logging

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from src.utils.logger_util import get_logger


class BasePage:
    """Base class for all Page Object Models."""

    def __init__(self, driver: WebDriver, timeout: int = 10):
        """
        Initialize the base page.

        Args:
            driver: Selenium WebDriver instance
            timeout: Default timeout for waits in seconds
        """
        self.driver: WebDriver = driver
        self.timeout: int = timeout
        self.wait: WebDriverWait = WebDriverWait(driver, timeout)
        self.logger: logging.Logger = get_logger(self.__class__.__name__)

    def navigate_to(self, url: str) -> None:
        """
        Navigate to a specific URL.

        Args:
            url: URL to navigate to
        """
        self.logger.info(f"Navigating to: {url}")
        self.driver.get(url)

    def find_element(self, locator: tuple) -> WebElement:
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
            element = self.wait.until(ec.presence_of_element_located(locator))
            self.logger.debug(f"Found element: {locator}")
            return element
        except TimeoutException:
            self.logger.error(f"Element not found: {locator}")
            raise

    def find_elements(self, locator: tuple) -> list[WebElement]:
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

    def click(self, locator: tuple) -> None:
        """
        Click an element with wait for clickability.

        Args:
            locator: Tuple of (By, value)
        """
        element = self.wait.until(ec.element_to_be_clickable(locator))
        element.click()
        self.logger.info(f"Clicked element: {locator}")

    def send_keys(self, locator: tuple, text: str, clear_first: bool = True) -> None:
        """
        Send keys to an input element.

        Args:
            locator: Tuple of (By, value)
            text: Text to send
            clear_first: Whether to clear the field first
        """
        element = self.find_element(locator)
        if clear_first:
            element.clear()
        element.send_keys(text)
        self.logger.info(f"Sent keys to element: {locator}")

    def get_text(self, locator: tuple) -> str:
        """
        Get text from an element.

        Args:
            locator: Tuple of (By, value)

        Returns:
            Element text
        """
        element = self.find_element(locator)
        text = element.text
        self.logger.debug(f"Got text from {locator}: {text}")
        return text

    def is_displayed(self, locator: tuple, timeout: int | None = None) -> bool:
        """
        Check if element is displayed.

        Args:
            locator: Tuple of (By, value)
            timeout: Custom timeout (uses default if None)

        Returns:
            True if element is displayed, False otherwise
        """
        try:
            wait_time = timeout if timeout is not None else self.timeout
            wait = WebDriverWait(self.driver, wait_time)
            wait.until(ec.visibility_of_element_located(locator))
            return True
        except TimeoutException:
            return False

    def wait_for_element_to_disappear(
        self, locator: tuple, timeout: int | None = None
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
            wait_time = timeout if timeout is not None else self.timeout
            wait = WebDriverWait(self.driver, wait_time)
            wait.until(ec.invisibility_of_element_located(locator))
            return True
        except TimeoutException:
            return False

    def get_attribute(self, locator: tuple, attribute: str) -> str:
        """
        Get attribute value from an element.

        Args:
            locator: Tuple of (By, value)
            attribute: Attribute name

        Returns:
            Attribute value
        """
        element = self.find_element(locator)
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

    def scroll_to_element(self, locator: tuple) -> None:
        """
        Scroll to make an element visible.

        Args:
            locator: Tuple of (By, value)
        """
        element = self.find_element(locator)
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        self.logger.debug(f"Scrolled to element: {locator}")

    def execute_script(self, script: str, *args) -> any:
        """
        Execute JavaScript on the page.

        Args:
            script: JavaScript code to execute
            *args: Arguments to pass to the script

        Returns:
            Script return value
        """
        return self.driver.execute_script(script, *args)

    def switch_to_frame(self, frame_reference) -> None:
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

    def take_screenshot(self, filename: str) -> str:
        """
        Take a screenshot of the current page.

        Args:
            filename: Name for the screenshot file

        Returns:
            Path to saved screenshot
        """
        screenshot_path = f"logs/screenshots/{filename}"
        self.driver.save_screenshot(screenshot_path)
        self.logger.info(f"Screenshot saved: {screenshot_path}")
        return screenshot_path
