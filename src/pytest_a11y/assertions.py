"""
Assertion and validation utilities for a11y testing.

Provides functions for validating axe-core results, categorizing violations,
and formatting violation data for display and reporting.
"""
from __future__ import annotations

from html import escape
from typing import Literal

from src.pytest_a11y.types import (
    AxeResults,
    AxeViolation,
    AxeNode,
    Severity,
)


# ============================================================================
# Violation categorization
# ============================================================================

def categorize_violations(violations: list[AxeViolation]) -> dict[Severity, list[AxeViolation]]:
    """
    Categorize violations by impact severity level.
    
    Groups violations into buckets by their impact level (critical, serious,
    moderate, minor) for easier analysis and reporting.
    
    Args:
        violations: List of violation dicts from AxeResults
        
    Returns:
        Dict mapping severity level to list of violations at that level.
        All keys present even if no violations at that level (empty list).
        
    Example:
        >>> violations = [
        ...     {"impact": "critical", "id": "rule1", ...},
        ...     {"impact": "critical", "id": "rule2", ...},
        ...     {"impact": "serious", "id": "rule3", ...},
        ... ]
        >>> categorized = categorize_violations(violations)
        >>> len(categorized["critical"])
        2
        >>> len(categorized["serious"])
        1
    """
    categorized: dict[Severity, list[AxeViolation]] = {
        "critical": [],
        "serious": [],
        "moderate": [],
        "minor": [],
    }

    for violation in violations:
        impact = violation.get("impact")
        if impact in categorized:  # type: ignore
            categorized[impact].append(violation)  # type: ignore

    return categorized


# ============================================================================
# Assertions
# ============================================================================

def assert_no_axe_violations(results: AxeResults) -> None:
    """
    Assert that no violations exist in axe results.
    
    Raises AssertionError with formatted violation list if any violations found.
    Typically used to fail tests when a11y issues are detected.
    
    Args:
        results: Complete AxeResults from axe.run()
        
    Raises:
        AssertionError: If any violations found, with formatted violation summary
        
    Example:
        >>> results = axe_runner.run()
        >>> assert_no_axe_violations(results)  # Raises if violations exist
    """
    violations: list[AxeViolation] = results.get("violations", [])
    if violations:
        messages = [
            f"{v.get('id', 'unknown')} ({len(v.get('nodes', []))} nodes)"
            for v in violations
        ]
        raise AssertionError(
            "axe violations found:\n" + "\n".join(messages)
        )


def assert_no_critical_violations(results: AxeResults) -> None:
    """
    Assert that no critical violations exist in axe results.
    
    Less strict than assert_no_axe_violations() - only fails on critical issues.
    Useful for CI pipelines that want to warn on serious/moderate but fail on critical.
    
    Args:
        results: Complete AxeResults from axe.run()
        
    Raises:
        AssertionError: If any critical violations found
    """
    violations: list[AxeViolation] = results.get("violations", [])
    critical = [v for v in violations if v.get("impact") == "critical"]
    
    if critical:
        messages = [
            f"{v.get('id', 'unknown')} ({len(v.get('nodes', []))} nodes)"
            for v in critical
        ]
        raise AssertionError(
            "critical axe violations found:\n" + "\n".join(messages)
        )


# ============================================================================
# Violation formatting
# ============================================================================

def format_violation_summary(violation: AxeViolation) -> str:
    """
    Format a violation into a human-readable summary line.
    
    Combines impact level, description, rule ID, and affected node count
    into a single formatted string suitable for logs and reports.
    
    Args:
        violation: Single violation dict from AxeResults
        
    Returns:
        Formatted summary string
        
    Example:
        >>> violation = {"impact": "critical", "description": "Issue", ...}
        >>> summary = format_violation_summary(violation)
        >>> print(summary)
        [CRITICAL] Issue (rule: rule-id, affected nodes: 2)
    """
    impact = (violation.get("impact") or "unknown").upper()
    description = violation.get("description", "Unknown violation")
    violation_id = violation.get("id", "unknown")
    nodes_count = len(violation.get("nodes", []))
    
    return (
        f"[{impact}] {description} "
        f"(rule: {violation_id}, affected nodes: {nodes_count})"
    )


def extract_violation_details(violation: AxeViolation) -> dict:
    """
    Extract key details from a violation for display purposes.
    
    Pulls out help text, documentation URL, affected nodes, and tags
    from a violation dict for use in reports and detailed views.
    
    Args:
        violation: Single violation dict from AxeResults
        
    Returns:
        Dict with keys: summary, help, helpUrl, nodes, tags
        
    Note:
        This is a legacy function. Prefer ProcessedViolation.from_axe_violation()
        for new code as it provides better typing and structure.
    """
    return {
        "summary": format_violation_summary(violation),
        "help": violation.get("help", "N/A"),
        "helpUrl": violation.get("helpUrl", ""),
        "nodes": violation.get("nodes", []),
        "tags": violation.get("tags", []),
    }


# ============================================================================
# HTML formatting
# ============================================================================

# def format_nodes_html(nodes: list[AxeNode]) -> str:
#     """
#     Format a list of affected nodes as HTML.
    
#     Creates styled HTML elements showing each node's selector, failure reason,
#     and HTML snippet in an expandable details element.
    
#     Args:
#         nodes: List of node dicts from a violation
        
#     Returns:
#         HTML string with formatted nodes, or empty message if no nodes
        
#     Note:
#         HTML is properly escaped. Safe for embedding in HTML documents.
#     """
#     if not nodes:
#         return "<p><em>No affected nodes</em></p>"

#     html_items = []
#     for node in nodes:
#         # Extract target selector
#         targets = node.get("target", [])
#         target = targets[0] if isinstance(targets, list) and targets else "unknown"
        
#         # Get HTML snippet and failure reason
#         html_element = escape(node.get("html", ""))
#         failure_summary = escape(node.get("failureSummary", "No details available"))

#         html_items.append(
#             f"""
#         <div class="node-item">
#             <strong>Selector:</strong> <code>{escape(target)}</code><br>
#             <strong>Issue:</strong> {failure_summary}<br>
#             <details class="node-html">
#                 <summary>View HTML</summary>
#                 <pre><code>{html_element}</code></pre>
#             </details>
#         </div>
#         """
#         )

#     return "".join(html_items)


# def format_tags_html(tags: list[str]) -> str:
#     """
#     Format a list of tags as HTML badges.
    
#     Creates small colored badge elements for categorization tags
#     (e.g., 'wcag21aa', 'cat.forms', 'best-practice').
    
#     Args:
#         tags: List of tag strings from a violation
        
#     Returns:
#         HTML string with badge elements, or empty message if no tags
        
#     Note:
#         Tags are HTML-escaped. Safe for embedding in HTML documents.
#     """
#     if not tags:
#         return "<em>No tags</em>"

#     tag_badges = " ".join(
#         f'<span class="tag">{escape(tag)}</span>'
#         for tag in tags
#     )
#     return tag_badges


# def format_violation_html(violation: AxeViolation) -> str:
    """
    Format a complete violation as styled HTML.
    
    Combines summary, help text, documentation link, affected nodes,
    and categorization tags into a complete HTML representation.
    
    Args:
        violation: Single violation dict from AxeResults
        
    Returns:
        Complete HTML representation of the violation
        
    Note:
        HTML is properly escaped. This is a convenience function for
        creating detailed violation displays.
    """
    summary = format_violation_summary(violation)
    help_text = escape(violation.get("help", "N/A"))
    help_url = escape(violation.get("helpUrl", ""))
    nodes_html = format_nodes_html(violation.get("nodes", []))
    tags_html = format_tags_html(violation.get("tags", []))
    
    return f"""
    <div class="violation-summary">
        <h3>{escape(violation.get('description', 'Unknown'))}</h3>
        <p class="violation-impact">{summary}</p>
    </div>
    <div class="violation-help">
        <strong>Help:</strong> {help_text}
    </div>
    <div class="violation-documentation">
        <strong>Learn More:</strong>
        <a href="{help_url}" target="_blank" rel="noopener">{help_url}</a>
    </div>
    <div class="violation-nodes">
        <strong>Affected Nodes:</strong>
        {nodes_html}
    </div>
    <div class="violation-tags">
        <strong>Tags:</strong>
        {tags_html}
    </div>
    """