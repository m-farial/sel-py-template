from __future__ import annotations

from pathlib import Path

import pytest
from tests.integration.fixtures_html import SUBPROCESS_FAILING_HTML
from tests.integration.helpers import load_json
from tests.integration.subprocess_helpers import (
    assert_dir_exists,
    assert_file_exists,
)


def _build_failing_test_module(html_name: str) -> str:
    """
    Build a minimal failing Selenium integration test for subprocess execution.

    Args:
        html_name: Fixture HTML file name relative to tmp_path.

    Returns:
        Python test module source.
    """
    return f"""
from __future__ import annotations

from pathlib import Path

from selenium.webdriver.common.by import By


def test_subprocess_failure_still_writes_artifacts(driver, tmp_path) -> None:
    html_path = tmp_path / \"{html_name}\"
    html_path.write_text({SUBPROCESS_FAILING_HTML!r}, encoding=\"utf-8\")
    driver.get(html_path.as_uri())

    heading = driver.find_element(By.ID, \"page-title\")
    assert heading.text == \"Wrong Heading\"
"""


@pytest.mark.integration
def test_artifacts_and_metadata_persist_for_local_run(
    pytestconfig: pytest.Config,
    log_path: str,
) -> None:
    """Validate artifact creation in the current pytest session."""
    run_dir = Path(log_path)
    pytest_html_dir = run_dir / "pytest_html"

    assert_dir_exists(pytest_html_dir, "pytest_html artifact directory")
    assert_file_exists(pytest_html_dir / "plus_metadata.json", "plus_metadata.json")

    if not pytestconfig.getoption("a11y"):
        a11y_dir = run_dir / "a11y"
        assert not a11y_dir.exists(), (
            "Expected no a11y artifacts when --a11y is not passed"
        )

    metadata = load_json(pytest_html_dir / "plus_metadata.json")
    assert isinstance(metadata, dict), (
        "Expected plus_metadata.json to parse as JSON object"
    )
