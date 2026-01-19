from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Literal

from selenium.webdriver.remote.webdriver import WebDriver

from pytest_axe_a11y.types import AxeResults

Severity = Literal["critical", "serious", "moderate", "minor", "unknown"]


@dataclass(frozen=True)
class OverlayStats:
    """Summary of what we attempted to mark vs what was actually marked."""

    attempted: int
    marked: int
    skipped_global: int
    not_found: int


# -------------------------
# JavaScript helpers
# -------------------------

_OVERLAY_INSTALL_JS: str = r"""
(() => {
  // Idempotent install of shared badge CSS (badges use inline positioning)
  if (document.getElementById("__pytest_a11y_overlay_style__")) return true;

  const style = document.createElement("style");
  style.id = "__pytest_a11y_overlay_style__";
  style.textContent = `
    [data-pytest-a11y="badge"]{
      position: fixed !important;
      z-index: 2147483647 !important;
      color: #fff !important;
      font-size: 12px !important;
      padding: 2px 6px !important;
      border-radius: 4px !important;
      font-family: Arial, sans-serif !important;
      line-height: 1.2 !important;
      white-space: nowrap !important;
      box-shadow: 0 1px 3px rgba(0,0,0,.25) !important;
      pointer-events: none !important;
    }
  `;
  document.head.appendChild(style);
  return true;
})();
"""

_OVERLAY_CLEAR_JS: str = r"""
(() => {
  document.querySelectorAll('[data-pytest-a11y="badge"]').forEach(b => b.remove());
  // Remove outlines we set (we tag the element so we don't remove user styles)
  document.querySelectorAll('[data-pytest-a11y="outlined"]').forEach(el => {
    el.style.outline = "";
    el.style.outlineOffset = "";
    el.removeAttribute("data-pytest-a11y");
  });
  const style = document.getElementById("__pytest_a11y_overlay_style__");
  if (style) style.remove();
  return true;
})();
"""

_MARK_JS: str = r"""
const selector = arguments[0];
const badgeText = arguments[1];
const color = arguments[2];
const offsetY = arguments[3];

const el = document.querySelector(selector);
if (!el) return {ok:false, selector, reason:"not_found"};

// Outline inline (most reliable; avoids CSP/style issues)
el.style.outline = `4px solid ${color}`;
el.style.outlineOffset = "2px";
el.setAttribute("data-pytest-a11y", "outlined");

// Badge attached to body (works for <input> and other void elements)
const rect = el.getBoundingClientRect();
const badge = document.createElement("div");
badge.textContent = badgeText;
badge.setAttribute("data-pytest-a11y", "badge");

badge.style.background = color;
badge.style.left = `${Math.max(0, rect.left)}px`;
badge.style.top  = `${Math.max(0, rect.top - 20 + offsetY)}px`;

document.body.appendChild(badge);

return {ok:true, selector, tag: el.tagName, id: el.id};
"""


# -------------------------
# Python helpers
# -------------------------


def _to_severity(impact: object) -> Severity:
    """Normalize axe 'impact' to a known severity."""
    if isinstance(impact, str):
        value = impact.lower().strip()
        if value in ("critical", "serious", "moderate", "minor"):
            return value  # type: ignore[return-value]
    return "unknown"


def _severity_color(sev: Severity) -> str:
    """
    Map severity to a stable color.

    Note: using hex strings keeps it consistent across browsers/headless.
    """
    return {
        "critical": "#b00020",  # deep red
        "serious": "#e65100",  # orange
        "moderate": "#f9a825",  # amber
        "minor": "#1565c0",  # blue
        "unknown": "#616161",  # gray
    }[sev]


def _is_global_selector(selector: str) -> bool:
    """Skip global/root selectors that don't help visually."""
    s = selector.strip().lower()
    return s in ("html", "body", "*")


def _iter_targets(
    results: AxeResults, *, max_nodes_per_violation: int | None
) -> Iterable[tuple[int, str, Severity]]:
    """
    Yield tuples: (violation_index, selector, severity).

    Filters out non-list targets and normalizes severity.
    """
    violations: list[Mapping[str, Any]] = results.get("violations", [])
    for v_index, violation in enumerate(violations, start=1):
        sev = _to_severity(violation.get("impact"))
        nodes: list[Mapping[str, Any]] = violation.get("nodes", [])

        if max_nodes_per_violation is not None:
            nodes = nodes[:max_nodes_per_violation]

        for node in nodes:
            targets = node.get("target")
            if not isinstance(targets, list):
                continue
            for sel in targets:
                if isinstance(sel, str) and sel.strip():
                    yield (v_index, sel.strip(), sev)


def install_overlay(driver: WebDriver) -> None:
    """Install overlay CSS (idempotent)."""
    driver.execute_script(_OVERLAY_INSTALL_JS)


def clear_overlay(driver: WebDriver) -> None:
    """Remove overlay badges/outlines (best-effort)."""
    driver.execute_script(_OVERLAY_CLEAR_JS)


def highlight_axe_violations(
    driver: WebDriver,
    results: AxeResults,
    *,
    scroll_into_view: bool = True,
    repaint_sync: bool = True,
    max_nodes_per_violation: int | None = 10,
    max_total_marks: int | None = 50,
) -> OverlayStats:
    """
    Visually mark axe violations on the current page by outlining target elements
    and placing a small badge near each target.

    - Works with <input> (badges are appended to body)
    - Adds severity-based coloring (critical/serious/moderate/minor)
    - Filters out global selectors like html/body
    - Safe for headless screenshots (optional repaint sync)

    Args:
        driver: Selenium WebDriver instance.
        results: axe results dict containing "violations".
        scroll_into_view: Scroll each target into view before marking.
        repaint_sync: Wait for 2 animation frames to ensure DOM paint before screenshot.
        max_nodes_per_violation: Limit targets per violation to reduce noise.
        max_total_marks: Limit total number of marked targets across all violations.

    Returns:
        OverlayStats describing overlay application.
    """
    install_overlay(driver)

    attempted = 0
    marked = 0
    skipped_global = 0
    not_found = 0

    # Small vertical offset to avoid badge overlap when multiple targets are close
    badge_offset_y = 0

    for v_index, selector, sev in _iter_targets(
        results, max_nodes_per_violation=max_nodes_per_violation
    ):
        if max_total_marks is not None and attempted >= max_total_marks:
            break

        attempted += 1

        if _is_global_selector(selector):
            skipped_global += 1
            continue

        if scroll_into_view:
            driver.execute_script(
                """
                const el = document.querySelector(arguments[0]);
                if (el) el.scrollIntoView({block:'center', inline:'center'});
                """,
                selector,
            )

        color = _severity_color(sev)
        badge_text = f"{v_index}: {results.get('violations', [])[v_index - 1].get('id', 'rule')!s}"

        res = driver.execute_script(
            _MARK_JS, selector, badge_text, color, badge_offset_y
        )
        if isinstance(res, dict) and res.get("ok"):
            marked += 1
            badge_offset_y = (badge_offset_y + 14) % 56
        else:
            not_found += 1

    if repaint_sync:
        driver.execute_script(
            "return new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))"
        )

    return OverlayStats(
        attempted=attempted,
        marked=marked,
        skipped_global=skipped_global,
        not_found=not_found,
    )
