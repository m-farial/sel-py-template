from datetime import datetime
import logging
import logging.config
import os
import shutil
import subprocess
import sys
from typing import Any

import pytest


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

    @staticmethod
    def _get_git_executable() -> str | None:
        """
        Get the full path to git executable.

        Returns:
            Full path to git or None if not found
        """
        return shutil.which("git")

    @staticmethod
    def _is_git_repo() -> bool:
        """
        Check if current directory is a git repository.

        Returns:
            bool: True if in a git repository, False otherwise
        """
        git_path = ReportPlugin._get_git_executable()
        if not git_path:
            return False

        try:
            subprocess.run(  # noqa: S603
                [git_path, "rev-parse", "--git-dir"],
                capture_output=True,
                shell=False,
                check=True,
                timeout=5,
            )
            return True
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ):
            return False

    @staticmethod
    def _run_git_command(command: list[str]) -> str | None:
        """
        Run a git command safely and return output.

        Args:
            command: Git command as list of strings (first element should be 'git')

        Returns:
            Command output if successful, None otherwise
        """
        git_path = ReportPlugin._get_git_executable()
        if not git_path:
            return None

        if command[0] == "git":
            command = [git_path, *command[1:]]

        try:
            result = subprocess.run(  # noqa: S603
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
                stderr=subprocess.DEVNULL,
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError, TimeoutError):
            pass
        return None

    def _get_git_info(self) -> dict[str, str]:
        """
        Get git branch and commit information.

        Returns:
            Dict with 'branch' and 'commit' keys
        """
        # Check if we're in a git repository first
        if not self._is_git_repo():
            return {"branch": "NA", "commit": "NA"}

        # Get branch name
        branch = (
            self._run_git_command(["git", "rev-parse", "--abbrev-ref", "HEAD"]) or "NA"
        )

        # Get commit hash
        commit = self._run_git_command(["git", "rev-parse", "--short", "HEAD"]) or "NA"

        return {"branch": branch, "commit": commit}

    def _get_environment_info(self) -> dict[str, Any]:
        """
        Gather environment information for the test report.

        Returns:
            Dictionary containing environment details
        """
        # Get git information
        git_info = self._get_git_info()

        return {
            "report_title": datetime.now().strftime("%m-%d-%Y"),
            "environment": "NA",  # Can be set via environment variable or config
            "branch": git_info["branch"],
            "commit": git_info["commit"],
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "generated_at": datetime.now().isoformat(),
            "browser": self.browser,
        }

    def configure_logging(self):
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
        print(f"\n Logs will be stored in: {self.log_file}")

    @pytest.fixture(scope="session")
    def logger(self, request: pytest.FixtureRequest) -> logging.Logger:
        return request.config._logger  # type: ignore

    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_runtest_makereport(self, item: pytest.Item, call: pytest.CallInfo):
        outcome = yield
        report = outcome.get_result()
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

                if driver:
                    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
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
                log_path = os.path.join(self.base_log_dir, f"{item.name}_failure.log")
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write(f"Test failed: {item.name}\n")
                    f.write(str(report.longrepr))
                report._log_file = log_path

            else:
                self.session_logger.info(f"xx Passed Test {report.nodeid}")

    # Hook: session summary
    @pytest.hookimpl(tryfirst=True)
    def pytest_sessionfinish(self, session, exitstatus):
        self.session_logger.info(">> Test session finished")
        total = len(self.test_reports)
        passed = sum(1 for t in self.test_reports if t["outcome"] == "passed")
        failed = sum(1 for t in self.test_reports if t["outcome"] == "failed")
        skipped = sum(1 for t in self.test_reports if t["outcome"] == "skipped")

        summary = (
            f"\n TEST SUMMARY \n"
            f"=====================\n"
            f" Passed : {passed}\n"
            f" Failed : {failed}\n"
            f" Skipped: {skipped}\n"
            f" Total  : {total}\n"
        )
        self.session_logger.info(summary)
        for tr in self.test_reports:
            self.session_logger.info(
                f"Test: {tr['nodeid']} - Outcome: {tr['outcome'].upper()} - Duration: {tr['duration']:.2f}s"
            )
