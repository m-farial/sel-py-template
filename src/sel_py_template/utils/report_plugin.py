from __future__ import annotations

from collections.abc import Generator
from datetime import datetime
import json
import logging
import logging.config
from pathlib import Path
from typing import Any

from dulwich.repo import Repo
import pytest
from pytest_html_plus.utils import get_python_version

from sel_py_template.utils.artifact_manager import ArtifactManager


class ReportPlugin:
    """Pytest plugin that manages run-level logging and reporting metadata."""

    def __init__(
        self,
        artifact_manager: ArtifactManager,
        browser: str | None = None,
        config: pytest.Config | None = None,
    ) -> None:
        """Initialize the report plugin.

        Args:
            artifact_manager: Artifact manager for the current test run.
            browser: Active browser name.
            config: Pytest configuration object.
        """
        self.browser = browser or "generic"
        self.artifact_manager = artifact_manager
        self.test_reports: list[dict[str, Any]] = []
        self.base_log_dir = str(self.artifact_manager.paths.run_root)
        self.log_file = str(self.artifact_manager.paths.log_file)
        self.config = config
        self.configure_logging()
        self.session_logger = logging.getLogger(f"app.{self.browser}")
        if config is not None:
            config._logger = self.session_logger  # type: ignore[attr-defined]
        self.set_config_metadata(config)

    def _get_git_info(self) -> dict[str, str]:
        """Retrieve git branch and commit information."""
        git_info = {"branch": "NA", "commit": "NA"}
        try:
            repo = Repo(".")
            head = repo.refs.read_ref(b"HEAD")  # type: ignore[arg-type]
            branch = (
                (head.decode() if isinstance(head, (bytes, bytearray)) else str(head))
                .replace("refs/heads/", "")
                .replace("ref: ", "")
            )
            commit_obj = repo[b"HEAD"]
            commit_sha = getattr(commit_obj, "id", None)
            if isinstance(commit_sha, (bytes, bytearray)):
                commit = commit_sha.decode()[:7]
            else:
                commit = None
            git_info["commit"] = commit if commit else "NA"
            git_info["branch"] = branch if branch else "NA"
        except Exception:
            self.session_logger.warning(
                "Dulwich not available or repository not found; cannot retrieve git information."
            )
        return git_info

    def _get_environment_info(self) -> dict[str, Any]:
        """Gather environment information for reporting."""
        git_info = self._get_git_info()
        return {
            "branch": git_info["branch"],
            "commit": git_info["commit"],
            "python_version": get_python_version(),
            "generated_at": datetime.now().isoformat(),
            "browser": self.browser,
        }

    def set_config_metadata(self, config: pytest.Config | None) -> None:
        """Set metadata values consumed by pytest-html-plus."""
        if config is None:
            return

        env = self._get_environment_info()
        cli_title = config.getoption("report_title", None)
        try:
            ini_title = config.getini("report_title")
        except Exception:
            ini_title = None
        env_title = None
        report_title = cli_title or ini_title or env_title or "Template tests report"

        if not getattr(config.option, "html_title", None):
            config.option.html_title = report_title
        config.option.environment = env.get("environment", "NA")
        config.option.git_branch = env.get("branch", "NA")
        config.option.git_commit = env.get("commit", "NA")
        config.option.python_version = env.get("python_version", "NA")
        config.option.browser = env.get("browser", "NA")
        config.option.generated_at = env.get("generated_at", "NA")

    def configure_logging(self) -> None:
        """Configure console and file logging for the current run."""
        cli_level = "INFO"
        file_level = "DEBUG"

        if self.config is not None:
            cli_option = self.config.getoption("log_cli_level")
            file_option = self.config.getoption("log_file_level")
            cli_level = str(cli_option or "INFO").upper()
            file_level = str(file_option or "DEBUG").upper()

        logging_config: dict[str, Any] = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "detailed": {
                    "format": "%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": cli_level,
                    "formatter": "detailed",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "class": "logging.FileHandler",
                    "level": file_level,
                    "formatter": "detailed",
                    "filename": self.log_file,
                    "mode": "w",
                    "encoding": "utf-8",
                },
            },
            "loggers": {
                "app": {
                    "level": file_level,
                    "handlers": ["console", "file"],
                    "propagate": False,
                },
                f"app.{self.browser}": {
                    "level": file_level,
                    "handlers": ["console", "file"],
                    "propagate": False,
                },
                # Silence noisy libraries
                "selenium": {
                    "level": "WARNING",
                },
                "urllib3": {
                    "level": "WARNING",
                },
                "urllib3.connectionpool": {
                    "level": "WARNING",
                },
            },
            "root": {"level": "WARNING", "handlers": ["console"]},
        }
        logging.config.dictConfig(logging_config)

    @pytest.fixture(scope="session")
    def logger(self, request: pytest.FixtureRequest) -> logging.Logger:
        """Return the session logger created for this plugin."""
        return request.config._logger  # type: ignore[attr-defined, no-any-return]

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_logstart(
        self,
        nodeid: str,
    ) -> None:
        """Write a clear start section for each test."""
        self.session_logger.info("=" * 50)
        self.session_logger.debug("Test: %s", nodeid)

    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_runtest_makereport(
        self,
        item: pytest.Item,
        call: pytest.CallInfo[None],
    ) -> Generator[None, None, None]:
        """Capture per-test report details and write failure artifacts when needed."""
        outcome: Any = yield
        report = outcome.get_result()
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        self.session_logger.debug(
            "makereport phase=%s outcome=%s nodeid=%s duration=%.4fs",
            report.when,
            report.outcome,
            report.nodeid,
            report.duration,
        )

        if report.when in ("call", "setup"):
            self.session_logger.info(">> Started Test %s", report.nodeid)
            report.description = str(item.function.__doc__)  # type: ignore[attr-defined]
            self.test_reports.append(
                {
                    "when": report.when,
                    "outcome": report.outcome,
                    "duration": report.duration,
                    "nodeid": report.nodeid,
                }
            )

            xfail = hasattr(report, "wasxfail")
            if (report.skipped and xfail) or (report.failed and not xfail):
                self.session_logger.info("xx Failed Test %s", report.nodeid)

                driver = item.funcargs.get("driver", None)  # type: ignore[attr-defined]
                report.driver = driver
                config = getattr(item, "config", None)
                html_plus_enabled = False
                if config:
                    pm = getattr(config, "pluginmanager", None)
                    html_plus_enabled = bool(
                        (
                            pm
                            and (
                                pm.hasplugin("pytest_html_plus") or pm.hasplugin("html")
                            )
                        )
                        or getattr(config.option, "html_output", None)
                    )

                self.session_logger.debug(
                    "Failure artifact collection started nodeid=%s html_plus_enabled=%s driver_present=%s",
                    report.nodeid,
                    html_plus_enabled,
                    driver is not None,
                )

                if driver and not html_plus_enabled:
                    screenshot_path = self.artifact_manager.failure_screenshot_path(
                        item.name,
                        timestamp,
                    )
                    driver.save_screenshot(str(screenshot_path))
                    report._screenshot_path = str(screenshot_path).replace("\\", "/")
                    self.session_logger.info(
                        ">> Screenshot saved to: %s",
                        report._screenshot_path,
                    )

                log_path = self.artifact_manager.failure_log_path(item.name, timestamp)
                with log_path.open("w", encoding="utf-8") as file_handle:
                    file_handle.write(f"Test failed: {item.name}\n")
                    file_handle.write(str(report.longrepr))
                report._log_file = str(log_path)
                self.session_logger.debug("Failure log saved to: %s", report._log_file)
            else:
                self.session_logger.info("xx Passed Test %s", report.nodeid)
                self.session_logger.debug(
                    "Test completed successfully nodeid=%s when=%s",
                    report.nodeid,
                    report.when,
                )

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_logfinish(
        self,
        nodeid: str,
        location: tuple[str, int | None, str],
    ) -> None:
        """Write a clear finish section for each test."""
        self.session_logger.info("-" * 80)
        self.session_logger.info("TEST END  : %s", nodeid)
        self.session_logger.info("-" * 80)

    @pytest.hookimpl(tryfirst=True)
    def pytest_sessionstart(self, session: pytest.Session) -> None:
        """Write ``plus_metadata.json`` into the pytest HTML folder early in the run."""
        try:
            plus_meta_path: Path = self.artifact_manager.paths.pytest_metadata_file
            with plus_meta_path.open("w", encoding="utf-8") as file_handle:
                json.dump(
                    {
                        "report_title": session.config.option.html_title,
                        "environment": session.config.option.environment,
                        "branch": session.config.option.git_branch,
                        "commit": session.config.option.git_commit,
                        "python_version": session.config.option.python_version,
                        "generated_at": session.config.option.generated_at,
                        "browser": session.config.option.browser,
                    },
                    file_handle,
                    indent=2,
                )
            self.session_logger.debug(
                "Wrote plus metadata file to: %s",
                plus_meta_path,
            )
        except Exception as error:
            self.session_logger.debug(
                "Could not write plus_metadata.json at session start: %s",
                error,
            )

    @pytest.hookimpl(tryfirst=True)
    def pytest_sessionfinish(self, session: pytest.Session, exitstatus: int) -> None:
        """Write a run summary into the session log at the end of execution."""
        self.session_logger.info(">> Test session finished")
        self.session_logger.debug("Session exitstatus=%s", exitstatus)
        total = len(self.test_reports)
        passed = sum(
            1 for test_report in self.test_reports if test_report["outcome"] == "passed"
        )
        failed = sum(
            1 for test_report in self.test_reports if test_report["outcome"] == "failed"
        )
        skipped = sum(
            1
            for test_report in self.test_reports
            if test_report["outcome"] == "skipped"
        )

        env = self._get_environment_info()
        environment = (
            f"\n EXECUTION METADATA \n"
            f"=====================\n"
            f" Environment : {env.get('environment', 'NA')}\n"
            f" Branch : {env.get('branch', 'NA')}\n"
            f" Commit: {env.get('commit', 'NA')}\n"
            f" Generated At : {env.get('generated_at', 'NA')}\n"
        )
        summary = (
            f"\n TEST SUMMARY \n"
            f"=====================\n"
            f" Passed : {passed}\n"
            f" Failed : {failed}\n"
            f" Skipped: {skipped}\n"
            f" Total  : {total}\n"
        )
        self.session_logger.info(f"{environment}\n{summary}")
        for test_report in self.test_reports:
            self.session_logger.info(
                "Test: %s - Outcome: %s - Duration: %.2fs",
                test_report["nodeid"],
                test_report["outcome"].upper(),
                test_report["duration"],
            )
