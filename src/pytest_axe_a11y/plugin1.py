# from __future__ import annotations

# from collections.abc import Callable
# import hashlib
# import os

# import pytest
# from selenium.webdriver.remote.webdriver import WebDriver

# from src.pytest_axe_a11y.assertions import assert_no_axe_violations
# from src.pytest_axe_a11y.reporting.html_report import generate_a11y_report
# from src.pytest_axe_a11y.reporting.json_report import write_a11y_json_report
# from src.pytest_axe_a11y.screenshots import save_screenshot
# from src.pytest_axe_a11y.types import A11YRunResults, AxeResults, AxeRunnerProtocol
# from src.pytest_axe_a11y.visual.axe_overlay import highlight_axe_violations
# from src.utils.logger_util import LoggerFactory

# logger = LoggerFactory.get_logger(__name__)


# def pytest_addoption(parser: pytest.Parser) -> None:
#     """
#     Register CLI options for accessibility testing.
#     """
#     parser.addoption(
#         "--a11y",
#         action="store_true",
#         default=False,
#         help="Run axe-core accessibility checks (and generate reports).",
#     )


# def _safe_slug(text: str, max_len: int = 10) -> str:
#     """
#     Convert a string into a filesystem-friendly slug.

#     Args:
#         text: Input text (e.g., pytest test name).
#         max_len: Max length of the slug.

#     Returns:
#         A slug-safe string.
#     """
#     keep: list[str] = []
#     for ch in text:
#         if ch.isalnum() or ch in ("-", "_", "."):
#             keep.append(ch)
#         else:
#             keep.append("_")
#     slug = "".join(keep)
#     return slug[:max_len].strip("_") or "a11y"


# def _nodeid_hash(nodeid: str, length: int = 10) -> str:
#     """
#     Generate a stable hash for filenames (xdist-safe).

#     Uses blake2b for speed and to satisfy security linters.

#     Args:
#         nodeid: pytest nodeid (includes file path + test name + params).
#         length: Length of the hex string to return.

#     Returns:
#         Hex digest string truncated to the requested length.
#     """
#     # hexdigest length is 2 * digest_size bytes
#     digest_size = max(4, length // 2 + 1)
#     return hashlib.blake2b(nodeid.encode("utf-8"), digest_size=digest_size).hexdigest()[
#         :length
#     ]


# @pytest.fixture
# def check_a11y(
#     driver: WebDriver,
#     request: pytest.FixtureRequest,
#     axe: AxeRunnerProtocol,
# ) -> Callable[[], A11YRunResults]:
#     """
#     Run axe-core accessibility checks on demand.

#     CLI:
#         - If --a11y is NOT provided: this fixture will skip when invoked.
#         - If --a11y is provided: runs axe-core checks.

#     Reporting:
#         Writes:
#           - <log_dir>/reports_html/<safe_name>__<worker>__<hash>.html
#           - <log_dir>/reports_json/<safe_name>__<worker>__<hash>.json
#           - <log_dir>/reports_screenshots/<safe_name>__<worker>__<hash>__axe_overlay.png
#             (only when violations exist)

#         xdist-safe naming: worker_id + nodeid hash prevents collisions.

#     Returns:
#         A callable that executes the checks and returns a result dictionary.
#     """
#     enabled: bool = bool(request.config.getoption("--a11y"))
#     if not enabled:

#         def _skipped() -> A11YRunResults:
#             pytest.skip("Accessibility checks not enabled (use --a11y)")
#             raise RuntimeError("unreachable")  # for type checkers

#         return _skipped

#     # Resolve a11y directory
#     try:
#         a11y_dir = LoggerFactory.get_a11y_dir()
#     except Exception:
#         a11y_dir = os.getcwd()

#     # xdist-safe naming
#     worker_id = os.environ.get("PYTEST_XDIST_WORKER", "master")
#     nodeid = request.node.nodeid
#     name = _safe_slug(request.node.name)
#     h = _nodeid_hash(nodeid)

#     base = f"{name}__{worker_id}__{h}"
#     html_path = os.path.join(a11y_dir, f"{base}.html")
#     json_path = os.path.join(a11y_dir, f"{base}.json")
#     axe_overlay_path = os.path.join(a11y_dir, f"{base}__axe_overlay.png")

#     def _run() -> A11YRunResults:
#         """
#         Execute axe-core checks, write reports, optionally create overlay screenshot,
#         then assert on violations.
#         """
#         axe_results: AxeResults | None = axe.run()
#         overlay_screenshot: str | None = None
#         breakpoint()
#         if axe_results is not None and axe_results.get("violations"):
#             for axe_result in axe_results["violations"]:
#                 highlight_axe_violations(driver, axe_results)
#                 driver.execute_script(
#                     "return new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))"
#                 )
#                 overlay_screenshot = str(save_screenshot(driver, axe_overlay_path))

#         # Always write reports
#         generate_a11y_report(
#             axe_results=axe_results,
#             page_url=driver.current_url,
#             output_path=html_path,
#         )
#         write_a11y_json_report(
#             axe_results=axe_results,
#             page_url=driver.current_url,
#             output_path=json_path,
#         )
#         # Assert last (so reports/screenshots are written first)
#         if axe_results is not None:
#             assert_no_axe_violations(axe_results)

#         result: A11YRunResults = {
#             "axe": axe_results,
#             "html_report": html_path,
#             "json_report": json_path,
#         }
#         if overlay_screenshot is not None:
#             result["axe_overlay_screenshot"] = overlay_screenshot

#         return result

#     return _run
