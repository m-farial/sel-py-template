from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from pytest_a11y import assert_no_critical_violations
from template_tests.integration.fixtures_html import (
    BROKEN_PAGE_HTML,
    BROKEN_PAGE_HTML_NAME,
    SIMPLE_PAGE_HTML,
    SIMPLE_PAGE_HTML_NAME,
)
from template_tests.integration.helpers import write_html

pytestmark = [pytest.mark.a11y, pytest.mark.integration]


@pytest.mark.a11y
class TestA11y:
    """Accessibility plugin smoke tests and basic violation detection."""

    def test_a11y_plugin_is_loaded(self) -> None:
        """Verify that the pytest-a11y plugin is installed and importable."""
        assert importlib.util.find_spec("pytest_a11y") is not None, (
            "pytest-a11y is not installed — add it to your dev dependencies"
        )

    def test_homepage_a11y(self, driver, axe, tmp_path) -> None:
        """Accessibility smoke test using a local controlled page."""
        url = write_html(tmp_path, SIMPLE_PAGE_HTML_NAME, SIMPLE_PAGE_HTML)
        driver.get(url)

        results = axe.run()
        assert_no_critical_violations(results)

    def test_a11y_detects_known_violation(self, driver, axe, tmp_path) -> None:
        """Verify axe finds a violation on an intentionally bad example."""
        url = write_html(tmp_path, BROKEN_PAGE_HTML_NAME, BROKEN_PAGE_HTML)
        driver.get(url)

        results = axe.run()
        violation_ids = [v.get("id") for v in results.get("violations", [])]

        assert len(violation_ids) > 0
        assert "label" in violation_ids or "form-field-multiple-labels" in violation_ids

    def test_a11y_report_artifacts(self, pytestconfig) -> None:
        """Validate that a11y artifact directory exists and includes generated output."""

        if not getattr(pytestconfig.option, "a11y", False):
            pytest.skip("re-run with --a11y")

        a11y_dir_str: str = getattr(pytestconfig, "a11y_session_dir", "")
        a11y_dir = Path(a11y_dir_str)
        assert a11y_dir.is_dir(), f"Expected a11y directory to exist: {a11y_dir}"

        report_files = list(a11y_dir.glob("**/*"))
        assert report_files, f"No files found in a11y directory: {a11y_dir}"

        # Basic parse test for one report file, if JSON present.
        json_report = next(
            (p for p in report_files if p.suffix.lower() == ".json"), None
        )
        if json_report:
            loaded = json.loads(json_report.read_text(encoding="utf-8"))
            assert "violations" in loaded or "passes" in loaded
