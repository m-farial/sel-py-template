from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

_ROOT_CONFTEST = Path(__file__).resolve().parents[2] / "conftest.py"
_SPEC = importlib.util.spec_from_file_location("root_conftest", _ROOT_CONFTEST)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"Unable to load root pytest configuration: {_ROOT_CONFTEST}")
project_conftest = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(project_conftest)


def _config(
    rootpath: Path,
    *,
    cli_report_title: str | None = None,
    cli_extra_artifacts: list[str] | None = None,
) -> MagicMock:
    """Build the pytest config surface used by project-settings helpers."""
    config = MagicMock()
    config.rootpath = rootpath
    config.option = SimpleNamespace(report_title=cli_report_title)
    config.getini.return_value = []
    config.getoption.side_effect = lambda name: {
        "--report-title": cli_report_title,
        "--extra-artifact": cli_extra_artifacts or [],
    }[name]
    return config


def _write_settings(rootpath: Path, content: str) -> None:
    (rootpath / "project_settings.ini").write_text(content, encoding="utf-8")


def test_project_settings_are_optional(tmp_path: Path) -> None:
    config = _config(tmp_path)

    assert project_conftest._project_setting(config, "report_title") is None
    assert project_conftest._parse_extra_artifacts_from_project_settings(config) == {}


def test_project_settings_override_default_report_title(tmp_path: Path) -> None:
    _write_settings(tmp_path, "[sel_py_template]\nreport_title = Project A Report\n")
    config = _config(tmp_path)

    project_conftest._apply_project_settings(config)

    assert config.option.report_title == "Project A Report"


def test_cli_report_title_overrides_project_settings(tmp_path: Path) -> None:
    _write_settings(tmp_path, "[sel_py_template]\nreport_title = Project A Report\n")
    config = _config(tmp_path, cli_report_title="CI Report")

    project_conftest._apply_project_settings(config)

    assert config.option.report_title == "CI Report"


def test_project_settings_register_extra_artifacts(tmp_path: Path) -> None:
    _write_settings(
        tmp_path,
        "[sel_py_template]\nextra_artifacts =\n    downloads=downloads\n    traces=debug/traces\n",
    )
    config = _config(tmp_path, cli_extra_artifacts=["downloads=ci-downloads"])

    assert project_conftest._resolve_extra_artifacts(config) == {
        "downloads": "ci-downloads",
        "traces": "debug/traces",
    }


@pytest.mark.parametrize("value", ["downloads", "=downloads", "downloads="])
def test_project_settings_reject_invalid_extra_artifacts(
    tmp_path: Path, value: str
) -> None:
    _write_settings(tmp_path, f"[sel_py_template]\nextra_artifacts = {value}\n")

    with pytest.raises(pytest.UsageError):
        project_conftest._parse_extra_artifacts_from_project_settings(_config(tmp_path))
