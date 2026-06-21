"""
Example page object — use this as a reference when creating your own pages.

INSTRUCTIONS FOR DOWNSTREAM USERS:
  1. Copy this file into src/pages/ and rename it (e.g. login_page.py)
  2. Rename the class to match your page (e.g. LoginPage)
  3. Replace the Element declarations with your own locators and element types
  4. Add methods that represent actions a user can perform on the page

DO NOT modify this file — it lives in examples/ which is template-owned.

HOW ELEMENTS WORK:
  Each class-level attribute declared with Element(...) is a Python descriptor.
  A descriptor is a special object that intercepts attribute access — so when
  you write `self.username_input` on an instance, the Element descriptor
  automatically creates and returns a BoundElement tied to that page instance.

  BoundElement gives you a rich API for interacting with the element:
    .click()               — click the element
    .type("text")          — clear and type into an input
    .text()                — read the visible text
    .is_visible()          — check if it's on screen
    .should_be_visible()   — assert it's visible (raises AssertionError if not)
    .should_contain_text("expected") — assert text content
    ... and more (see sel_py_template/ui/elements.py)
"""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from sel_py_template.pages.base_page import BasePage
from sel_py_template.ui.elements import Element, ElementType


class ExamplePage(BasePage):
    """
    Example page object model demonstrating the Element descriptor pattern.

    Each Element(...) declaration below defines a UI element on this page.
    The arguments are:
      - value:        the selector string (e.g. "user-name", ".submit-btn")
      - element_type: what kind of element it is (ElementType.BUTTON, TEXT_INPUT, etc.)
      - by:           the Selenium By strategy (default: By.ID)
      - name:         a human-readable label used in logs and error messages
      - timeout_s:    how many seconds to wait for this element (default: 10)
    """

    # --- Inputs ---
    username_input: Element = Element(
        "username",
        ElementType.TEXT_INPUT,
        by=By.ID,
        name="Username Input",
    )
    password_input: Element = Element(
        "password",
        ElementType.TEXT_INPUT,
        by=By.ID,
        name="Password Input",
    )

    # --- Buttons ---
    submit_button: Element = Element(
        "input[type='submit']",
        ElementType.BUTTON,
        by=By.CSS_SELECTOR,
        name="Submit Button",
    )

    # --- Feedback / state ---
    error_message: Element = Element(
        ".error-message",
        ElementType.TOAST,
        by=By.CSS_SELECTOR,
        name="Error Message",
    )
    success_banner: Element = Element(
        ".success-banner",
        ElementType.TOAST,
        by=By.CSS_SELECTOR,
        name="Success Banner",
    )

    def __init__(self, driver: WebDriver, browser: str, timeout: int = 10) -> None:
        """
        Initialize the example page.

        Args:
            driver: The Selenium WebDriver instance controlling the browser.
            browser: Name of the browser being used (e.g. 'chrome', 'firefox').
            timeout: Default number of seconds to wait for elements to appear.
        """
        super().__init__(driver, browser=browser, timeout=timeout)

    # ------------------------------------------------------------------ #
    # Actions — each method represents one thing a user can do on the page #
    # ------------------------------------------------------------------ #

    def enter_username(self, username: str) -> None:
        """
        Type a username into the username input field.

        Args:
            username: The username string to enter.
        """
        self.username_input.type(username)

    def enter_password(self, password: str) -> None:
        """
        Type a password into the password input field.

        Args:
            password: The password string to enter.
        """
        self.password_input.type(password)

    def submit(self) -> None:
        """Click the submit button."""
        self.submit_button.click_retry()

    def login(self, username: str, password: str) -> None:
        """
        Convenience method: fill in credentials and submit the form.

        This composes the lower-level action methods above into a single
        reusable step, which keeps test files readable.

        Args:
            username: The username to log in with.
            password: The password to log in with.
        """
        self.enter_username(username)
        self.enter_password(password)
        self.submit()

    # ------------------------------------------------------------------ #
    # Assertions — each method verifies something about the page state    #
    # ------------------------------------------------------------------ #

    def should_show_error(self, expected_text: str) -> None:
        """
        Assert that an error message is visible and contains expected_text.

        The should_* methods on BoundElement raise AssertionError automatically
        if the condition is not met, so no explicit assert is needed here.

        Args:
            expected_text: The text that must appear inside the error message.
        """
        self.error_message.should_be_visible()
        self.error_message.should_contain_text(expected_text)

    def should_show_success(self) -> None:
        """Assert that the success banner is visible after a successful action."""
        self.success_banner.should_be_visible()

    def should_have_submit_enabled(self) -> None:
        """Assert that the submit button is enabled and ready to interact with."""
        self.submit_button.should_be_enabled()
