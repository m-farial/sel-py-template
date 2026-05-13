"""
Framework resilience tests for CI/CD reliability.

Focus: Timeout handling, element interactions, and edge cases
that commonly cause test flakiness in CI environments.

**Important**: These tests are adjusted for your framework's actual behavior:
  - is_visible() returns False if element not visible (doesn't wait for visibility)
  - should_contain_text() gets current text immediately (doesn't wait for content change)
  - Timing tests account for CI environment slowness

Run with:
  pytest template_tests/integration/test_framework_resilience.py --all-browsers --headless -v
  pytest template_tests/integration/test_framework_resilience.py -m ci_critical --headless -v
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from template_tests.integration.helpers import write_html

from sel_py_template.pages.base_page import BasePage
from sel_py_template.ui.elements import Element, ElementType

pytestmark = pytest.mark.integration


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
class TestElementFinding:
    """Tests for element finding, waiting, and visibility behaviour."""

    def test_element_wait_timeout_explicit(
        self, resilient_page: BasePage, tmp_path: Path, logger
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
        url: str = write_html(
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

        resilient_page.navigate(url)

        # Try to find non-existent element with short timeout
        with pytest.raises((TimeoutException, NoSuchElementException)) as exc_info:
            resilient_page.button.find(timeout=1)

        error_str: str = str(exc_info.value).lower()
        assert "timed out" in error_str or "not found" in error_str, (
            f"Expected 'timed out' or 'not found' in exception. Got: {str(exc_info.value)[:100]}"
        )
        logger.info(f"✓ Correctly raised exception: {type(exc_info.value).__name__}")

    def test_element_found_immediately(
        self, resilient_page: BasePage, tmp_path: Path, logger
    ) -> None:
        """
        Test: Element that exists is found immediately.

        **Why CI-critical**:
          - Baseline test: if this fails, element finding is broken
          - Verifies wait_for() works for present elements
          - Tests basic framework functionality

        **Scenario**: Element exists from page load, find it
        """
        url: str = write_html(
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

        resilient_page.navigate(url)

        # Element should be found immediately
        element = resilient_page.button.find(timeout=5)
        assert element is not None, "Element should be found"
        logger.info("✓ Element found immediately")

    def test_element_appears_after_short_delay(
        self, resilient_page: BasePage, tmp_path: Path, logger
    ) -> None:
        """
        Test: Element appears after delay, wait catches it.

        **Why CI-critical**:
          - CI runners are slower than local machines
          - Tests that waits correctly handle delayed elements
          - Simulates real-world scenarios (lazy loading, animations)

        **Scenario**: Element added to DOM after 300ms, should be found within 2s
        """
        url: str = write_html(
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

        resilient_page.navigate(url)

        # Element not present yet
        logger.info("Element not yet added to DOM")

        # Wait for it - should find within 2s (300ms delay + buffer)
        element = resilient_page.button.find(timeout=3)
        assert element is not None, "Element should be found after delay"
        logger.info("✓ Element found after being added to DOM")

    def test_element_visibility_checking(
        self, resilient_page: BasePage, tmp_path: Path, logger
    ) -> None:
        """
        Test: is_visible() distinguishes between present and visible elements.

        **Why CI-critical**:
          - is_visible() has different behavior than find()
          - find() = element in DOM
          - is_visible() = element visible to user
          - Tests both checks work correctly

        **Scenario**: Element in DOM but hidden, verify is_visible returns False
        """
        url: str = write_html(
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

        resilient_page.navigate(url)

        # Element exists in DOM
        element = resilient_page.button.find(timeout=2)
        assert element is not None, "Element should be in DOM"
        logger.info("✓ Element found in DOM")

        # But not visible
        is_visible: bool = resilient_page.button.is_visible(timeout=1)
        assert not is_visible, "Hidden element should return False from is_visible()"
        logger.info("✓ Element correctly detected as hidden")


# ============================================================================
# CLICK & INTERACTION TESTS
# ============================================================================


@pytest.mark.ci_critical
class TestClickInteractions:
    """Tests for click interactions and scroll-to-click resilience."""

    def test_click_simple_button(
        self, resilient_page: BasePage, tmp_path: Path, logger
    ) -> None:
        """
        Test: Click a visible button and verify result.

        **Why CI-critical**:
          - Foundation test: if clicking fails, everything fails
          - Tests basic user interaction
          - Verifies click() works in headless mode
        """
        url: str = write_html(
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

        resilient_page.navigate(url)

        # Click button
        resilient_page.button.click(timeout=5)
        logger.info("✓ Button clicked")

        # Verify click worked
        status: str = resilient_page.status.text()
        assert status == "clicked", f"Expected 'clicked', got: {status!r}"
        logger.info("✓ Click event handler executed")

    def test_click_retry_with_scroll(
        self, resilient_page: BasePage, tmp_path: Path, logger
    ) -> None:
        """
        Test: click_retry() handles off-screen elements by scrolling.

        **Why CI-critical**:
          - Headless rendering can position elements differently
          - click_retry() is key resilience pattern
          - Tests that scroll + click logic works

        **Scenario**: Element off-screen, click_retry scrolls and clicks
        """
        url: str = write_html(
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

        resilient_page.navigate(url)

        # click_retry should scroll and click
        resilient_page.button.click_retry(timeout=5)
        logger.info("✓ click_retry() scrolled and clicked")

        # Verify click succeeded
        status: str = resilient_page.status.text()
        assert status == "clicked", f"Expected 'clicked', got: {status!r}"


# ============================================================================
# ELEMENT STATE TESTS
# ============================================================================


@pytest.mark.ci_critical
class TestElementState:
    """Tests for element enabled/disabled state detection.

    Parametrize notes
    -----------------
    ``test_button_state`` is parametrized over enabled and disabled cases.
    Each case provides:
      - ``html``              : the HTML page string to write to disk
      - ``expected_enabled``  : the boolean is_enabled() should return
      - ``assert_method_name``: the name of the assertion method to call on the
                                element (``should_be_enabled`` or
                                ``should_be_disabled``).

    Inside the test body, ``getattr(resilient_page.button, assert_method_name)`` looks up
    the method by name at runtime and returns it as a callable — a function
    stored in a variable that can be invoked with ``()``.  This avoids an
    if/else branch and keeps the parametrize table the single source of truth
    for which assertion belongs to which case.
    """

    @pytest.mark.parametrize(
        "html, expected_enabled, assert_method_name, label",
        [
            pytest.param(
                """
<!doctype html>
<html>
  <body>
    <button id="btn">Click me</button>
  </body>
</html>
                """,
                True,
                "should_be_enabled",
                "enabled",
                id="enabled",
            ),
            pytest.param(
                """
<!doctype html>
<html>
  <body>
    <button id="btn" disabled>Click me</button>
  </body>
</html>
                """,
                False,
                "should_be_disabled",
                "disabled",
                id="disabled",
            ),
        ],
    )
    def test_button_state(
        self,
        resilient_page: BasePage,
        tmp_path: Path,
        logger,
        html: str,
        expected_enabled: bool,
        assert_method_name: str,
        label: str,
    ) -> None:
        """
        Test: Verify button enabled/disabled state.

        **Why CI-critical**:
          - Tests is_enabled() for both active and inactive elements
          - Tests should_be_enabled() and should_be_disabled() assertions
          - Disabled buttons shouldn't be clickable

        Parametrized over: enabled button, disabled button.
        """
        url: str = write_html(tmp_path, f"{label}_button.html", html)

        resilient_page.navigate(url)

        is_enabled: bool = resilient_page.button.is_enabled()
        assert is_enabled == expected_enabled, (
            f"Expected is_enabled()={expected_enabled} for {label} button, got {is_enabled}"
        )
        logger.info(f"✓ Button is {label}")

        # Retrieve and call e.g. resilient_page.button.should_be_enabled() at runtime.
        assert_method: Callable[[], None] = getattr(
            resilient_page.button, assert_method_name
        )
        assert_method()
        logger.info(f"✓ {assert_method_name}() passed")


# ============================================================================
# TEXT & VALUE TESTS
# ============================================================================


@pytest.mark.ci_critical
class TestTextAndValues:
    """Tests for text retrieval and value assertions on elements.

    Parametrize notes
    -----------------
    ``test_text_assertion_methods`` is parametrized over the two text assertion
    methods.  Both write a page with a ``#status`` div and call one assertion
    method on it — the only differences are the div's content, the method name,
    and the argument passed to it.

    ``test_get_button_text`` and ``test_input_value_getter`` each target a
    different page element (``button`` vs ``input_field``) and use different
    getters (``text()`` vs ``value()``), so merging them would require
    conditional logic that obscures what is actually being tested.  They remain
    as standalone tests.
    """

    def test_get_button_text(
        self, resilient_page: BasePage, tmp_path: Path, logger
    ) -> None:
        """
        Test: Retrieve button text.

        **Why CI-critical**:
          - Tests text() getter
          - Verifies HTML content extraction works
          - Baseline for content assertions
        """
        url: str = write_html(
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

        resilient_page.navigate(url)

        # Get text
        text: str = resilient_page.button.text()
        assert text == "Click Here", f"Expected 'Click Here', got: {text!r}"
        logger.info("✓ Button text retrieved correctly")

    @pytest.mark.parametrize(
        "status_text, assert_method_name, assert_arg",
        [
            pytest.param(
                "User logged in: john123",
                "should_contain_text",
                "logged in",
                id="contains",
            ),
            pytest.param(
                "Ready",
                "should_equal_text",
                "Ready",
                id="equals",
            ),
        ],
    )
    def test_text_assertion_methods(
        self,
        resilient_page: BasePage,
        tmp_path: Path,
        logger,
        status_text: str,
        assert_method_name: str,
        assert_arg: str,
    ) -> None:
        """
        Test: should_contain_text() and should_equal_text() assertion methods.

        **Why CI-critical**:
          - should_contain_text() tests substring matching for dynamic content
          - should_equal_text() tests strict matching when exact text is required
          - Both produce helpful assertion error messages

        Parametrized over: partial match (contains), exact match (equals).
        """
        url: str = write_html(
            tmp_path,
            f"text_{assert_method_name}.html",
            f"""
<!doctype html>
<html>
  <body>
    <div id="status">{status_text}</div>
  </body>
</html>
            """,
        )

        resilient_page.navigate(url)

        assert_method: Callable[[str], None] = getattr(
            resilient_page.status, assert_method_name
        )
        assert_method(assert_arg)
        logger.info(f"✓ {assert_method_name}({assert_arg!r}) passed")

    def test_input_value_getter(
        self, resilient_page: BasePage, tmp_path: Path, logger
    ) -> None:
        """
        Test: value() retrieves input field value.

        **Why CI-critical**:
          - Tests value() for input elements
          - Different from text() (uses .value attribute)
          - Baseline for form testing
        """
        url: str = write_html(
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

        resilient_page.navigate(url)

        # Get value
        value: str = resilient_page.input_field.value()
        assert value == "initial", f"Expected 'initial', got: {value!r}"
        logger.info("✓ Input value retrieved correctly")


# ============================================================================
# FORM INTERACTION TESTS
# ============================================================================


@pytest.mark.ci_critical
class TestFormInteractions:
    """Tests for typing, clearing, and value assertions on form inputs.

    Parametrize notes
    -----------------
    ``test_type_into_input`` is parametrized over two typing scenarios.  Both
    write an HTML page with an ``<input>``, call ``type()``, and assert the
    resulting ``value()``.  The only differences are whether the input starts
    with an existing value (testing the clear-first behaviour) and what text
    is typed.

    ``test_should_have_value_assertion`` tests both the positive and negative
    case of ``should_have_value()`` within a single body.  Splitting it into
    two parametrized cases would mean the negative branch (the ``try/except``)
    would need to be expressed differently for each, adding complexity without
    reducing duplication.  It stays as a standalone test.
    """

    @pytest.mark.parametrize(
        "initial_value_attr, typed_text, expected_value",
        [
            pytest.param(
                "",
                "test123",
                "test123",
                id="type_into_empty",
            ),
            pytest.param(
                'value="old"',
                "new",
                "new",
                id="type_replaces_existing",
            ),
        ],
    )
    def test_type_into_input(
        self,
        resilient_page: BasePage,
        tmp_path: Path,
        logger,
        initial_value_attr: str,
        typed_text: str,
        expected_value: str,
    ) -> None:
        """
        Test: type() writes text into an input; clear_first=True is the default.

        **Why CI-critical**:
          - Tests type() method in headless mode
          - Verifies text input works on empty and pre-filled fields
          - Verifies clear() + send_keys() pattern (clear_first=True default)

        Parametrized over: empty input, input with pre-existing value.
        """
        url: str = write_html(
            tmp_path,
            "input_typing.html",
            f"""
<!doctype html>
<html>
  <body>
    <input id="input" type="text" {initial_value_attr}>
  </body>
</html>
            """,
        )

        resilient_page.navigate(url)

        resilient_page.input_field.type(typed_text)
        logger.info(f"✓ Typed {typed_text!r} into input")

        value: str = resilient_page.input_field.value()
        assert value == expected_value, f"Expected {expected_value!r}, got: {value!r}"
        logger.info(f"✓ Input value is {expected_value!r} as expected")

    def test_should_have_value_assertion(
        self, resilient_page: BasePage, tmp_path: Path, logger
    ) -> None:
        """
        Test: should_have_value() assertion for input values.

        **Why CI-critical**:
          - Tests value assertion with error messages
          - Useful for form verification
          - Tests both positive and negative cases
        """
        url: str = write_html(
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

        resilient_page.navigate(url)

        # Assertion should pass
        resilient_page.input_field.should_have_value("expected")
        logger.info("✓ Value assertion passed")

        # Negative case: wrong value
        try:
            resilient_page.input_field.should_have_value("wrong")
        except AssertionError as e:
            logger.info(f"✓ Correctly raised AssertionError for wrong value: {e}")
        else:
            raise AssertionError("Expected should_have_value('wrong') to raise AssertionError")


# ============================================================================
# CHECKBOX TESTS
# ============================================================================


@pytest.mark.ci_critical
class TestCheckboxInteractions:
    """Tests for checkbox state detection and toggling.

    Parametrize notes
    -----------------
    ``test_checkbox_initial_state`` is parametrized over the checked and
    unchecked cases.  Both render a checkbox with or without the ``checked``
    HTML attribute and assert the value returned by ``is_checked()``.

    ``test_set_checkbox_checked`` performs an interaction (toggling state) and
    verifies a before/after transition — structurally different from the state
    detection cases, so it remains a standalone test.
    """

    @pytest.mark.parametrize(
        "checked_attr, expected_checked",
        [
            pytest.param("checked", True, id="initially_checked"),
            pytest.param("", False, id="initially_unchecked"),
        ],
    )
    def test_checkbox_initial_state(
        self,
        resilient_page: BasePage,
        tmp_path: Path,
        logger,
        checked_attr: str,
        expected_checked: bool,
    ) -> None:
        """
        Test: is_checked() reflects the initial HTML state of the checkbox.

        **Why CI-critical**:
          - Tests is_checked() for both checked and unchecked initial states
          - Baseline for form validation and conditional logic

        Parametrized over: initially checked, initially unchecked.
        """
        url: str = write_html(
            tmp_path,
            "checkbox_state.html",
            f"""
<!doctype html>
<html>
  <body>
    <input id="agree" type="checkbox" {checked_attr}>
  </body>
</html>
            """,
        )

        resilient_page.navigate(url)

        is_checked: bool = resilient_page.checkbox.is_checked()
        assert is_checked == expected_checked, (
            f"Expected is_checked()={expected_checked}, got {is_checked}"
        )
        state_label: str = "checked" if expected_checked else "unchecked"
        logger.info(f"✓ Checkbox is {state_label}")

    def test_set_checkbox_checked(
        self, resilient_page: BasePage, tmp_path: Path, logger
    ) -> None:
        """
        Test: set_checked(True) checks a checkbox.

        **Why CI-critical**:
          - Tests set_checked() method
          - Tests click interaction triggered by checkbox
          - Real scenario: form filling
        """
        url: str = write_html(
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

        resilient_page.navigate(url)

        # Initially unchecked
        assert not resilient_page.checkbox.is_checked(), "Should start unchecked"

        # Set checked
        resilient_page.checkbox.set_checked(True)
        logger.info("✓ Set checkbox to checked")

        # Verify checked
        is_checked: bool = resilient_page.checkbox.is_checked()
        assert is_checked, "Checkbox should now be checked"
        logger.info("✓ Checkbox now checked")


# ============================================================================
# DROPDOWN/SELECT TESTS
# ============================================================================


@pytest.mark.ci_critical
class TestDropdownInteractions:
    """Tests for native <select> dropdown option selection."""

    def test_select_option_by_value(
        self, resilient_page: BasePage, tmp_path: Path, logger
    ) -> None:
        """
        Test: Select dropdown option by value.

        **Why CI-critical**:
          - Tests select_option() with value parameter
          - Tests native <select> element handling
          - Common form pattern

        **Scenario**: Select from <select> dropdown
        """
        url: str = write_html(
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

        resilient_page.navigate(url)

        # Select option by value
        resilient_page.dropdown.select_option(value="admin")
        logger.info("✓ Selected option by value")

        # Verify selection
        status: str = resilient_page.status.text()
        assert "admin" in status, f"Expected 'admin' in status, got: {status!r}"
        logger.info("✓ Dropdown selection verified")


# ============================================================================
# KEYBOARD INTERACTION TESTS
# ============================================================================


@pytest.mark.ci_critical
class TestKeyboardInteractions:
    """Tests for keyboard key presses (Enter, Escape, Tab).

    Parametrize notes
    -----------------
    ``test_key_press`` is parametrized over Enter, Escape, and Tab.  Each case
    provides:
      - ``html``              : the fixture page, including the JS event listener
                                wired to that specific key
      - ``filename``          : the HTML file name written to disk
      - ``setup_action``      : a string flag for any interaction needed before
                                pressing the key (typing text, clicking to focus,
                                or nothing)
      - ``press_method_name`` : the name of the press method on the element
                                (``press_enter``, ``press_escape``, ``press_tab``)
      - ``expected_status``   : the substring expected in the ``#status`` div

    ``setup_action`` uses a small set of string flags (``"type_search"``,
    ``"click_first"``, ``"none"``) rather than passing lambdas, keeping the
    parametrize table readable as plain data.  ``getattr`` then resolves the
    press method by name at runtime, the same pattern used in ``TestElementState``
    and ``TestTextAndValues``.
    """

    @pytest.mark.parametrize(
        "html, filename, setup_action, press_method_name, expected_status",
        [
            pytest.param(
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
                "enter_key.html",
                "type_search",
                "press_enter",
                "Submitted",
                id="enter",
            ),
            pytest.param(
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
                "escape_key.html",
                "none",
                "press_escape",
                "Cancelled",
                id="escape",
            ),
            pytest.param(
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
                "tab_navigation.html",
                "click_first",
                "press_tab",
                "Button focused",
                id="tab",
            ),
        ],
    )
    def test_key_press(
        self,
        resilient_page: BasePage,
        tmp_path: Path,
        logger,
        html: str,
        filename: str,
        setup_action: str,
        press_method_name: str,
        expected_status: str,
    ) -> None:
        """
        Test: Key press methods (Enter, Escape, Tab) fire the correct handlers.

        **Why CI-critical**:
          - Tests keyboard interactions in headless mode
          - Covers real scenarios: form submission (Enter), cancel (Escape),
            and focus navigation (Tab)

        Parametrized over: Enter key, Escape key, Tab key.
        """
        url: str = write_html(tmp_path, filename, html)

        resilient_page.navigate(url)

        # Some keys require setup before pressing:
        #   "type_search" — Enter test needs text in the input first
        #   "click_first" — Tab test needs the input focused first
        #   "none"        — Escape test needs no setup
        if setup_action == "type_search":
            resilient_page.input_field.type("search")
        elif setup_action == "click_first":
            resilient_page.input_field.click()

        press_method: Callable[[], None] = getattr(
            resilient_page.input_field, press_method_name
        )
        press_method()
        logger.info(f"✓ Called {press_method_name}()")

        status: str = resilient_page.status.text()
        assert expected_status in status, (
            f"Expected {expected_status!r} in status, got: {status!r}"
        )
        logger.info(f"✓ {press_method_name} handler executed correctly")


# ============================================================================
# ATTRIBUTE TESTS
# ============================================================================


@pytest.mark.ci_critical
class TestAttributeAssertions:
    """Tests for reading and asserting HTML element attributes."""

    def test_get_element_attribute(
        self, resilient_page: BasePage, tmp_path: Path, logger
    ) -> None:
        """
        Test: Retrieve HTML attribute from element.

        **Why CI-critical**:
          - Tests attr() getter
          - Real scenario: check data-* attributes, aria-* attributes
        """
        url: str = write_html(
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

        resilient_page.navigate(url)

        # Get custom attribute
        testid: str = resilient_page.button.attr("data-testid")
        assert testid == "primary", f"Expected 'primary', got: {testid!r}"
        logger.info("✓ Custom attribute retrieved")

        # Get aria attribute
        label: str = resilient_page.button.attr("aria-label")
        assert label == "Submit form", f"Expected 'Submit form', got: {label!r}"
        logger.info("✓ Aria attribute retrieved")

    def test_should_have_attr_assertion(
        self, resilient_page: BasePage, tmp_path: Path, logger
    ) -> None:
        """
        Test: should_have_attr() assertion for attributes.

        **Why CI-critical**:
          - Tests attribute assertion with helpful errors
          - Useful for accessibility and data attribute checks
        """
        url: str = write_html(
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

        resilient_page.navigate(url)

        # Attribute assertion should pass
        resilient_page.button.should_have_attr("type", "submit")
        logger.info("✓ Attribute assertion passed")
