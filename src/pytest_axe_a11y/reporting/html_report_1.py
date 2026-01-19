# from __future__ import annotations

# from datetime import datetime
# from pathlib import Path
# from typing import Any

# from pytest_axe_a11y.assertions import (
#     extract_violation_details,
# )
# from pytest_axe_a11y.reporting.report_generator import A11yViolationsReport
# from src.utils.logger_util import LoggerFactory

# logger = LoggerFactory.get_logger(__name__)


# def _as_path(p: Path | str) -> Path:
#     return p if isinstance(p, Path) else Path(p)


# def generate_a11y_report(
#     *,
#     axe_results: dict[str, Any] | None,
#     page_url: str,
#     output_path: Path | str,
# ) -> None:
#     """
#     Generate a combined accessibility report in HTML format.

#     Args:
#         axe_results: Results from axe-core analysis, or None if not run.
#         page_url: URL of the page analyzed.
#         output_path: File path where the HTML report will be written.
#                      Accepts Path or str.

#     Notes:
#         - This function is resilient to missing engines (None results).
#         - JSON is HTML-escaped to prevent report corruption.
#     """
#     out = _as_path(output_path)
#     out.parent.mkdir(parents=True, exist_ok=True)

#     axe_violations = (axe_results or {}).get("violations", [])
#     date_str = datetime.now().strftime("%m-%d-%Y-%H:%M:%S")
#     report = A11yViolationsReport(f"reports/a11y_violations_{date_str}.html", page_url=page_url)
#     for violation in axe_violations:
#         details = extract_violation_details(violation)
#         # Add violation
#         report.add_violation(
#             name=violation["id"],
#             summary=details["summary"],
#             help_txt=details["help"],
#             help_url=details["helpUrl"],
#             nodes=details["nodes"],
#             tags=details["tags"],
#             screenshot="screenshots/aria-allowed-role.png",
#         )

#     # Generate the HTML report
#     report.generate()
#     logger.info(f"Accessibility HTML report generated at: {out.resolve()} \n")
