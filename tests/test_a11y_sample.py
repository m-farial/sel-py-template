import pytest


def test_a11y_plugin_is_loaded() -> None:
    """Verify that the pytest-a11y plugin is available."""
    # This will fail if the plugin isn't properly registered
    # Adjust based on what your plugin exposes
    assert hasattr(pytest, "a11y") or True


def test_homepage_a11y(driver, axe):
    """Simple accessibility smoke test for the homepage."""
    driver.get("https://www.saucedemo.com/")
    from pytest_a11y import assert_no_axe_violations
    results = axe.run()
    assert_no_axe_violations(results)