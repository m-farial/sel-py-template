from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from sel_py_template.utils.artifact_manager import ArtifactConfig, ArtifactManager


def build_manager(
    tmp_path: Path,
    *,
    create_daily_folder: bool = True,
    timestamped_runs: bool = True,
    a11y_enabled: bool = False,
    extra_artifacts: dict[str, str] | None = None,
) -> ArtifactManager:
    """Create an artifact manager with deterministic timestamps for unit tests."""
    config = ArtifactConfig(
        base_dir=tmp_path / "artifacts",
        create_daily_folder=create_daily_folder,
        timestamped_runs=timestamped_runs,
        extra_artifacts=extra_artifacts or {},
    )
    return ArtifactManager(
        config,
        browser="chrome",
        a11y_enabled=a11y_enabled,
        now=datetime(2026, 3, 6, 19, 18, 4),
    )


def test_build_paths_with_daily_folder_and_timestamp(tmp_path: Path) -> None:
    """Build paths with the default daily folder and timestamped run structure."""
    manager = build_manager(
        tmp_path,
        extra_artifacts={"downloads": "downloads", "abs": str(tmp_path / "shared")},
    )

    assert manager.paths.run_root == (
        tmp_path / "artifacts" / "2026-03-06" / "run_191804"
    )
    assert manager.paths.log_file.name == "chrome_test_run_19-18-04.log"
    assert manager.paths.pytest_html_report.name == "report.html"
    assert manager.paths.pytest_metadata_file.name == "plus_metadata.json"
    assert manager.paths.a11y_html_report.name == "a11y_report.html"
    assert manager.paths.extra_dirs["downloads"] == manager.paths.run_root / "downloads"
    assert manager.paths.extra_dirs["abs"] == tmp_path / "shared"


def test_build_paths_without_daily_folder_or_timestamp(tmp_path: Path) -> None:
    """Build paths without a daily folder and with a stable run name."""
    manager = build_manager(
        tmp_path,
        create_daily_folder=False,
        timestamped_runs=False,
    )

    assert manager.paths.run_root == tmp_path / "artifacts" / "run"
    assert (
        manager.paths.log_file
        == manager.paths.run_root / "chrome_test_run_19-18-04.log"
    )


def test_resolve_artifact_dir_handles_relative_and_absolute_paths(
    tmp_path: Path,
) -> None:
    """Resolve relative paths under the run root and preserve absolute paths."""
    manager = build_manager(tmp_path)
    absolute = tmp_path / "outside"

    assert manager._resolve_artifact_dir("debug/traces", manager.paths.run_root) == (
        manager.paths.run_root / "debug" / "traces"
    )
    assert (
        manager._resolve_artifact_dir(str(absolute), manager.paths.run_root) == absolute
    )


def test_register_producer_rejects_invalid_values(tmp_path: Path) -> None:
    """Reject blank producer names and blank artifact names or paths."""
    manager = build_manager(tmp_path)

    with pytest.raises(ValueError, match="Producer name cannot be empty"):
        manager.register_producer("   ", {"videos": "videos"})

    with pytest.raises(ValueError, match="empty artifact name"):
        manager.register_producer("playwright", {"   ": "videos"})

    with pytest.raises(ValueError, match="empty path"):
        manager.register_producer("playwright", {"videos": "   "})


def test_register_producer_uses_user_override_and_tracks_producers(
    tmp_path: Path,
) -> None:
    """Prefer user-defined extra artifact paths over producer defaults."""
    manager = build_manager(tmp_path, extra_artifacts={"videos": "custom/videos"})

    manager.register_producer(
        "playwright",
        {"videos": "videos", "traces": "debug/traces"},
    )

    assert (
        manager.paths.extra_dirs["videos"]
        == manager.paths.run_root / "custom" / "videos"
    )
    assert (
        manager.paths.extra_dirs["traces"]
        == manager.paths.run_root / "debug" / "traces"
    )
    assert manager.get_producer_dirs("playwright") == {
        "videos": manager.paths.run_root / "custom" / "videos",
        "traces": manager.paths.run_root / "debug" / "traces",
    }
    assert manager.get_registered_producers() == {
        "playwright": manager.get_producer_dirs("playwright")
    }


def test_get_producer_dirs_unknown_name_raises(tmp_path: Path) -> None:
    """Raise a clear error for unknown producers."""
    manager = build_manager(tmp_path)

    with pytest.raises(KeyError, match="Unknown artifact producer"):
        manager.get_producer_dirs("missing")


def test_create_directories_creates_expected_folders(tmp_path: Path) -> None:
    """Create run, report, a11y, extra, and producer directories."""
    manager = build_manager(
        tmp_path,
        a11y_enabled=True,
        extra_artifacts={"downloads": "downloads"},
    )
    manager.register_producer("playwright", {"traces": "debug/traces"})

    manager.create_directories()

    assert manager.paths.run_root.is_dir()
    assert manager.paths.pytest_html_dir.is_dir()
    assert manager.paths.failure_screenshots_dir.is_dir()
    assert manager.paths.a11y_dir.is_dir()
    assert manager.paths.violation_screenshots_dir.is_dir()
    assert (manager.paths.run_root / "downloads").is_dir()
    assert (manager.paths.run_root / "debug" / "traces").is_dir()


def test_create_directories_skips_a11y_when_disabled(tmp_path: Path) -> None:
    """Skip accessibility folders when accessibility reporting is disabled."""
    manager = build_manager(tmp_path, a11y_enabled=False)

    manager.create_directories()

    assert manager.paths.run_root.is_dir()
    assert manager.paths.pytest_html_dir.is_dir()
    assert not manager.paths.a11y_dir.exists()
    assert not manager.paths.violation_screenshots_dir.exists()


@pytest.mark.parametrize(
    ("nodeid", "expected"),
    [
        (
            r"tests/ui/test login.py::TestLogin::test/happy\path",
            "tests_ui_test_login.py__TestLogin__test_happy_path",
        ),
        ("simple", "simple"),
    ],
)
def test_sanitize_nodeid(nodeid: str, expected: str, tmp_path: Path) -> None:
    """Sanitize pytest node ids into filesystem-safe names."""
    manager = build_manager(tmp_path)

    assert manager.sanitize_nodeid(nodeid) == expected


def test_failure_artifact_paths_include_optional_timestamp(tmp_path: Path) -> None:
    """Build failure screenshot and log paths with and without timestamps."""
    manager = build_manager(tmp_path)

    assert manager.failure_screenshot_path("tests/test_example.py::test_demo") == (
        manager.paths.failure_screenshots_dir / "tests_test_example.py__test_demo.png"
    )
    assert (
        manager.failure_screenshot_path(
            "tests/test_example.py::test_demo",
            "STAMP",
        )
        == manager.paths.failure_screenshots_dir
        / "tests_test_example.py__test_demo_STAMP.png"
    )

    assert manager.failure_log_path("tests/test_example.py::test_demo") == (
        manager.paths.run_root / "tests_test_example.py__test_demo_failure.log"
    )
    assert (
        manager.failure_log_path(
            "tests/test_example.py::test_demo",
            "STAMP",
        )
        == manager.paths.run_root / "tests_test_example.py__test_demo_STAMP_failure.log"
    )


def test_get_extra_dir_and_file_create_parent_paths(tmp_path: Path) -> None:
    """Create parent directories for extra artifact lookups when requested."""
    manager = build_manager(tmp_path, extra_artifacts={"downloads": "downloads"})

    extra_dir = manager.get_extra_dir("downloads")
    extra_file = manager.get_extra_file("downloads", "artifact.txt")

    assert extra_dir.is_dir()
    assert extra_file == extra_dir / "artifact.txt"


def test_get_extra_dir_without_create_and_unknown_name(tmp_path: Path) -> None:
    """Support non-creating lookups and raise for unknown extra artifacts."""
    manager = build_manager(tmp_path, extra_artifacts={"downloads": "downloads"})

    extra_dir = manager.get_extra_dir("downloads", create=False)
    assert extra_dir == manager.paths.run_root / "downloads"
    assert not extra_dir.exists()

    with pytest.raises(KeyError, match="Unknown extra artifact directory"):
        manager.get_extra_dir("missing")
