"""
Generate HTML reports from axe-core results.

Entry point for creating interactive HTML reports from accessibility checks.
Integrates with captured violation screenshots for visual representation.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.pytest_axe_a11y.types import AxeResults

from src.pytest_axe_a11y.reporting.report_generator import (
    A11yViolationsReport,
    ReportViolation,
    AxeNode,
)


def generate_a11y_report(
    axe_results: AxeResults | None,
    page_url: str,
    output_path: str | Path,
    screenshot_dir: str | Path | None = None,
) -> None:
    """
    Generate an interactive HTML report from axe-core results.
    
    Creates a standalone HTML file with clickable violation cards,
    detailed node information, and optional per-violation screenshots.
    
    Screenshots are embedded using relative paths from the report file location,
    making the report portable and shareable.
    
    Args:
        axe_results: Complete AxeResults from axe.run() or None if not run
        page_url: URL of the page that was analyzed
        output_path: File path where HTML report will be written
        screenshot_dir: Directory containing per-violation screenshots
                       (optional, screenshots linked if provided)
    
    Example:
        >>> from pathlib import Path
        >>> generate_a11y_report(
        ...     axe_results=results,
        ...     page_url="https://example.com",
        ...     output_path="reports/a11y.html",
        ...     screenshot_dir="reports/violation_screenshots"
        ... )
    """
    # Convert string paths to Path objects
    output_path = Path(output_path) if isinstance(output_path, str) else output_path
    screenshot_dir = Path(screenshot_dir) if screenshot_dir else None
    
    # Create report generator
    report = A11yViolationsReport(
        output_path=output_path,
        page_url=page_url,
    )
    
    # Add violations if results exist
    if axe_results:
        violations = axe_results.get("violations", [])
        for v_index, violation in enumerate(violations, start=1):
            # Convert nodes from axe format to AxeNode dataclass
            nodes = [
                AxeNode(
                    target=node.get("target", ["unknown"])[0] if node.get("target") else "unknown",
                    html=node.get("html", ""),
                    failure_summary=node.get("failureSummary", "No details available"),
                    impact=node.get("impact"),
                )
                for node in violation.get("nodes", [])
            ]
            
            # Determine screenshot path if directory provided
            screenshot_path = ""
            if screenshot_dir and screenshot_dir.exists():
                violation_id = violation.get("id", "unknown")
                screenshot_file = screenshot_dir / f"{v_index}_{violation_id}.png"
                if screenshot_file.exists():
                    # Compute relative path from report file to screenshot
                    try:
                        relative_path = screenshot_file.relative_to(output_path.parent)
                        screenshot_path = relative_path.as_posix()
                    except ValueError:
                        # If paths don't share a common base, use absolute path
                        screenshot_path = screenshot_file.as_posix()
            
            # Create report violation
            report_violation = ReportViolation(
                name=violation.get("id", "unknown"),
                summary=_format_violation_summary(violation),
                help=violation.get("help", "N/A"),
                help_url=violation.get("helpUrl", ""),
                nodes=nodes,
                tags=violation.get("tags", []),
                screenshot=screenshot_path,
            )
            
            # Add to report
            report.add_violation(report_violation)
    
    # Generate the HTML report
    report.generate()


def _format_violation_summary(violation: dict) -> str:
    """
    Format violation summary from axe result.
    
    Creates a human-readable summary including impact level,
    description, rule ID, and affected node count.
    
    Args:
        violation: Violation dict from AxeResults
    
    Returns:
        Formatted summary string
    """
    impact = (violation.get("impact", "unknown") or "unknown").upper()
    description = violation.get("description", "Unknown violation")
    violation_id = violation.get("id", "unknown")
    nodes_count = len(violation.get("nodes", []))
    
    return (
        f"[{impact}] {description} "
        f"(rule: {violation_id}, affected nodes: {nodes_count})"
    )