import json
import logging
import logging.config
import os
from collections.abc import Generator
from datetime import datetime
from typing import Any

import pytest
from dulwich.repo import Repo
from pytest_html_plus.utils import get_python_version


class ReportPlugin:
    def __init__(
        self,
        logs_dir: str,
        browser: str | None = None,
        config: pytest.Config | None = None,
    ):
        self.browser = browser or "generic"
        self.test_reports = []  # type: ignore
        self.base_log_dir = logs_dir
        os.makedirs(self.base_log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%H-%M-%S")
        self.log_file = os.path.join(
            self.base_log_dir, f"{self.browser}_test_run_{timestamp}.log"
        )
        # Configure logging and keep the session logger on the instance
        self.configure_logging()
        self.session_logger = logging.getLogger(f"app.{self.browser}")
        config._logger = self.session_logger  # type: ignore
        self.set_config_metadata(config)

    def _get_git_info(self) -> dict[str, str]:
        """
        Retrieve git branch and commit information.

        Returns:
            Dictionary with 'branch' and 'commit' keys
        """
        git_info = {"branch": "NA", "commit": "NA"}
        try:
            repo = Repo(".")
            # read_ref API is typed to use Ref objects; dulwich may return bytes at runtime
            head = repo.refs.read_ref(b"HEAD")  # type: ignore[arg-type]
            branch = (
                (head.decode() if isinstance(head, (bytes, bytearray)) else str(head))
                .replace("refs/heads/", "")
                .replace("ref: ", "")
            )
            # Get current commit; index access is untyped for the Repo mapping
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
        """
        Gather environment information for the test report.

        Returns:
            Dictionary containing environment details
        """
        git_info = self._get_git_info()

        return {
            "branch": git_info["branch"],
            "commit": git_info["commit"],
            "python_version": get_python_version(),
            "generated_at": datetime.now().isoformat(),
            "browser": self.browser,
        }

    def set_config_metadata(self, config: pytest.Config | None) -> None:
        """Set metadata for pytest-html-plus reports."""
        if config is None:
            return
        env = self._get_environment_info()
        # Precedence: cli_title > env_title > default
        cli_title = config.getoption("report_title", None)
        try:
            ini_title = config.getini("report_title")
        except Exception:
            ini_title = None
        env_title = os.getenv("REPORT_TITLE", None)
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
        logging_config = {
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
                    "level": "DEBUG",
                    "formatter": "detailed",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "class": "logging.FileHandler",
                    "level": "DEBUG",
                    "formatter": "detailed",
                    "filename": self.log_file,
                    "mode": "w",
                    "encoding": "utf-8",
                },
            },
            "loggers": {
                f"app.{self.browser}": {
                    "level": "DEBUG",
                    "handlers": ["console", "file"],
                    "propagate": False,  # prevent double logging
                },
            },
            "root": {"level": "WARNING", "handlers": ["console"]},
        }

        logging.config.dictConfig(logging_config)

    @pytest.fixture(scope="session")
    def logger(self, request: pytest.FixtureRequest) -> logging.Logger:
        return request.config._logger  # type: ignore

    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_runtest_makereport(
        self, item: pytest.Item, call: pytest.CallInfo[None]
    ) -> Generator[None, None, None]:
        outcome: Any = yield
        report = outcome.get_result()
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        if report.when in ("call", "setup"):
            self.session_logger.info(f">> Started Test {report.nodeid}")
            report.description = str(item.function.__doc__)  # type: ignore
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
                self.session_logger.info(f"xx Failed Test {report.nodeid}")

                driver = item.funcargs.get("driver", None)  # type: ignore
                report.driver = driver
                # detection of pytest-html-plus (or similar html plugin)
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
                # take screenshot only if driver exists AND html plugin is NOT enabled
                if driver and not html_plus_enabled:
                    screenshot_path = os.path.join(
                        self.base_log_dir, f"{item.name}_{timestamp}.png"
                    )
                    driver.save_screenshot(screenshot_path)
                    screenshot_path = screenshot_path.replace("\\", "/")
                    report._screenshot_path = screenshot_path
                    self.session_logger.info(
                        f">> Screenshot saved to: {screenshot_path}"
                    )

                # Write failure log
                log_path = os.path.join(
                    self.base_log_dir, f"{item.name}_{timestamp}_failure.log"
                )
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write(f"Test failed: {item.name}\n")
                    f.write(str(report.longrepr))
                report._log_file = log_path

            else:
                self.session_logger.info(f"xx Passed Test {report.nodeid}")

    @pytest.hookimpl(tryfirst=True)
    def pytest_sessionstart(self, session: pytest.Session) -> None:
        """Write pytest-html-plus compatible plus_metadata.json into the report folder early.

        This ensures the HTML generator can pick up git/branch info even when pytest-html-plus
        does not pass through those values from the CLI.
        """
        try:
            html_output = getattr(
                getattr(session, "config", None), "option", None
            ) and getattr(session.config.option, "html_output", None)

            if html_output:
                plus_meta_path = os.path.join(html_output, "plus_metadata.json")
                with open(plus_meta_path, "w", encoding="utf-8") as pm:
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
                        pm,
                        indent=2,
                    )

        except Exception as e:
            # Non-fatal; useful for diagnostics
            if self.session_logger:
                self.session_logger.debug(
                    "Could not write plus_metadata.json at session start: %s", e
                )

    # Hook: session summary
    @pytest.hookimpl(tryfirst=True)
    def pytest_sessionfinish(self, session: pytest.Session, exitstatus: int) -> None:
        self.session_logger.info(">> Test session finished")
        total = len(self.test_reports)
        passed = sum(1 for t in self.test_reports if t["outcome"] == "passed")
        failed = sum(1 for t in self.test_reports if t["outcome"] == "failed")
        skipped = sum(1 for t in self.test_reports if t["outcome"] == "skipped")

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
        for tr in self.test_reports:
            self.session_logger.info(
                f"Test: {tr['nodeid']} - Outcome: {tr['outcome'].upper()} - Duration: {tr['duration']:.2f}s"
            )
