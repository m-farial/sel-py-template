"""Local-fixture smoke tests for Chrome, Firefox, and Edge setup."""

from __future__ import annotations

from pathlib import Path

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from template_tests.integration.fixtures_html import BROWSER_SMOKE_HTML
from template_tests.integration.helpers import write_html


@pytest.fixture()
def browser_smoke_url(tmp_path: Path) -> str:
    """Provide a local page so framework validation never depends on the network."""
    return write_html(tmp_path, "browser_smoke.html", BROWSER_SMOKE_HTML)


@pytest.mark.e2e
class TestBrowserSetup:
    """Verify essential browser operations against a deterministic local page."""

    def test_browser_launches(self, driver: WebDriver) -> None:
        assert driver.session_id is not None

    def test_navigate_to_url(self, driver: WebDriver, browser_smoke_url: str) -> None:
        driver.get(browser_smoke_url)
        assert driver.current_url == browser_smoke_url

    def test_page_title(self, driver: WebDriver, browser_smoke_url: str) -> None:
        driver.get(browser_smoke_url)
        assert driver.title == "Browser Smoke Fixture"

    def test_find_and_interact_with_element(
        self, driver: WebDriver, browser_smoke_url: str
    ) -> None:
        driver.get(browser_smoke_url)
        search_box = driver.find_element(By.NAME, "q")
        assert search_box.is_displayed()
        search_box.send_keys("Selenium WebDriver")
        assert search_box.get_attribute("value") == "Selenium WebDriver"

    def test_javascript_execution(
        self, driver: WebDriver, browser_smoke_url: str
    ) -> None:
        driver.get(browser_smoke_url)
        assert (
            driver.execute_script("return document.title;") == "Browser Smoke Fixture"
        )

    def test_window_management(self, driver: WebDriver, browser_smoke_url: str) -> None:
        driver.get(browser_smoke_url)
        assert driver.current_window_handle is not None
        size = driver.get_window_size()
        assert size["width"] > 0
        assert size["height"] > 0

    def test_screenshot_capability(
        self, driver: WebDriver, tmp_path: Path, browser_smoke_url: str
    ) -> None:
        driver.get(browser_smoke_url)
        screenshot_path = tmp_path / "test_screenshot.png"
        driver.save_screenshot(str(screenshot_path))
        assert screenshot_path.is_file()
        assert screenshot_path.stat().st_size > 0

    def test_login_fixture_navigation(
        self, driver: WebDriver, browser_smoke_url: str
    ) -> None:
        driver.get(browser_smoke_url)
        assert driver.find_element(By.ID, "user-name").is_displayed()
        assert driver.find_element(By.ID, "password").is_displayed()
        assert driver.find_element(By.ID, "login-button").is_displayed()


def test_quick_browser_check(driver: WebDriver, browser_smoke_url: str) -> None:
    """Run the smallest browser-and-DOM check without external network access."""
    driver.get(browser_smoke_url)
    assert driver.find_element(By.TAG_NAME, "h1").text == "Browser Smoke Fixture"
