# Selenium Page Objects with Bound Elements

A lightweight, opinionated Selenium framework for Python that makes UI tests **readable, resilient, and hard to misuse**.

This project combines:
- A robust `BasePage` with safe waits and ActionChains interactions
- Declarative element definitions at the page level
- Driver-bound elements with fluent actions and built-in assertions

Designed for teams who want **clean tests**, **low flake**, and **minimal Selenium noise**.

---

## Features

- Explicit waits baked into every interaction
- ActionChains-based clicks (more reliable than `.click()`)
- Declarative element definitions (no locators in tests)
- Fluent assertions directly on elements
- Element-type–aware behavior (inputs, checkboxes, dropdowns, etc.)
- Clear, actionable errors when things fail

---

## Quick Start

### 1. Define a Page Object

```python
from selenium.webdriver.common.by import By
from pages.base_page import BasePage
from elements import Element, ElementType


class LoginPage(BasePage):
    username = Element("user-name", ElementType.TEXT_INPUT)
    password = Element("password", ElementType.TEXT_INPUT)
    login_button = Element("login-button", ElementType.BUTTON)

    def login(self, user: str, password: str) -> None:
        self.username.type(user)
        self.password.type(password)
        self.login_button.click()
```

---

### 2. Write a Test

```python
def test_successful_login(login_page):
    login_page.navigate("https://example.com/login")
    login_page.login("standard_user", "secret_sauce")

    login_page.login_button.should_be_disabled()
```

No raw `driver.find_element`, no manual waits, no brittle sleeps.

---

## Pytest Fixture Example

A simple fixture that creates and cleans up the page object:

```python
import pytest
from selenium import webdriver
from pages.login_page import LoginPage


@pytest.fixture
def login_page():
    driver = webdriver.Chrome()
    driver.maximize_window()

    page = LoginPage(driver, browser="chrome")

    yield page

    driver.quit()
```

You can extend this pattern for:
- multi-browser runs
- headless vs interactive modes
- logging and screenshots
- parallel execution (pytest-xdist)

---

## Element Definitions

Elements are declared once, at the class level:

```python
login_button = Element(
    value="login-button",
    element_type=ElementType.BUTTON,
    name="Login Button",
    timeout_s=10,
)
```

At runtime, these become **Bound Elements** that:
- are automatically tied to the page’s driver
- cache themselves per page instance
- expose safe, high-level interactions

---

## Common Interactions

### Clicking
```python
el.click()
el.click_retry()
el.double_click()
el.right_click()
```

### Typing & Keyboard
```python
el.type("hello")
el.press_enter()
el.press_escape()
```

### State & Visibility
```python
el.is_visible()
el.should_be_visible()
el.should_be_enabled()
el.should_be_disabled()
```

### Assertions
```python
el.should_contain_text("Success")
el.should_equal_text("Saved")
el.should_have_value("123")
el.should_have_attr("aria-disabled", "true")
```

Assertions live **on the element**, keeping tests expressive and consistent.

---

## Supported Element Types

```python
BUTTON, LINK, TEXT_INPUT, TEXTAREA, DROPDOWN,
CHECKBOX, RADIO, TOGGLE, TAB, MENU_ITEM,
MODAL, TOAST, PAGINATION
```

Element types enforce valid behavior:
- `.type()` only works for text inputs
- `.is_checked()` only works for checkables
- Native `<select>` dropdowns are handled automatically

---

## Error Handling Philosophy

- Selenium exceptions are wrapped in domain-specific errors
- Failures include element name, locator, and expected behavior
- Tests fail loudly and clearly—no silent flakiness

---

## Design Goals

- Readable tests
- Minimal Selenium leakage
- Strong defaults
- Easy extension
- Low flake rate

This framework is intentionally small but opinionated—designed to scale across teams without becoming magic.

---

## License

MIT (or internal-use license—adjust as needed)
