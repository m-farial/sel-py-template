from __future__ import annotations

from collections.abc import Generator
from datetime import datetime
import json
import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from sel_py_template.utils.artifact_manager import ArtifactConfig, ArtifactManager
from sel_py_template.utils.report_plugin import ReportPlugin


def build_artifact_manager(tmp_path: Path) -> ArtifactManager:
    """Create a deterministic artifact manager for report plugin tests."""
    return ArtifactManager(
        ArtifactConfig(base_dir=tmp_path / "artifacts"),
        browser="chrome",
        now=datetime(2026, 3, 6, 19, 18, 4),
    )


def build_config() -> MagicMock:
    """Create a pytest config double with the attributes used by the plugin."""
    config = MagicMock()
    config.option = SimpleNamespace(html_title=None)
    config.getoption.side_effect = lambda name, default=None: {
        "report_title": "CLI Title",
        "log_cli_level": "INFO",
        "log_file_level": "DEBUG",
    }.get(name, default)
    config.getini.side_effect = lambda name: {"report_title": "INI Title"}[name]
    return config


def drive_hookwrapper(
    generator: Generator[None, Any, None],
    outcome: Any,
) -> None:
    """Advance a hookwrapper generator and deliver an outcome object."""
    next(generator)
    with pytest.raises(StopIteration):
        generator.send(outcome)


class TestReportPluginInit:
    """Tests covering plugin initialization and configuration."""

    @patch("sel_py_template.utils.report_plugin.logging.config.dictConfig")
    @patch.object(ReportPlugin, "set_config_metadata")
    def test_init_sets_core_attributes(
        self,
        mock_set_config_metadata: MagicMock,
        mock_dict_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Initialize the plugin with expected paths and session logger."""
        artifact_manager = build_artifact_manager(tmp_path)
        config = build_config()

        plugin = ReportPlugin(
            artifact_manager=artifact_manager,
            browser="chrome",
            config=config,
        )

        assert plugin.browser == "chrome"
        assert plugin.base_log_dir == str(artifact_manager.paths.run_root)
        assert plugin.log_file == str(artifact_manager.paths.log_file)
        assert plugin.session_logger.name == "app.chrome"
        assert config._logger is plugin.session_logger
        mock_dict_config.assert_called_once()
        mock_set_config_metadata.assert_called_once_with(config)

    @patch("sel_py_template.utils.report_plugin.logging.config.dictConfig")
    def test_configure_logging_uses_configured_levels(
        self,
        mock_dict_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Build logging config from pytest's built-in logging options."""
        artifact_manager = build_artifact_manager(tmp_path)
        config = build_config()
        with patch.object(ReportPlugin, "set_config_metadata"):
            plugin = ReportPlugin(
                artifact_manager=artifact_manager, browser="chrome", config=config
            )

        plugin.configure_logging()

        logging_config = mock_dict_config.call_args.args[0]
        assert logging_config["handlers"]["console"]["level"] == "INFO"
        assert logging_config["handlers"]["file"]["level"] == "DEBUG"
        assert logging_config["loggers"]["app"]["level"] == "DEBUG"
        assert logging_config["loggers"]["selenium"]["level"] == "WARNING"
        assert logging_config["loggers"]["urllib3"]["level"] == "WARNING"
        assert logging_config["loggers"]["urllib3.connectionpool"]["level"] == "WARNING"

    @patch("sel_py_template.utils.report_plugin.logging.config.dictConfig")
    def test_configure_logging_defaults_without_config(
        self,
        mock_dict_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Use sensible default logging levels when no pytest config exists."""
        artifact_manager = build_artifact_manager(tmp_path)
        with patch.object(ReportPlugin, "set_config_metadata"):
            plugin = ReportPlugin(
                artifact_manager=artifact_manager, browser="chrome", config=None
            )

        plugin.configure_logging()

        logging_config = mock_dict_config.call_args.args[0]
        assert logging_config["handlers"]["console"]["level"] == "INFO"
        assert logging_config["handlers"]["file"]["level"] == "DEBUG"

    def test_logger_fixture_returns_session_logger(self, tmp_path: Path) -> None:
        """Return the session logger stored on pytest config."""
        artifact_manager = build_artifact_manager(tmp_path)
        config = build_config()
        with (
            patch.object(ReportPlugin, "configure_logging"),
            patch.object(ReportPlugin, "set_config_metadata"),
        ):
            plugin = ReportPlugin(
                artifact_manager=artifact_manager,
                browser="chrome",
                config=config,
            )

        request = MagicMock()
        request.config._logger = logging.getLogger("app.chrome")

        result = plugin.logger.__wrapped__(plugin, request)

        assert result is request.config._logger


class TestReportPluginGitAndEnvironment:
    """Tests covering git metadata and environment info generation."""

    @patch("sel_py_template.utils.report_plugin.Repo")
    def test_get_git_info_success(
        self,
        mock_repo_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Return branch and commit information when the repository is available."""
        artifact_manager = build_artifact_manager(tmp_path)
        config = build_config()
        with (
            patch.object(ReportPlugin, "configure_logging"),
            patch.object(ReportPlugin, "set_config_metadata"),
        ):
            plugin = ReportPlugin(
                artifact_manager=artifact_manager, browser="chrome", config=config
            )
        plugin.session_logger = MagicMock()

        repo = MagicMock()
        repo.refs.read_ref.return_value = b"refs/heads/main"
        commit_obj = MagicMock()
        commit_obj.id = b"abcdef123456"
        repo.__getitem__.return_value = commit_obj
        mock_repo_class.return_value = repo

        assert plugin._get_git_info() == {"branch": "main", "commit": "abcdef1"}

    @patch("sel_py_template.utils.report_plugin.Repo")
    def test_get_git_info_uses_na_when_commit_id_not_bytes(
        self,
        mock_repo_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Return NA when the git commit id is not bytes."""
        artifact_manager = build_artifact_manager(tmp_path)
        config = build_config()
        with (
            patch.object(ReportPlugin, "configure_logging"),
            patch.object(ReportPlugin, "set_config_metadata"),
        ):
            plugin = ReportPlugin(
                artifact_manager=artifact_manager, browser="chrome", config=config
            )
        plugin.session_logger = MagicMock()

        repo = MagicMock()
        repo.refs.read_ref.return_value = b"refs/heads/main"
        commit_obj = MagicMock()
        commit_obj.id = "abcdef123456"
        repo.__getitem__.return_value = commit_obj
        mock_repo_class.return_value = repo

        assert plugin._get_git_info() == {"branch": "main", "commit": "NA"}

    @patch("sel_py_template.utils.report_plugin.Repo", side_effect=RuntimeError("boom"))
    def test_get_git_info_failure_logs_warning(
        self,
        mock_repo_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Return fallback git info and warn when repository lookup fails."""
        artifact_manager = build_artifact_manager(tmp_path)
        config = build_config()
        with (
            patch.object(ReportPlugin, "configure_logging"),
            patch.object(ReportPlugin, "set_config_metadata"),
        ):
            plugin = ReportPlugin(
                artifact_manager=artifact_manager, browser="chrome", config=config
            )
        plugin.session_logger = MagicMock()

        info = plugin._get_git_info()

        assert info == {"branch": "NA", "commit": "NA"}
        plugin.session_logger.warning.assert_called_once()
        mock_repo_class.assert_called_once_with(".")

    @patch(
        "sel_py_template.utils.report_plugin.get_python_version", return_value="3.12.0"
    )
    @patch.object(
        ReportPlugin,
        "_get_git_info",
        return_value={"branch": "dev", "commit": "abc1234"},
    )
    def test_get_environment_info(
        self,
        mock_git_info: MagicMock,
        mock_python_version: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Include git, browser, timestamp, and Python metadata in environment info."""
        artifact_manager = build_artifact_manager(tmp_path)
        config = build_config()
        with (
            patch.object(ReportPlugin, "configure_logging"),
            patch.object(ReportPlugin, "set_config_metadata"),
        ):
            plugin = ReportPlugin(
                artifact_manager=artifact_manager, browser="chrome", config=config
            )

        env = plugin._get_environment_info()

        assert env["branch"] == "dev"
        assert env["commit"] == "abc1234"
        assert env["python_version"] == "3.12.0"
        assert env["browser"] == "chrome"
        assert "generated_at" in env
        mock_git_info.assert_called_once()
        mock_python_version.assert_called_once()


class TestReportPluginMetadata:
    """Tests covering report metadata population and persistence."""

    @patch.object(ReportPlugin, "_get_environment_info")
    def test_set_config_metadata_populates_option_fields(
        self,
        mock_environment_info: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Populate pytest-html-plus metadata from environment info and CLI title."""
        mock_environment_info.return_value = {
            "branch": "main",
            "commit": "abc1234",
            "python_version": "3.12.0",
            "generated_at": "2026-03-06T19:18:04",
            "browser": "chrome",
            "environment": "local",
        }
        artifact_manager = build_artifact_manager(tmp_path)
        config = build_config()
        with patch.object(ReportPlugin, "configure_logging"):
            plugin = ReportPlugin(
                artifact_manager=artifact_manager, browser="chrome", config=config
            )

        plugin.set_config_metadata(config)

        assert config.option.html_title == "CLI Title"
        assert config.option.environment == "local"
        assert config.option.git_branch == "main"
        assert config.option.git_commit == "abc1234"
        assert config.option.python_version == "3.12.0"
        assert config.option.browser == "chrome"
        assert config.option.generated_at == "2026-03-06T19:18:04"

    def test_set_config_metadata_handles_none_config(self, tmp_path: Path) -> None:
        """Return early when no config object is provided."""
        artifact_manager = build_artifact_manager(tmp_path)
        with (
            patch.object(ReportPlugin, "configure_logging"),
            patch.object(ReportPlugin, "set_config_metadata"),
        ):
            plugin = ReportPlugin(
                artifact_manager=artifact_manager, browser="chrome", config=None
            )

        plugin.set_config_metadata(None)

    def test_set_config_metadata_falls_back_to_ini_title(self, tmp_path: Path) -> None:
        """Use the ini report title when the CLI title is not provided."""
        artifact_manager = build_artifact_manager(tmp_path)
        config = build_config()
        config.option.html_title = None
        config.getoption.side_effect = lambda name, default=None: {
            "report_title": None,
            "log_cli_level": "INFO",
            "log_file_level": "DEBUG",
        }.get(name, default)
        with (
            patch.object(ReportPlugin, "configure_logging"),
            patch.object(
                ReportPlugin,
                "_get_environment_info",
                return_value={
                    "branch": "NA",
                    "commit": "NA",
                    "python_version": "3.12.0",
                    "generated_at": "now",
                    "browser": "chrome",
                },
            ),
        ):
            plugin = ReportPlugin(
                artifact_manager=artifact_manager, browser="chrome", config=config
            )

        plugin.set_config_metadata(config)

        assert config.option.html_title == "INI Title"

    def test_set_config_metadata_handles_missing_ini_title(
        self, tmp_path: Path
    ) -> None:
        """Fall back to the default title when ini lookup fails."""
        artifact_manager = build_artifact_manager(tmp_path)
        config = build_config()
        config.getoption.side_effect = lambda name, default=None: {
            "report_title": None,
            "log_cli_level": "INFO",
            "log_file_level": "DEBUG",
        }.get(name, default)
        config.getini.side_effect = RuntimeError("missing ini")
        with (
            patch.object(ReportPlugin, "configure_logging"),
            patch.object(
                ReportPlugin,
                "_get_environment_info",
                return_value={
                    "branch": "NA",
                    "commit": "NA",
                    "python_version": "3.12.0",
                    "generated_at": "now",
                    "browser": "chrome",
                },
            ),
        ):
            plugin = ReportPlugin(
                artifact_manager=artifact_manager, browser="chrome", config=config
            )

        plugin.set_config_metadata(config)

        assert config.option.html_title == "Template tests report"

    def test_pytest_sessionstart_writes_plus_metadata(self, tmp_path: Path) -> None:
        """Write pytest-html-plus metadata at session start."""
        artifact_manager = build_artifact_manager(tmp_path)
        artifact_manager.create_directories()
        config = build_config()
        with (
            patch.object(ReportPlugin, "configure_logging"),
            patch.object(ReportPlugin, "set_config_metadata"),
        ):
            plugin = ReportPlugin(
                artifact_manager=artifact_manager, browser="chrome", config=config
            )

        plugin.session_logger = MagicMock()
        session = MagicMock()
        session.config.option = SimpleNamespace(
            html_title="My Report",
            environment="local",
            git_branch="main",
            git_commit="abc1234",
            python_version="3.12.0",
            generated_at="2026-03-06T19:18:04",
            browser="chrome",
        )

        plugin.pytest_sessionstart(session)

        data = json.loads(
            artifact_manager.paths.pytest_metadata_file.read_text(encoding="utf-8")
        )
        assert data["report_title"] == "My Report"
        assert data["browser"] == "chrome"

    def test_pytest_sessionstart_logs_debug_when_metadata_write_fails(
        self,
        tmp_path: Path,
    ) -> None:
        """Log a debug message when writing plus_metadata.json fails."""
        artifact_manager = build_artifact_manager(tmp_path)
        artifact_manager.create_directories()
        config = build_config()

        with (
            patch.object(ReportPlugin, "configure_logging"),
            patch.object(ReportPlugin, "set_config_metadata"),
        ):
            plugin = ReportPlugin(
                artifact_manager=artifact_manager,
                browser="chrome",
                config=config,
            )

        plugin.session_logger = MagicMock()
        session = MagicMock()
        session.config.option = SimpleNamespace(
            html_title="My Report",
            environment="local",
            git_branch="main",
            git_commit="abc1234",
            python_version="3.12.0",
            generated_at="2026-03-06T19:18:04",
            browser="chrome",
        )

        error = OSError("write error")
        with patch.object(Path, "open", side_effect=error):
            plugin.pytest_sessionstart(session)

        plugin.session_logger.debug.assert_called_with(
            "Could not write plus_metadata.json at session start: %s",
            error,
        )


class TestReportPluginHooks:
    """Tests covering runtest and session hook behavior."""

    def test_pytest_runtest_logstart_and_logfinish_write_markers(
        self,
        tmp_path: Path,
    ) -> None:
        """Write start and finish markers around each test."""
        artifact_manager = build_artifact_manager(tmp_path)
        config = build_config()
        with (
            patch.object(ReportPlugin, "configure_logging"),
            patch.object(ReportPlugin, "set_config_metadata"),
        ):
            plugin = ReportPlugin(
                artifact_manager=artifact_manager, browser="chrome", config=config
            )

        plugin.session_logger = MagicMock()

        plugin.pytest_runtest_logstart("tests/test_demo.py::test_one")
        plugin.pytest_runtest_logfinish(
            "tests/test_demo.py::test_one",
            ("tests/test_demo.py", 1, "test_one"),
        )

        assert plugin.session_logger.info.call_count >= 4
        plugin.session_logger.debug.assert_called_once_with(
            "Test: %s", "tests/test_demo.py::test_one"
        )

    def test_pytest_runtest_makereport_pass_path(self, tmp_path: Path) -> None:
        """Record passing tests and emit completion logs."""
        artifact_manager = build_artifact_manager(tmp_path)
        config = build_config()
        with (
            patch.object(ReportPlugin, "configure_logging"),
            patch.object(ReportPlugin, "set_config_metadata"),
        ):
            plugin = ReportPlugin(
                artifact_manager=artifact_manager, browser="chrome", config=config
            )

        plugin.session_logger = MagicMock()
        item = MagicMock()
        item.function.__doc__ = "test doc"
        item.funcargs = {}
        item.name = "test_pass"
        report = SimpleNamespace(
            when="call",
            outcome="passed",
            nodeid="tests/test_demo.py::test_pass",
            duration=1.25,
            skipped=False,
            failed=False,
        )
        outcome = MagicMock()
        outcome.get_result.return_value = report

        drive_hookwrapper(plugin.pytest_runtest_makereport(item, MagicMock()), outcome)

        assert plugin.test_reports == [
            {
                "when": "call",
                "outcome": "passed",
                "duration": 1.25,
                "nodeid": "tests/test_demo.py::test_pass",
            }
        ]
        assert report.description == "test doc"
        plugin.session_logger.info.assert_any_call("xx Passed Test %s", report.nodeid)
        plugin.session_logger.debug.assert_any_call(
            "Test completed successfully nodeid=%s when=%s",
            report.nodeid,
            report.when,
        )

    @patch("sel_py_template.utils.report_plugin.datetime")
    def test_pytest_runtest_makereport_failure_saves_artifacts(
        self,
        mock_datetime: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Save failure screenshots and failure logs when HTML plugin is disabled."""
        mock_datetime.now.return_value.strftime.return_value = "STAMP"
        artifact_manager = build_artifact_manager(tmp_path)
        artifact_manager.create_directories()
        config = build_config()
        with (
            patch.object(ReportPlugin, "configure_logging"),
            patch.object(ReportPlugin, "set_config_metadata"),
        ):
            plugin = ReportPlugin(
                artifact_manager=artifact_manager, browser="chrome", config=config
            )

        plugin.session_logger = MagicMock()
        driver = MagicMock()
        item_config = MagicMock()
        item_config.pluginmanager = MagicMock()
        item_config.pluginmanager.hasplugin.return_value = False
        item_config.option = SimpleNamespace(html_output=None)

        item = MagicMock()
        item.function.__doc__ = "failure doc"
        item.funcargs = {"driver": driver}
        item.name = "test_fail"
        item.config = item_config

        report = SimpleNamespace(
            when="call",
            outcome="failed",
            nodeid="tests/test_demo.py::test_fail",
            duration=0.5,
            skipped=False,
            failed=True,
            longrepr="traceback text",
        )
        outcome = MagicMock()
        outcome.get_result.return_value = report

        drive_hookwrapper(plugin.pytest_runtest_makereport(item, MagicMock()), outcome)

        driver.save_screenshot.assert_called_once()
        assert Path(report._log_file).exists()
        assert "traceback text" in Path(report._log_file).read_text(encoding="utf-8")
        assert report._screenshot_path.endswith(".png")
        plugin.session_logger.info.assert_any_call("xx Failed Test %s", report.nodeid)

    def test_pytest_runtest_makereport_failed_without_wasxfail_attribute(
        self,
        tmp_path: Path,
    ) -> None:
        """Treat a normal failed test as failed when wasxfail is absent."""
        artifact_manager = build_artifact_manager(tmp_path)
        artifact_manager.create_directories()
        config = build_config()
        with (
            patch.object(ReportPlugin, "configure_logging"),
            patch.object(ReportPlugin, "set_config_metadata"),
        ):
            plugin = ReportPlugin(
                artifact_manager=artifact_manager, browser="chrome", config=config
            )

        plugin.session_logger = MagicMock()
        item = MagicMock()
        item.function.__doc__ = "failure doc"
        item.funcargs = {}
        item.name = "test_fail"
        item.config = MagicMock()
        item.config.pluginmanager = MagicMock()
        item.config.pluginmanager.hasplugin.return_value = False
        item.config.option = SimpleNamespace(html_output=None)

        report = SimpleNamespace(
            when="call",
            outcome="failed",
            nodeid="tests/test_demo.py::test_fail",
            duration=0.5,
            skipped=False,
            failed=True,
            longrepr="traceback text",
        )
        outcome = MagicMock()
        outcome.get_result.return_value = report

        drive_hookwrapper(plugin.pytest_runtest_makereport(item, MagicMock()), outcome)

        plugin.session_logger.info.assert_any_call("xx Failed Test %s", report.nodeid)
        assert Path(report._log_file).exists()

    def test_pytest_runtest_makereport_failure_with_no_pluginmanager(
        self,
        tmp_path: Path,
    ) -> None:
        """Handle failure artifact logic when config exists but pluginmanager is missing."""
        artifact_manager = build_artifact_manager(tmp_path)
        artifact_manager.create_directories()
        config = build_config()

        with (
            patch.object(ReportPlugin, "configure_logging"),
            patch.object(ReportPlugin, "set_config_metadata"),
        ):
            plugin = ReportPlugin(
                artifact_manager=artifact_manager,
                browser="chrome",
                config=config,
            )

        plugin.session_logger = MagicMock()
        driver = MagicMock()

        item_config = MagicMock()
        item_config.pluginmanager = None
        item_config.option = SimpleNamespace(html_output=None)

        item = MagicMock()
        item.function.__doc__ = "failure doc"
        item.funcargs = {"driver": driver}
        item.name = "test_fail"
        item.config = item_config

        report = SimpleNamespace(
            when="call",
            outcome="failed",
            nodeid="tests/test_demo.py::test_fail",
            duration=0.5,
            skipped=False,
            failed=True,
            longrepr="traceback text",
        )
        outcome = MagicMock()
        outcome.get_result.return_value = report

        drive_hookwrapper(plugin.pytest_runtest_makereport(item, MagicMock()), outcome)

        driver.save_screenshot.assert_called_once()
        assert Path(report._log_file).exists()

    def test_pytest_runtest_makereport_failure_skips_screenshot_when_html_plugin_enabled(
        self,
        tmp_path: Path,
    ) -> None:
        """Skip manual screenshot capture when the built-in html plugin is enabled."""
        artifact_manager = build_artifact_manager(tmp_path)
        artifact_manager.create_directories()
        config = build_config()

        with (
            patch.object(ReportPlugin, "configure_logging"),
            patch.object(ReportPlugin, "set_config_metadata"),
        ):
            plugin = ReportPlugin(
                artifact_manager=artifact_manager,
                browser="chrome",
                config=config,
            )

        plugin.session_logger = MagicMock()
        driver = MagicMock()

        item_config = MagicMock()
        item_config.pluginmanager = MagicMock()
        item_config.pluginmanager.hasplugin.side_effect = lambda name: name == "html"
        item_config.option = SimpleNamespace(html_output=None)

        item = MagicMock()
        item.function.__doc__ = "failure doc"
        item.funcargs = {"driver": driver}
        item.name = "test_fail"
        item.config = item_config

        report = SimpleNamespace(
            when="call",
            outcome="failed",
            nodeid="tests/test_demo.py::test_fail",
            duration=0.5,
            skipped=False,
            failed=True,
            longrepr="traceback text",
        )
        outcome = MagicMock()
        outcome.get_result.return_value = report

        drive_hookwrapper(plugin.pytest_runtest_makereport(item, MagicMock()), outcome)

        driver.save_screenshot.assert_not_called()
        assert Path(report._log_file).exists()

    def test_pytest_runtest_makereport_failure_skips_screenshot_when_html_output_set(
        self,
        tmp_path: Path,
    ) -> None:
        """Skip manual screenshot capture when html_output is configured directly."""
        artifact_manager = build_artifact_manager(tmp_path)
        artifact_manager.create_directories()
        config = build_config()

        with (
            patch.object(ReportPlugin, "configure_logging"),
            patch.object(ReportPlugin, "set_config_metadata"),
        ):
            plugin = ReportPlugin(
                artifact_manager=artifact_manager,
                browser="chrome",
                config=config,
            )

        plugin.session_logger = MagicMock()
        driver = MagicMock()

        item_config = MagicMock()
        item_config.pluginmanager = MagicMock()
        item_config.pluginmanager.hasplugin.return_value = False
        item_config.option = SimpleNamespace(html_output="report.html")

        item = MagicMock()
        item.function.__doc__ = "failure doc"
        item.funcargs = {"driver": driver}
        item.name = "test_fail"
        item.config = item_config

        report = SimpleNamespace(
            when="call",
            outcome="failed",
            nodeid="tests/test_demo.py::test_fail",
            duration=0.5,
            skipped=False,
            failed=True,
            longrepr="traceback text",
        )
        outcome = MagicMock()
        outcome.get_result.return_value = report

        drive_hookwrapper(plugin.pytest_runtest_makereport(item, MagicMock()), outcome)

        driver.save_screenshot.assert_not_called()
        assert Path(report._log_file).exists()

    @patch("sel_py_template.utils.report_plugin.datetime")
    def test_pytest_runtest_makereport_failure_skips_screenshot_when_html_enabled(
        self,
        mock_datetime: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Skip manual screenshot capture when pytest-html-plus is active."""
        mock_datetime.now.return_value.strftime.return_value = "STAMP"
        artifact_manager = build_artifact_manager(tmp_path)
        artifact_manager.create_directories()
        config = build_config()
        with (
            patch.object(ReportPlugin, "configure_logging"),
            patch.object(ReportPlugin, "set_config_metadata"),
        ):
            plugin = ReportPlugin(
                artifact_manager=artifact_manager, browser="chrome", config=config
            )

        plugin.session_logger = MagicMock()
        driver = MagicMock()
        item_config = MagicMock()
        item_config.pluginmanager = MagicMock()
        item_config.pluginmanager.hasplugin.side_effect = lambda name: (
            name == "pytest_html_plus"
        )
        item_config.option = SimpleNamespace(html_output="report.html")

        item = MagicMock()
        item.function.__doc__ = "failure doc"
        item.funcargs = {"driver": driver}
        item.name = "test_fail"
        item.config = item_config

        report = SimpleNamespace(
            when="call",
            outcome="failed",
            nodeid="tests/test_demo.py::test_fail",
            duration=0.5,
            skipped=False,
            failed=True,
            longrepr="traceback text",
        )
        outcome = MagicMock()
        outcome.get_result.return_value = report

        drive_hookwrapper(plugin.pytest_runtest_makereport(item, MagicMock()), outcome)

        driver.save_screenshot.assert_not_called()
        assert Path(report._log_file).exists()

    def test_pytest_runtest_makereport_setup_phase_and_xfail_branch(
        self,
        tmp_path: Path,
    ) -> None:
        """Handle setup-phase reports and xfail-skipped reports as failures."""
        artifact_manager = build_artifact_manager(tmp_path)
        artifact_manager.create_directories()
        config = build_config()
        with (
            patch.object(ReportPlugin, "configure_logging"),
            patch.object(ReportPlugin, "set_config_metadata"),
        ):
            plugin = ReportPlugin(
                artifact_manager=artifact_manager, browser="chrome", config=config
            )

        plugin.session_logger = MagicMock()
        item = MagicMock()
        item.function.__doc__ = "xfail doc"
        item.funcargs = {}
        item.name = "test_xfail"
        item.config = MagicMock()
        item.config.pluginmanager = MagicMock()
        item.config.pluginmanager.hasplugin.return_value = False
        item.config.option = SimpleNamespace(html_output=None)

        report = SimpleNamespace(
            when="setup",
            outcome="skipped",
            nodeid="tests/test_demo.py::test_xfail",
            duration=0.1,
            skipped=True,
            failed=False,
            wasxfail=True,
            longrepr="xfail trace",
        )
        outcome = MagicMock()
        outcome.get_result.return_value = report

        drive_hookwrapper(plugin.pytest_runtest_makereport(item, MagicMock()), outcome)

        plugin.session_logger.info.assert_any_call("xx Failed Test %s", report.nodeid)
        assert Path(report._log_file).exists()

    def test_pytest_runtest_makereport_ignores_other_phases(
        self,
        tmp_path: Path,
    ) -> None:
        """Ignore teardown and other phases outside call/setup."""
        artifact_manager = build_artifact_manager(tmp_path)
        config = build_config()
        with (
            patch.object(ReportPlugin, "configure_logging"),
            patch.object(ReportPlugin, "set_config_metadata"),
        ):
            plugin = ReportPlugin(
                artifact_manager=artifact_manager, browser="chrome", config=config
            )

        plugin.session_logger = MagicMock()
        item = MagicMock()
        report = SimpleNamespace(
            when="teardown",
            outcome="passed",
            nodeid="tests/test_demo.py::test_teardown",
            duration=0.1,
        )
        outcome = MagicMock()
        outcome.get_result.return_value = report

        drive_hookwrapper(plugin.pytest_runtest_makereport(item, MagicMock()), outcome)

        assert plugin.test_reports == []

    def test_pytest_sessionfinish_logs_summary(self, tmp_path: Path) -> None:
        """Log session summary information for all recorded tests."""
        artifact_manager = build_artifact_manager(tmp_path)
        config = build_config()
        with (
            patch.object(ReportPlugin, "configure_logging"),
            patch.object(ReportPlugin, "set_config_metadata"),
            patch.object(
                ReportPlugin,
                "_get_environment_info",
                return_value={
                    "environment": "local",
                    "branch": "main",
                    "commit": "abc1234",
                    "generated_at": "2026-03-06T19:18:04",
                },
            ),
        ):
            plugin = ReportPlugin(
                artifact_manager=artifact_manager, browser="chrome", config=config
            )

        plugin.session_logger = MagicMock()
        plugin.test_reports = [
            {"nodeid": "test_pass", "outcome": "passed", "duration": 1.0},
            {"nodeid": "test_fail", "outcome": "failed", "duration": 2.0},
            {"nodeid": "test_skip", "outcome": "skipped", "duration": 3.0},
        ]

        plugin.pytest_sessionfinish(MagicMock(), 1)

        plugin.session_logger.info.assert_any_call(">> Test session finished")
        plugin.session_logger.debug.assert_any_call("Session exitstatus=%s", 1)
        plugin.session_logger.info.assert_any_call(
            "Test: %s - Outcome: %s - Duration: %.2fs",
            "test_pass",
            "PASSED",
            1.0,
        )

    def test_pytest_runtest_makereport_failure_with_no_config(
        self,
        tmp_path: Path,
    ) -> None:
        """Handle failure artifact logic when the pytest item has no config object."""
        artifact_manager = build_artifact_manager(tmp_path)
        artifact_manager.create_directories()
        config = build_config()

        with (
            patch.object(ReportPlugin, "configure_logging"),
            patch.object(ReportPlugin, "set_config_metadata"),
        ):
            plugin = ReportPlugin(
                artifact_manager=artifact_manager,
                browser="chrome",
                config=config,
            )

        plugin.session_logger = MagicMock()
        driver = MagicMock()

        item = MagicMock()
        item.function.__doc__ = "failure doc"
        item.funcargs = {"driver": driver}
        item.name = "test_fail"
        item.config = None

        report = SimpleNamespace(
            when="call",
            outcome="failed",
            nodeid="tests/test_demo.py::test_fail",
            duration=0.5,
            skipped=False,
            failed=True,
            longrepr="traceback text",
        )
        outcome = MagicMock()
        outcome.get_result.return_value = report

        drive_hookwrapper(plugin.pytest_runtest_makereport(item, MagicMock()), outcome)

        driver.save_screenshot.assert_called_once()
        assert Path(report._log_file).exists()
