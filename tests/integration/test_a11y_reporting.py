from __future__ import annotations

from pathlib import Path

import pytest
from pytest_a11y import assert_no_axe_violations
from selenium.webdriver.remote.webdriver import WebDriver
from tests.integration.fixtures_html import (
    A11Y_ACCESSIBLE_HTML,
    A11Y_INACCESSIBLE_HTML,
)
from tests.integration.helpers import (
    assert_axe_result_shape,
    collect_rule_ids,
    count_violations,
    write_html,
)

pytestmark = pytest.mark.a11y


@pytest.mark.a11y
@pytest.mark.integration
class TestA11yReporting:
    """Tests for axe report generation and violation comparison across fixture pages."""

    def test_a11y_report_generation_for_local_fixture(
        self,
        driver: WebDriver,
        axe,
        tmp_path: Path,
    ) -> None:
        """
        Validate that a local intentionally broken page produces parseable axe output.
        """
        url = write_html(tmp_path, "form_inaccessible.html", A11Y_INACCESSIBLE_HTML)
        driver.get(url)

        results = axe.run()

        assert_axe_result_shape(results)

        violation_ids = collect_rule_ids(results)
        assert violation_ids, "Expected at least one accessibility violation"
        assert "label" in violation_ids or "form-field-multiple-labels" in violation_ids

    def test_a11y_violation_drops_after_fix(
        self,
        driver: WebDriver,
        axe,
        tmp_path: Path,
    ) -> None:
        """
        Verify the same fixture becomes more accessible after the missing label is fixed.
        """
        broken_url = write_html(
            tmp_path, "form_inaccessible.html", A11Y_INACCESSIBLE_HTML
        )
        fixed_url = write_html(tmp_path, "form_accessible.html", A11Y_ACCESSIBLE_HTML)

        driver.get(broken_url)
        broken_results = axe.run()
        broken_ids = collect_rule_ids(broken_results)
        broken_count = count_violations(broken_results)

        assert broken_ids, "Expected at least one violation on broken page"
        assert "label" in broken_ids or "form-field-multiple-labels" in broken_ids

        driver.get(fixed_url)
        fixed_results = axe.run()
        fixed_ids = collect_rule_ids(fixed_results)
        fixed_count = count_violations(fixed_results)

        assert fixed_count <= broken_count, (
            f"Expected fixed page to have fewer or equal violations: "
            f"broken={broken_count}, fixed={fixed_count}"
        )
        assert "label" not in fixed_ids, (
            "Expected missing-label violation to be resolved on the fixed page"
        )
        assert_no_axe_violations(fixed_results)
