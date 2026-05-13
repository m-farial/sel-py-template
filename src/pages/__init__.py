"""
Custom Page Objects Directory.

This is the designated space for your project-specific page objects.
By placing your page objects here, you can extend the core framework
(`sel_py_template.pages.base_page.BasePage`) with representations of your
actual application pages.

Here you should:
- Subclass `BasePage` for your specific pages.
- Define application-specific locators (using plain tuples or the UI `Element` wrappers).
- Implement methods representing user interactions on those pages.

WHAT BELONGS HERE:
  - Page Object Model (POM) classes for each page/screen in your app

WHAT DOES NOT BELONG HERE:
  - Fixtures        → tests/fixtures/
  - Test files      → tests/
  - Shared helpers  → create a src/helpers/ package (also user-owned)


Example usage with raw locators:

    from selenium.webdriver.common.by import By
    from sel_py_template.pages.base_page import BasePage

    class LoginPageRaw(BasePage):
        USERNAME_INPUT = (By.ID, "username")
        SUBMIT_BUTTON = (By.ID, "submit")

        def login(self, username):
            self.send_keys(self.USERNAME_INPUT, username)
            self.click(self.SUBMIT_BUTTON)

Example usage with UI Element descriptors (recommended):

    from selenium.webdriver.common.by import By
    from sel_py_template.pages.base_page import BasePage
    from sel_py_template.ui.elements import Element, ElementType

    class LoginPage(BasePage):
        # 1. Define rich UI elements
        username_input = Element("username", ElementType.TEXT_INPUT, by=By.ID)
        submit_button = Element("submit", ElementType.BUTTON, by=By.ID)

        # 2. Encapsulate actions with fluent element interactions
        def login(self, username):
            self.username_input.type(username)
            self.submit_button.click()
"""
