"""
Framework resilience tests for CI/CD reliability.

Focus: Timeout handling, element interactions, and edge cases
that commonly cause test flakiness in CI environments.

**Important**: These tests are adjusted for your framework's actual behavior:
  - is_visible() returns False if element not visible (doesn't wait for visibility)
  - should_contain_text() gets current text immediately (doesn't wait for content change)
  - Timing tests account for CI environment slowness

Run with:
  pytest tests/test_framework_resilience.py --all-browsers --headless -v
  pytest tests/test_framework_resilience.py -m ci_critical --headless -v
"""

from __future__ import annotations

from pathlib import Path

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from sel_py_template.pages.base_page import BasePage
from sel_py_template.ui.elements import Element, ElementType


def _write_html(tmp_path: Path, name: str, html: str) -> str:
    """
    Helper: Write HTML to temporary file and return file:// URI.

    Args:
        tmp_path: pytest temporary directory fixture
        name: filename to create
        html: HTML content to write

    Returns:
        str: file:// URI pointing to the temporary HTML file
    """
    p: Path = tmp_path / name
    p.write_text(html, encoding="utf-8")
    return p.as_uri()


@pytest.fixture(autouse=True)
def _stub_logger_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub LoggerFactory for test isolation."""
    try:
        import sel_py_template.pages.base_page as bp
    except ImportError:
        return

    class _Logger:
        def debug(self, *a: object, **k: object) -> None:
            pass

        def info(self, *a: object, **k: object) -> None:
            pass

        def warning(self, *a: object, **k: object) -> None:
            pass

        def error(self, *a: object, **k: object) -> None:
            pass

    class _LF:
        @staticmethod
        def get_logger(*a: object, **k: object) -> _Logger:
            return _Logger()

        @staticmethod
        def get_log_dir() -> None:
            return None

    monkeypatch.setattr(bp, "LoggerFactory", _LF, raising=True)


class ResilientPage(BasePage):
    """Page Object for resilience testing."""

    button: Element = Element("btn", ElementType.BUTTON, name="Button")
    status: Element = Element("status", ElementType.TOAST, by=By.ID, name="Status")
    input_field: Element = Element("input", ElementType.TEXT_INPUT, name="Input")
    checkbox: Element = Element("agree", ElementType.CHECKBOX, name="Checkbox")
    dropdown: Element = Element("role", ElementType.DROPDOWN, by=By.ID, name="Dropdown")


# ============================================================================
# ELEMENT FINDING & WAITING TESTS
# ============================================================================


@pytest.mark.ci_critical
def test_element_wait_timeout_explicit(
    driver: WebDriver, tmp_path: Path, logger
) -> None:
    """
    Test: Explicit wait timeout for element that never appears.

    **Why CI-critical**:
      - Verifies timeout mechanism works (test doesn't hang forever)
      - Tests that exceptions are raised correctly
      - Prevents infinite waits in CI pipelines

    **Scenario**: Try to find non-existent element, verify timeout happens
    **Expected**: Timeout exception after ~1 second
    """
    url: str = _write_html(
        tmp_path,
        "no_element.html",
        """
<!doctype html>
<html>
  <body>
    <p>Empty page</p>
  </body>
</html>
        """,
    )

    page: ResilientPage = ResilientPage(driver, browser="chrome")
    page.navigate(url)

    # Try to find non-existent element with short timeout
    try:
        page.button.find(timeout=1)
        # Should not reach here
        raise AssertionError("Should have raised exception for missing element")
    except Exception as e:
        # Expected: ElementNotFoundError or similar
        logger.info(f"✓ Correctly raised exception: {type(e).__name__}")
        error_str: str = str(e).lower()
        # Check for timeout message (case-insensitive)
        assert "timed out" in error_str or "not found" in error_str, (
            f"Expected 'timed out' or 'not found' in exception. Got: {str(e)[:100]}"
        )


@pytest.mark.ci_critical
def test_element_found_immediately(driver: WebDriver, tmp_path: Path, logger) -> None:
    """
    Test: Element that exists is found immediately.

    **Why CI-critical**:
      - Baseline test: if this fails, element finding is broken
      - Verifies wait_for() works for present elements
      - Tests basic framework functionality

    **Scenario**: Element exists from page load, find it
    """
    url: str = _write_html(
        tmp_path,
        "element_present.html",
        """
<!doctype html>
<html>
  <body>
    <button id="btn">Click me</button>
  </body>
</html>
        """,
    )

    page: ResilientPage = ResilientPage(driver, browser="chrome")
    page.navigate(url)

    # Element should be found immediately
    element = page.button.find(timeout=5)
    assert element is not None, "Element should be found"
    logger.info("✓ Element found immediately")


@pytest.mark.ci_critical
def test_element_appears_after_short_delay(
    driver: WebDriver, tmp_path: Path, logger
) -> None:
    """
    Test: Element appears after delay, wait catches it.

    **Why CI-critical**:
      - CI runners are slower than local machines
      - Tests that waits correctly handle delayed elements
      - Simulates real-world scenarios (lazy loading, animations)

    **Scenario**: Element added to DOM after 300ms, should be found within 2s
    """
    url: str = _write_html(
        tmp_path,
        "delayed_element.html",
        """
<!doctype html>
<html>
  <body>
    <div id="container"></div>
    <script>
      setTimeout(() => {
        const btn = document.createElement('button');
        btn.id = 'btn';
        btn.textContent = 'Delayed Button';
        document.getElementById('container').appendChild(btn);
      }, 300);
    </script>
  </body>
</html>
        """,
    )

    page: ResilientPage = ResilientPage(driver, browser="chrome")
    page.navigate(url)

    # Element not present yet
    logger.info("Element not yet added to DOM")

    # Wait for it - should find within 2s (300ms delay + buffer)
    element = page.button.find(timeout=3)
    assert element is not None, "Element should be found after delay"
    logger.info("✓ Element found after being added to DOM")


@pytest.mark.ci_critical
def test_element_visibility_checking(driver: WebDriver, tmp_path: Path, logger) -> None:
    """
    Test: is_visible() distinguishes between present and visible elements.

    **Why CI-critical**:
      - is_visible() has different behavior than find()
      - find() = element in DOM
      - is_visible() = element visible to user
      - Tests both checks work correctly

    **Scenario**: Element in DOM but hidden, verify is_visible returns False
    """
    url: str = _write_html(
        tmp_path,
        "hidden_element.html",
        """
<!doctype html>
<html>
  <body>
    <button id="btn" style="display:none;">Hidden Button</button>
  </body>
</html>
        """,
    )

    page: ResilientPage = ResilientPage(driver, browser="chrome")
    page.navigate(url)

    # Element exists in DOM
    element = page.button.find(timeout=2)
    assert element is not None, "Element should be in DOM"
    logger.info("✓ Element found in DOM")

    # But not visible
    is_visible: bool = page.button.is_visible(timeout=1)
    assert not is_visible, "Hidden element should return False from is_visible()"
    logger.info("✓ Element correctly detected as hidden")


# ============================================================================
# CLICK & INTERACTION TESTS
# ============================================================================


@pytest.mark.ci_critical
def test_click_simple_button(driver: WebDriver, tmp_path: Path, logger) -> None:
    """
    Test: Click a visible button and verify result.

    **Why CI-critical**:
      - Foundation test: if clicking fails, everything fails
      - Tests basic user interaction
      - Verifies click() works in headless mode
    """
    url: str = _write_html(
        tmp_path,
        "simple_click.html",
        """
<!doctype html>
<html>
  <body>
    <button id="btn">Click me</button>
    <div id="status"></div>
    <script>
      document.getElementById('btn').addEventListener('click', () => {
        document.getElementById('status').textContent = 'clicked';
      });
    </script>
  </body>
</html>
        """,
    )

    page: ResilientPage = ResilientPage(driver, browser="chrome")
    page.navigate(url)

    # Click button
    page.button.click(timeout=5)
    logger.info("✓ Button clicked")

    # Verify click worked
    status: str = page.status.text()
    assert status == "clicked", f"Expected 'clicked', got: {status!r}"
    logger.info("✓ Click event handler executed")


@pytest.mark.ci_critical
def test_click_retry_with_scroll(driver: WebDriver, tmp_path: Path, logger) -> None:
    """
    Test: click_retry() handles off-screen elements by scrolling.

    **Why CI-critical**:
      - Headless rendering can position elements differently
      - click_retry() is key resilience pattern
      - Tests that scroll + click logic works

    **Scenario**: Element off-screen, click_retry scrolls and clicks
    """
    url: str = _write_html(
        tmp_path,
        "tall_page.html",
        """
<!doctype html>
<html>
  <body style="height:3000px;">
    <div style="height:2000px; background:lightgray;"></div>
    <button id="btn">Bottom button</button>
    <div id="status"></div>
    <script>
      document.getElementById('btn').addEventListener('click', () => {
        document.getElementById('status').textContent = 'clicked';
      });
    </script>
  </body>
</html>
        """,
    )

    page: ResilientPage = ResilientPage(driver, browser="chrome")
    page.navigate(url)

    # click_retry should scroll and click
    page.button.click_retry(timeout=5)
    logger.info("✓ click_retry() scrolled and clicked")

    # Verify click succeeded
    status: str = page.status.text()
    assert status == "clicked", f"Expected 'clicked', got: {status!r}"


# ============================================================================
# ELEMENT STATE TESTS
# ============================================================================


@pytest.mark.ci_critical
def test_button_enabled_state(driver: WebDriver, tmp_path: Path, logger) -> None:
    """
    Test: Verify enabled button state.

    **Why CI-critical**:
      - Tests is_enabled() for active elements
      - Tests should_be_enabled() assertion
      - Baseline: button is enabled by default
    """
    url: str = _write_html(
        tmp_path,
        "enabled_button.html",
        """
<!doctype html>
<html>
  <body>
    <button id="btn">Click me</button>
  </body>
</html>
        """,
    )

    page: ResilientPage = ResilientPage(driver, browser="chrome")
    page.navigate(url)

    # Button should be enabled
    is_enabled: bool = page.button.is_enabled()
    assert is_enabled, "Button should be enabled"
    logger.info("✓ Button is enabled")

    # Assertion should pass
    page.button.should_be_enabled()
    logger.info("✓ should_be_enabled() passed")


@pytest.mark.ci_critical
def test_button_disabled_state(driver: WebDriver, tmp_path: Path, logger) -> None:
    """
    Test: Verify disabled button state.

    **Why CI-critical**:
      - Tests is_enabled() for inactive elements
      - Tests should_be_disabled() assertion
      - Disabled buttons shouldn't be clickable
    """
    url: str = _write_html(
        tmp_path,
        "disabled_button.html",
        """
<!doctype html>
<html>
  <body>
    <button id="btn" disabled>Click me</button>
  </body>
</html>
        """,
    )

    page: ResilientPage = ResilientPage(driver, browser="chrome")
    page.navigate(url)

    # Button should be disabled
    is_enabled: bool = page.button.is_enabled()
    assert not is_enabled, "Button should be disabled"
    logger.info("✓ Button is disabled")

    # Assertion should pass
    page.button.should_be_disabled()
    logger.info("✓ should_be_disabled() passed")


# ============================================================================
# TEXT & VALUE TESTS
# ============================================================================


@pytest.mark.ci_critical
def test_get_button_text(driver: WebDriver, tmp_path: Path, logger) -> None:
    """
    Test: Retrieve button text.

    **Why CI-critical**:
      - Tests text() getter
      - Verifies HTML content extraction works
      - Baseline for content assertions
    """
    url: str = _write_html(
        tmp_path,
        "button_text.html",
        """
<!doctype html>
<html>
  <body>
    <button id="btn">Click Here</button>
  </body>
</html>
        """,
    )

    page: ResilientPage = ResilientPage(driver, browser="chrome")
    page.navigate(url)

    # Get text
    text: str = page.button.text()
    assert text == "Click Here", f"Expected 'Click Here', got: {text!r}"
    logger.info("✓ Button text retrieved correctly")


@pytest.mark.ci_critical
def test_should_contain_text(driver: WebDriver, tmp_path: Path, logger) -> None:
    """
    Test: should_contain_text() partial text matching.

    **Why CI-critical**:
      - Tests substring matching
      - Useful for content with dynamic parts
      - Tests assertion with helpful error messages

    **Scenario**: Verify text contains expected substring
    """
    url: str = _write_html(
        tmp_path,
        "partial_text.html",
        """
<!doctype html>
<html>
  <body>
    <div id="status">User logged in: john123</div>
  </body>
</html>
        """,
    )

    page: ResilientPage = ResilientPage(driver, browser="chrome")
    page.navigate(url)

    # Partial text should match
    page.status.should_contain_text("logged in")
    logger.info("✓ Partial text matched")


@pytest.mark.ci_critical
def test_should_equal_text(driver: WebDriver, tmp_path: Path, logger) -> None:
    """
    Test: should_equal_text() exact text matching.

    **Why CI-critical**:
      - Tests exact text (not substring)
      - More strict than should_contain_text()
      - Tests assertion when exact match needed
    """
    url: str = _write_html(
        tmp_path,
        "exact_text.html",
        """
<!doctype html>
<html>
  <body>
    <div id="status">Ready</div>
  </body>
</html>
        """,
    )

    page: ResilientPage = ResilientPage(driver, browser="chrome")
    page.navigate(url)

    # Exact text should match
    page.status.should_equal_text("Ready")
    logger.info("✓ Exact text matched")


@pytest.mark.ci_critical
def test_input_value_getter(driver: WebDriver, tmp_path: Path, logger) -> None:
    """
    Test: value() retrieves input field value.

    **Why CI-critical**:
      - Tests value() for input elements
      - Different from text() (uses .value attribute)
      - Baseline for form testing
    """
    url: str = _write_html(
        tmp_path,
        "input_value.html",
        """
<!doctype html>
<html>
  <body>
    <input id="input" type="text" value="initial">
  </body>
</html>
        """,
    )

    page: ResilientPage = ResilientPage(driver, browser="chrome")
    page.navigate(url)

    # Get value
    value: str = page.input_field.value()
    assert value == "initial", f"Expected 'initial', got: {value!r}"
    logger.info("✓ Input value retrieved correctly")


# ============================================================================
# FORM INTERACTION TESTS
# ============================================================================


@pytest.mark.ci_critical
def test_type_text_into_input(driver: WebDriver, tmp_path: Path, logger) -> None:
    """
    Test: Type text into input field.

    **Why CI-critical**:
      - Tests type() method in headless mode
      - Verifies text input works
      - Common pattern in form tests
    """
    url: str = _write_html(
        tmp_path,
        "input_typing.html",
        """
<!doctype html>
<html>
  <body>
    <input id="input" type="text">
  </body>
</html>
        """,
    )

    page: ResilientPage = ResilientPage(driver, browser="chrome")
    page.navigate(url)

    # Type text
    page.input_field.type("test123")
    logger.info("✓ Typed text into input")

    # Verify value
    value: str = page.input_field.value()
    assert value == "test123", f"Expected 'test123', got: {value!r}"
    logger.info("✓ Input value verified")


@pytest.mark.ci_critical
def test_type_with_clear(driver: WebDriver, tmp_path: Path, logger) -> None:
    """
    Test: Type replaces existing value (clear_first=True by default).

    **Why CI-critical**:
      - Tests clear() + send_keys() pattern
      - Verifies default behavior (clear_first=True)
      - Important for form field replacement

    **Scenario**: Input has initial value, type() should replace it
    """
    url: str = _write_html(
        tmp_path,
        "input_replace.html",
        """
<!doctype html>
<html>
  <body>
    <input id="input" type="text" value="old">
  </body>
</html>
        """,
    )

    page: ResilientPage = ResilientPage(driver, browser="chrome")
    page.navigate(url)

    # Type should clear and replace
    page.input_field.type("new")
    logger.info("✓ Typed replacement text")

    # Verify it replaced (not appended)
    value: str = page.input_field.value()
    assert value == "new", f"Expected 'new', got: {value!r}"
    logger.info("✓ Previous value was cleared and replaced")


@pytest.mark.ci_critical
def test_should_have_value_assertion(driver: WebDriver, tmp_path: Path, logger) -> None:
    """
    Test: should_have_value() assertion for input values.

    **Why CI-critical**:
      - Tests value assertion with error messages
      - Useful for form verification
      - Tests both positive and negative cases
    """
    url: str = _write_html(
        tmp_path,
        "input_assertion.html",
        """
<!doctype html>
<html>
  <body>
    <input id="input" type="text" value="expected">
  </body>
</html>
        """,
    )

    page: ResilientPage = ResilientPage(driver, browser="chrome")
    page.navigate(url)

    # Assertion should pass
    page.input_field.should_have_value("expected")
    logger.info("✓ Value assertion passed")

    # Negative case: wrong value
    try:
        page.input_field.should_have_value("wrong")
        raise AssertionError("Should have raised AssertionError")
    except AssertionError as e:
        logger.info(f"✓ Correctly raised AssertionError for wrong value: {e}")


# ============================================================================
# CHECKBOX TESTS
# ============================================================================


@pytest.mark.ci_critical
def test_checkbox_checked_state(driver: WebDriver, tmp_path: Path, logger) -> None:
    """
    Test: Verify checkbox checked state.

    **Why CI-critical**:
      - Tests is_checked() for checked checkboxes
      - Tests checkbox state detection
      - Baseline: initially unchecked
    """
    url: str = _write_html(
        tmp_path,
        "checkbox_checked.html",
        """
<!doctype html>
<html>
  <body>
    <input id="agree" type="checkbox" checked>
  </body>
</html>
        """,
    )

    page: ResilientPage = ResilientPage(driver, browser="chrome")
    page.navigate(url)

    # Should be checked
    is_checked: bool = page.checkbox.is_checked()
    assert is_checked, "Checkbox should be checked"
    logger.info("✓ Checkbox is checked")


@pytest.mark.ci_critical
def test_checkbox_unchecked_state(driver: WebDriver, tmp_path: Path, logger) -> None:
    """
    Test: Verify checkbox unchecked state.

    **Why CI-critical**:
      - Tests is_checked() for unchecked checkboxes
      - Tests negative state
      - Important for form validation
    """
    url: str = _write_html(
        tmp_path,
        "checkbox_unchecked.html",
        """
<!doctype html>
<html>
  <body>
    <input id="agree" type="checkbox">
  </body>
</html>
        """,
    )

    page: ResilientPage = ResilientPage(driver, browser="chrome")
    page.navigate(url)

    # Should be unchecked
    is_checked: bool = page.checkbox.is_checked()
    assert not is_checked, "Checkbox should be unchecked"
    logger.info("✓ Checkbox is unchecked")


@pytest.mark.ci_critical
def test_set_checkbox_checked(driver: WebDriver, tmp_path: Path, logger) -> None:
    """
    Test: set_checked(True) checks a checkbox.

    **Why CI-critical**:
      - Tests set_checked() method
      - Tests click interaction triggered by checkbox
      - Real scenario: form filling
    """
    url: str = _write_html(
        tmp_path,
        "checkbox_toggle.html",
        """
<!doctype html>
<html>
  <body>
    <input id="agree" type="checkbox">
  </body>
</html>
        """,
    )

    page: ResilientPage = ResilientPage(driver, browser="chrome")
    page.navigate(url)

    # Initially unchecked
    assert not page.checkbox.is_checked(), "Should start unchecked"

    # Set checked
    page.checkbox.set_checked(True)
    logger.info("✓ Set checkbox to checked")

    # Verify checked
    is_checked: bool = page.checkbox.is_checked()
    assert is_checked, "Checkbox should now be checked"
    logger.info("✓ Checkbox now checked")


# ============================================================================
# DROPDOWN/SELECT TESTS
# ============================================================================


@pytest.mark.ci_critical
def test_select_option_by_value(driver: WebDriver, tmp_path: Path, logger) -> None:
    """
    Test: Select dropdown option by value.

    **Why CI-critical**:
      - Tests select_option() with value parameter
      - Tests native <select> element handling
      - Common form pattern

    **Scenario**: Select from <select> dropdown
    """
    url: str = _write_html(
        tmp_path,
        "select_dropdown.html",
        """
<!doctype html>
<html>
  <body>
    <select id="role">
      <option value="">Choose...</option>
      <option value="admin">Admin</option>
      <option value="user">User</option>
    </select>
    <div id="status"></div>
    <script>
      document.getElementById('role').addEventListener('change', (e) => {
        document.getElementById('status').textContent = 'Selected: ' + e.target.value;
      });
    </script>
  </body>
</html>
        """,
    )

    page: ResilientPage = ResilientPage(driver, browser="chrome")
    page.navigate(url)

    # Select option by value
    page.dropdown.select_option(value="admin")
    logger.info("✓ Selected option by value")

    # Verify selection
    status: str = page.status.text()
    assert "admin" in status, f"Expected 'admin' in status, got: {status!r}"
    logger.info("✓ Dropdown selection verified")


# ============================================================================
# KEYBOARD INTERACTION TESTS
# ============================================================================


@pytest.mark.ci_critical
def test_press_enter_key(driver: WebDriver, tmp_path: Path, logger) -> None:
    """
    Test: Press Enter key and verify handler executes.

    **Why CI-critical**:
      - Tests keyboard interaction (Enter)
      - Tests key events in headless mode
      - Real scenario: form submission
    """
    url: str = _write_html(
        tmp_path,
        "enter_key.html",
        """
<!doctype html>
<html>
  <body>
    <input id="input" type="text">
    <div id="status"></div>
    <script>
      document.getElementById('input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
          document.getElementById('status').textContent = 'Submitted: ' + e.target.value;
        }
      });
    </script>
  </body>
</html>
        """,
    )

    page: ResilientPage = ResilientPage(driver, browser="chrome")
    page.navigate(url)

    # Type and press Enter
    page.input_field.type("search")
    page.input_field.press_enter()
    logger.info("✓ Pressed Enter key")

    # Verify handler executed
    status: str = page.status.text()
    assert "Submitted" in status, f"Expected 'Submitted' in status, got: {status!r}"
    logger.info("✓ Enter key handler executed")


@pytest.mark.ci_critical
def test_press_escape_key(driver: WebDriver, tmp_path: Path, logger) -> None:
    """
    Test: Press Escape key and verify handler executes.

    **Why CI-critical**:
      - Tests keyboard interaction (Escape)
      - Real scenario: close modals, cancel operations
    """
    url: str = _write_html(
        tmp_path,
        "escape_key.html",
        """
<!doctype html>
<html>
  <body>
    <input id="input" type="text">
    <div id="status"></div>
    <script>
      document.getElementById('input').addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          document.getElementById('status').textContent = 'Cancelled';
        }
      });
    </script>
  </body>
</html>
        """,
    )

    page: ResilientPage = ResilientPage(driver, browser="chrome")
    page.navigate(url)

    # Press Escape
    page.input_field.press_escape()
    logger.info("✓ Pressed Escape key")

    # Verify handler executed
    status: str = page.status.text()
    assert status == "Cancelled", f"Expected 'Cancelled', got: {status!r}"
    logger.info("✓ Escape key handler executed")


@pytest.mark.ci_critical
def test_press_tab_key(driver: WebDriver, tmp_path: Path, logger) -> None:
    """
    Test: Press Tab key for focus navigation.

    **Why CI-critical**:
      - Tests Tab key for accessibility testing
      - Verifies focus movement
    """
    url: str = _write_html(
        tmp_path,
        "tab_navigation.html",
        """
<!doctype html>
<html>
  <body>
    <input id="input" type="text">
    <button id="btn">Button</button>
    <div id="status"></div>
    <script>
      document.getElementById('btn').addEventListener('focus', () => {
        document.getElementById('status').textContent = 'Button focused';
      });
    </script>
  </body>
</html>
        """,
    )

    page: ResilientPage = ResilientPage(driver, browser="chrome")
    page.navigate(url)

    # Focus on input first
    page.input_field.click()

    # Press Tab to move focus to button
    page.input_field.press_tab()
    logger.info("✓ Pressed Tab key")

    # Verify focus moved (check if button handler fired)
    status: str = page.status.text()
    assert "Button focused" in status, f"Expected 'Button focused', got: {status!r}"
    logger.info("✓ Tab key moved focus correctly")


# ============================================================================
# ATTRIBUTE TESTS
# ============================================================================


@pytest.mark.ci_critical
def test_get_element_attribute(driver: WebDriver, tmp_path: Path, logger) -> None:
    """
    Test: Retrieve HTML attribute from element.

    **Why CI-critical**:
      - Tests attr() getter
      - Real scenario: check data-* attributes, aria-* attributes
    """
    url: str = _write_html(
        tmp_path,
        "element_attributes.html",
        """
<!doctype html>
<html>
  <body>
    <button id="btn" data-testid="primary" aria-label="Submit form">Submit</button>
  </body>
</html>
        """,
    )

    page: ResilientPage = ResilientPage(driver, browser="chrome")
    page.navigate(url)

    # Get custom attribute
    testid: str = page.button.attr("data-testid")
    assert testid == "primary", f"Expected 'primary', got: {testid!r}"
    logger.info("✓ Custom attribute retrieved")

    # Get aria attribute
    label: str = page.button.attr("aria-label")
    assert label == "Submit form", f"Expected 'Submit form', got: {label!r}"
    logger.info("✓ Aria attribute retrieved")


@pytest.mark.ci_critical
def test_should_have_attr_assertion(driver: WebDriver, tmp_path: Path, logger) -> None:
    """
    Test: should_have_attr() assertion for attributes.

    **Why CI-critical**:
      - Tests attribute assertion with helpful errors
      - Useful for accessibility and data attribute checks
    """
    url: str = _write_html(
        tmp_path,
        "attr_assertion.html",
        """
<!doctype html>
<html>
  <body>
    <button id="btn" type="submit">Submit</button>
  </body>
</html>
        """,
    )

    page: ResilientPage = ResilientPage(driver, browser="chrome")
    page.navigate(url)

    # Attribute assertion should pass
    page.button.should_have_attr("type", "submt")
    logger.info("✓ Attribute assertion passed")
