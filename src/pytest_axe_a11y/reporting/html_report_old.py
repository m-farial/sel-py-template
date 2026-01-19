# from __future__ import annotations

# from dataclasses import dataclass
# from datetime import datetime, timezone
# from html import escape
# import json
# import os
# from pathlib import Path
# from typing import Any

# from pytest_axe_a11y.assertions import format_violation, categorize_violations,

# from src.utils.logger_util import LoggerFactory


# def _as_path(p: Path | str) -> Path:
#     return p if isinstance(p, Path) else Path(p)


# def _pretty_json(obj: Any) -> str:
#     """Pretty-print JSON safely for embedding in HTML <pre>."""
#     return escape(json.dumps(obj, indent=2, ensure_ascii=False))


# @dataclass(frozen=True)
# class _Counts:
#     axe_violations: int


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
#     # formatted_violations = [format_violation(v) for v in axe_violations]
#     breakpoint()

#     counts = _Counts(
#         axe_violations=len(axe_violations) if isinstance(axe_violations, list) else 0,
#     )

#     generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")

#     axe_status = "not run" if axe_results is None else "ran"

#     html = f"""\
# <!DOCTYPE html>
# <html lang="en">
# <head>
#   <meta charset="utf-8"/>
#   <title>Accessibility Report</title>
#   <style>
#     body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.4; }}
#     h1 {{ color: #333; margin-bottom: 0; }}
#     .meta {{ color: #555; margin-top: 6px; }}
#     h2 {{ margin-top: 28px; }}
#     .card {{ border: 1px solid #ddd; border-radius: 10px; padding: 14px 16px; margin-top: 12px; }}
#     .row {{ display: flex; gap: 18px; flex-wrap: wrap; }}
#     .pill {{ display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 12px; border: 1px solid #ccc; }}
#     .fail {{ color: #b00020; font-weight: bold; }}
#     .pass {{ color: #1b5e20; font-weight: bold; }}
#     pre {{ background: #f6f8fa; padding: 12px; overflow-x: auto; border-radius: 8px; border: 1px solid #eee; }}
#     .muted {{ color: #777; }}
#     a {{ color: inherit; }}
#     code {{ background: #f6f8fa; padding: 0 4px; border-radius: 4px; }}
#   </style>
# </head>
# <body>

# <h1>Accessibility Report</h1>
# <div class="meta">
#   <div><strong>URL:</strong> <a href="{escape(page_url)}">{escape(page_url)}</a></div>
#   <div><strong>Generated:</strong> {generated}</div>
# </div>

# <div class="card">
#   <h2 style="margin-top: 0;">Summary</h2>
#   <div class="row">
#     <div>
#       <div class="pill">axe-core: {axe_status}</div><br/>
#       <span class="{'fail' if counts.axe_violations else 'pass'}">
#         Violations: {counts.axe_violations}
#       </span>
#     </div>
#   </div>
#   <div class="muted" style="margin-top: 10px;">
#     Tip: Run <code>pytest --a11y</code>.
#   </div>
# </div>

# <h2>axe-core Results</h2>
# <div class="card">
#   <div class="pill">Status: {axe_status}</div>
#   <p class="{'fail' if counts.axe_violations else 'pass'}">
#     Violations: {counts.axe_violations}
#   </p>
#   <pre>{_pretty_json(axe_violations)}</pre>
# </div>

# </body>
# </html>
# """
#     out.write_text(html, encoding="utf-8")


# def write_html_report(results, test_name):
#     a11y_dir = LoggerFactory.get_a11y_dir() or os.getcwd()
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     path = a11y_dir / f"{test_name}_{timestamp}.html"
#     rows = []
#     for v in results["violations"]:
#         rows.append(
#             f"""
#             <tr>
#                 <td>{v['impact']}</td>
#                 <td>{v['id']}</td>
#                 <td>{v['description']}</td>
#                 <td>{len(v['nodes'])}</td>
#             </tr>
#             """
#         )

#     html = f"""
#     <html>
#     <head>
#         <title>Accessibility Report</title>
#         <style>
#             table {{ border-collapse: collapse; width: 100%; }}
#             th, td {{ border: 1px solid #ccc; padding: 8px; }}
#             th {{ background: #f4f4f4; }}
#         </style>
#     </head>
#     <body>
#         <h1>Accessibility Report: {test_name}</h1>
#         <table>
#             <tr>
#                 <th>Impact</th>
#                 <th>Rule</th>
#                 <th>Description</th>
#                 <th>Nodes</th>
#             </tr>
#             {''.join(rows)}
#         </table>
#     </body>
#     </html>
#     """

#     path.write_text(html, encoding="utf-8")
#     return str(path)
