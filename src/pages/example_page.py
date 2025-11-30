"""Example page object - replace with your actual pages."""

from selenium.webdriver.common.by import By

from src.pages.base_page import BasePage


class ExamplePage(BasePage):
    """Example page object model."""

    # Locators
    EXAMPLE_LOCATOR = (By.ID, "example")

    def __init__(self, driver):
        """Initialize the example page."""
        super().__init__(driver)
