"""
Browser setup smoke tests.

Simple tests to verify Chrome, Firefox, and Edge are properly configured.
Run with: poetry run pytest tests/test_browser_setup.py --all-browsers --headed
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


class TestBrowserSetup:
    """Smoke tests to verify browser setup."""

    def test_browser_launches(self, driver: WebDriver, logger) -> None:
        """
        Test that the browser launches successfully.

        Args:
            driver: WebDriver fixture
            logger: Logger fixture
        """
        logger.info("Testing browser launch")
        assert driver is not None, "Driver should not be None"
        assert driver.session_id is not None, "Browser session should be active"
        logger.info("✓ Browser launched successfully")

    def test_navigate_to_url(self, driver: WebDriver, logger) -> None:
        """
        Test that the browser can navigate to a URL.

        Args:
            driver: WebDriver fixture
            logger: Logger fixture
        """
        test_url = "https://www.google.com"
        logger.info(f"Navigating to {test_url}")

        driver.get(test_url)

        assert driver.current_url.startswith(
            "https://www.google"
        ), f"Expected Google URL, got {driver.current_url}"
        logger.info("✓ Successfully navigated to URL")

    def test_page_title(self, driver: WebDriver, logger) -> None:
        """
        Test that the browser can retrieve page title.

        Args:
            driver: WebDriver fixture
            logger: Logger fixture
        """
        driver.get("https://www.google.com")

        title = driver.title
        logger.info(f"Page title: {title}")

        assert title is not None, "Page title should not be None"
        assert len(title) > 0, "Page title should not be empty"
        assert "Google" in title, f"Expected 'Google' in title, got '{title}'"
        logger.info("✓ Page title retrieved successfully")

    def test_find_element(self, driver: WebDriver, logger) -> None:
        """
        Test that the browser can find elements on a page.

        Args:
            driver: WebDriver fixture
            logger: Logger fixture
        """
        driver.get("https://www.google.com")

        # Wait for and find the search box
        wait = WebDriverWait(driver, 10)
        search_box = wait.until(ec.presence_of_element_located((By.NAME, "q")))

        assert search_box is not None, "Search box element should be found"
        assert search_box.is_displayed(), "Search box should be visible"
        logger.info("✓ Element found and displayed")

    def test_interact_with_element(self, driver: WebDriver, logger) -> None:
        """
        Test that the browser can interact with elements.

        Args:
            driver: WebDriver fixture
            logger: Logger fixture
        """
        driver.get("https://www.google.com")

        # Find search box
        wait = WebDriverWait(driver, 10)
        search_box = wait.until(ec.presence_of_element_located((By.NAME, "q")))

        # Type text
        test_text = "Selenium WebDriver"
        search_box.send_keys(test_text)

        # Verify text was entered
        entered_text = search_box.get_attribute("value")
        assert (
            entered_text == test_text
        ), f"Expected '{test_text}', got '{entered_text}'"
        logger.info("✓ Successfully interacted with element")

    def test_javascript_execution(self, driver: WebDriver, logger) -> None:
        """
        Test that the browser can execute JavaScript.

        Args:
            driver: WebDriver fixture
            logger: Logger fixture
        """
        driver.get("https://www.google.com")

        # Execute simple JavaScript
        result = driver.execute_script("return document.title;")

        assert result is not None, "JavaScript should return a value"
        assert "Google" in result, f"Expected 'Google' in result, got '{result}'"
        logger.info("✓ JavaScript execution successful")

    def test_window_management(self, driver: WebDriver, logger) -> None:
        """
        Test that the browser can manage windows.

        Args:
            driver: WebDriver fixture
            logger: Logger fixture
        """
        driver.get("https://www.google.com")

        # Get window handle
        current_handle = driver.current_window_handle
        assert current_handle is not None, "Window handle should not be None"

        # Get window size
        size = driver.get_window_size()
        assert size["width"] > 0, "Window width should be positive"
        assert size["height"] > 0, "Window height should be positive"

        logger.info(f"Window size: {size['width']}x{size['height']}")
        logger.info("✓ Window management successful")

    def test_screenshot_capability(self, driver: WebDriver, logger, tmp_path) -> None:
        """
        Test that the browser can take screenshots.

        Args:
            driver: WebDriver fixture
            logger: Logger fixture
            tmp_path: Pytest temporary directory fixture
        """
        driver.get("https://www.google.com")

        # Take screenshot
        screenshot_path = tmp_path / "test_screenshot.png"
        driver.save_screenshot(str(screenshot_path))

        assert screenshot_path.exists(), "Screenshot file should be created"
        assert screenshot_path.stat().st_size > 0, "Screenshot file should not be empty"
        logger.info(f"✓ Screenshot saved: {screenshot_path}")


# Quick sanity test - runs on default browser only
def test_quick_browser_check(driver: WebDriver) -> None:
    """
    Quick sanity check that browser basics work.
    Run with: poetry run pytest tests/test_browser_setup.py::test_quick_browser_check
    """
    driver.get("https://www.example.com")
    assert "Example Domain" in driver.title
    assert driver.find_element(By.TAG_NAME, "h1").text == "Example Domain"


# SauceDemo specific test
def test_saucedemo_navigation(driver: WebDriver, logger) -> None:
    """
    Test navigation to SauceDemo site.

    Args:
        driver: WebDriver fixture
        logger: Logger fixture
    """
    url = "https://www.saucedemo.com"
    logger.info(f"Navigating to SauceDemo: {url}")

    driver.get(url)

    # Verify page loaded
    assert (
        "Swag Labs" in driver.title
    ), f"Expected 'Swag Labs' in title, got '{driver.title}'"

    # Verify login elements exist
    username_field = driver.find_element(By.ID, "user-name")
    password_field = driver.find_element(By.ID, "password")
    login_button = driver.find_element(By.ID, "login-button")

    assert username_field.is_displayed(), "Username field should be visible"
    assert password_field.is_displayed(), "Password field should be visible"
    assert login_button.is_displayed(), "Login button should be visible"

    logger.info("✓ SauceDemo page loaded successfully")
