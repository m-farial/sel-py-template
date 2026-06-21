from __future__ import annotations

import pytest
from template_tests.integration.helpers import load_json
from template_tests.integration.subprocess_helpers import (
    assert_dir_exists,
    assert_file_exists,
)


@pytest.mark.integration
def test_artifacts_and_metadata_persist_for_local_run(
    pytestconfig: pytest.Config,
    log_path: str,
) -> None:
    """Validate artifact creation in the current pytest session."""

    paths = pytestconfig._artifact_manager.paths  # type: ignore[attr-defined]
    pytest_html_dir = paths.pytest_html_dir
    metadata_file = paths.pytest_metadata_file

    assert_dir_exists(pytest_html_dir, "pytest_html artifact directory")
    assert_file_exists(metadata_file, metadata_file.name)

    metadata = load_json(metadata_file)
    assert isinstance(metadata, dict), (
        "Expected plus_metadata.json to parse as JSON object"
    )
