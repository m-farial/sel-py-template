from pytest_a11y.types import ViolationDetails


def categorize_violations(violations: list[dict]) -> dict[str, list[dict]]:
    categorized = {
        "critical": [],
        "serious": [],
        "moderate": [],
        "minor": [],
    }

    for violation in violations:
        impact = violation.get("impact")
        if impact in categorized:
            categorized[impact].append(violation)

    return categorized


# def format_violation(violation: dict) -> str:
#     return (
#         f"[{violation.get('impact', 'N/A').upper()}] "
#         f"{violation.get('description', 'N/A')} "
#         f"(rule: {violation.get('id', 'N/A')}, "
#         f"affected nodes: {len(violation.get('nodes', []))})"
#     )


# def assert_accessibility(
#     violations,
#     driver=None,
#     test_name="accessibility_test",
#     fail_on=("critical", "serious"),
# ):
#     categorized = categorize_violations(violations)

#     errors = []
#     warnings = []

#     for impact, items in categorized.items():
#         for item in items:
#             message = format_violation(item)

#             if impact in fail_on:
#                 screenshot = None
#                 if driver:
#                     screenshot = save_violation_screenshot(
#                         driver,
#                         test_name,
#                         item["id"],
#                         impact,
#                     )

#                 if screenshot:
#                     message += f"\n  Screenshot: {screenshot}"

#                 errors.append(message)
#             else:
#                 warnings.append(message)

#     for warning in warnings:
#         print(f"A11Y WARNING: {warning}")

#     if errors:
#         raise AssertionError("Accessibility violations found:\n" + "\n".join(errors))


def assert_no_axe_violations(results: dict):
    violations = results.get("violations", [])
    if violations:
        messages = [f"{v['id']} ({len(v['nodes'])} nodes)" for v in violations]
        raise AssertionError("axe violations found:\n" + "\n".join(messages))


def format_violation_summary(violation: dict) -> str:
    """Format the main violation summary line"""
    return (
        f"[{violation.get('impact', 'N/A').upper()}] "
        f"{violation.get('description', 'N/A')} "
        f"(rule: {violation.get('id', 'N/A')}, "
        f"affected nodes: {len(violation['nodes'])})"
    )


def extract_violation_details(violation: dict) -> ViolationDetails:
    """Extract detailed information from a violation"""
    return {
        "summary": format_violation_summary(violation),
        "help": violation.get("help", "N/A"),
        "helpUrl": violation.get("helpUrl", ""),
        "nodes": violation.get("nodes", []),
        "tags": violation.get("tags", []),
    }


def format_nodes_html(nodes: list) -> str:
    """Format nodes as HTML list"""
    if not nodes:
        return "<p><em>No affected nodes</em></p>"

    html_items = []
    for node in nodes:
        target = node.get("target", ["unknown"])[0] if node.get("target") else "unknown"
        html_element = node.get("html", "")
        failure_summary = node.get("failureSummary", "No details available")

        html_items.append(
            f"""
        <div class="node-item">
            <strong>Selector:</strong> <code>{target}</code><br>
            <strong>Issue:</strong> {failure_summary}<br>
            <details class="node-html">
                <summary>View HTML</summary>
                <pre><code>{html_element}</code></pre>
            </details>
        </div>
        """
        )

    return "".join(html_items)


def format_tags_html(tags: list) -> str:
    """Format tags as HTML badges"""
    if not tags:
        return "<em>No tags</em>"

    tag_badges = " ".join(f'<span class="tag">{tag}</span>' for tag in tags)
    return tag_badges
