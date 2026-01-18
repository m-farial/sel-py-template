def test_homepage_a11y(driver, check_a11y):
    """Simple accessibility smoke test for the homepage."""
    driver.get("https://www.saucedemo.com/")
    results = check_a11y()
    assert results["axe"] is not None
