"""Example page object - replace with your actual pages."""

from .base_page import BasePage
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver


class ExamplePage(BasePage):
    """Example page object model."""

    # Locators
    EXAMPLE_LOCATOR = (By.ID, "example")

    def __init__(self, driver: WebDriver, browser: str, timeout: int = 10) -> None:
        """Initialize the example page."""
        super().__init__(driver, browser=browser, timeout=timeout)
