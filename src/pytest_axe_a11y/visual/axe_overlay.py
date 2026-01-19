"""
Per-violation screenshot capture for a11y violations.

Captures individual screenshots for each violation with visual highlighting
instead of one screenshot with all violations marked together.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Any
from selenium.webdriver.remote.webdriver import WebDriver

from src.pytest_axe_a11y.types import AxeViolation, AxeResults


# ============================================================================
# Types
# ============================================================================

@dataclass
class ViolationScreenshot:
    """Result of capturing a single violation screenshot."""
    violation_id: str
    violation_index: int
    screenshot_path: Path
    marked_count: int


# ============================================================================
# Private utilities
# ============================================================================

def _iter_violation_selectors(
    violation: AxeViolation,
    *,
    max_nodes: int | None = None,
) -> Iterable[str]:
    """
    Yield CSS selectors for nodes affected by this violation.
    
    Filters out non-list targets and global selectors (html, body, *).
    
    Args:
        violation: Single violation from axe results
        max_nodes: Maximum number of nodes to yield (default: no limit)
        
    Yields:
        CSS selector strings for affected elements
    """
    nodes: list[Mapping[str, Any]] = violation.get("nodes", [])
    
    if max_nodes is not None:
        nodes = nodes[:max_nodes]
    
    for node in nodes:
        targets = node.get("target")
        if not isinstance(targets, list):
            continue
        for sel in targets:
            if isinstance(sel, str) and sel.strip() and not _is_global_selector(sel):
                yield sel.strip()


def _is_global_selector(selector: str) -> bool:
    """
    Check if selector is a global/root element that doesn't help visually.
    
    Args:
        selector: CSS selector string
        
    Returns:
        True if selector is html, body, or *
    """
    s = selector.strip().lower()
    return s in ("html", "body", "*")


def _severity_color(impact: str | None) -> str:
    """
    Map impact severity to a display color.
    
    Uses hex colors that are stable across browsers and headless environments.
    
    Args:
        impact: Impact level from axe (critical, serious, moderate, minor)
        
    Returns:
        Hex color code string
    """
    impact_lower = (impact or "unknown").lower().strip()
    return {
        "critical": "#b00020",   # deep red
        "serious": "#e65100",    # orange
        "moderate": "#f9a825",   # amber
        "minor": "#1565c0",      # blue
        "unknown": "#616161",    # gray
    }.get(impact_lower, "#616161")


def _mark_selector_on_page(
    driver: WebDriver,
    selector: str,
    label: str,
    color: str,
    badge_offset_y: int = 0,
) -> bool:
    """
    Mark a single selector on the current page with outline and badge.
    
    Adds a colored outline around the element and a fixed-position badge label
    near the element's top-left corner.
    
    Args:
        driver: Selenium WebDriver instance
        selector: CSS selector to mark
        label: Text label for the badge
        color: Hex color code for the outline and badge
        badge_offset_y: Vertical offset for badge positioning (default: 0)
        
    Returns:
        True if element was found and marked, False if not found
    """
    result = driver.execute_script(
        """
        const sel = arguments[0];
        const label = arguments[1];
        const color = arguments[2];
        const offsetY = arguments[3];
        
        const el = document.querySelector(sel);
        if (!el) return false;
        
        // Add outline
        el.style.outline = `3px solid ${color}`;
        el.style.outlineOffset = '2px';
        
        // Add badge
        const badge = document.createElement('div');
        badge.textContent = label;
        badge.style.position = 'fixed';
        badge.style.top = (el.getBoundingClientRect().top + offsetY) + 'px';
        badge.style.left = (el.getBoundingClientRect().left - 30) + 'px';
        badge.style.background = color;
        badge.style.color = 'white';
        badge.style.padding = '4px 8px';
        badge.style.borderRadius = '3px';
        badge.style.fontSize = '11px';
        badge.style.fontWeight = 'bold';
        badge.style.zIndex = '999999';
        badge.style.whiteSpace = 'nowrap';
        badge.className = 'a11y-violation-badge';
        document.body.appendChild(badge);
        
        return true;
        """,
        selector,
        label,
        color,
        badge_offset_y,
    )
    return bool(result)


def _cleanup_violation_marks(driver: WebDriver) -> None:
    """
    Remove all violation badges and outlines from the page.
    
    Cleans up visual markers added by _mark_selector_on_page().
    This is best-effort - some styles may persist if set via classes.
    
    Args:
        driver: Selenium WebDriver instance
    """
    driver.execute_script(
        """
        // Remove badges
        document.querySelectorAll('.a11y-violation-badge').forEach(el => el.remove());
        
        // Remove outlines (best-effort)
        document.querySelectorAll('[style*="outline"]').forEach(el => {
            el.style.outline = '';
            el.style.outlineOffset = '';
        });
        """
    )


# ============================================================================
# Public API
# ============================================================================

def capture_violation_screenshot(
    driver: WebDriver,
    violation: AxeViolation,
    violation_index: int,
    screenshot_dir: Path,
    *,
    scroll_into_view: bool = True,
    max_nodes_per_violation: int | None = 10,
    cleanup_after: bool = True,
) -> ViolationScreenshot | None:
    """
    Capture a screenshot with only this violation highlighted.
    
    Marks all affected elements for this violation with colored outlines
    and badges, then captures a screenshot and cleans up the marks.
    
    Args:
        driver: Selenium WebDriver instance
        violation: Single violation from axe results
        violation_index: Index of this violation (for file naming)
        screenshot_dir: Directory to save screenshot file
        scroll_into_view: Whether to scroll each element into view (default: True)
        max_nodes_per_violation: Limit elements marked per violation (default: 10)
        cleanup_after: Whether to remove marks after capture (default: True)
    
    Returns:
        ViolationScreenshot with file path and stats, or None if no elements marked
    """
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    violation_id = violation.get("id", "unknown")
    color = _severity_color(violation.get("impact"))
    
    # Mark all selectors for this violation
    marked_count = 0
    badge_offset_y = 0
    
    for selector in _iter_violation_selectors(
        violation, max_nodes=max_nodes_per_violation
    ):
        if scroll_into_view:
            driver.execute_script(
                """
                const el = document.querySelector(arguments[0]);
                if (el) el.scrollIntoView({block:'center', inline:'center'});
                """,
                selector,
            )
        
        label = f"{violation_index}: {violation_id}"
        if _mark_selector_on_page(driver, selector, label, color, badge_offset_y):
            marked_count += 1
            badge_offset_y = (badge_offset_y + 14) % 56
    
    # Skip if no elements were marked
    if marked_count == 0:
        return None
    
    # Sync repaint before screenshot
    driver.execute_script(
        "return new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))"
    )
    
    # Capture screenshot
    screenshot_path = screenshot_dir / f"{violation_index}_{violation_id}.png"
    driver.save_screenshot(str(screenshot_path))
    
    # Cleanup badges and outlines
    if cleanup_after:
        _cleanup_violation_marks(driver)
    
    return ViolationScreenshot(
        violation_id=violation_id,
        violation_index=violation_index,
        screenshot_path=screenshot_path,
        marked_count=marked_count,
    )


def capture_all_violations_individually(
    driver: WebDriver,
    results: AxeResults,
    screenshot_dir: Path | str,
    *,
    scroll_into_view: bool = True,
    max_nodes_per_violation: int | None = 10,
) -> dict[str, str]:
    """
    Capture individual screenshots for each violation in results.
    
    Iterates through all violations, captures a screenshot for each one
    with only that violation highlighted, and updates violation dicts
    with screenshot_path in-place.
    
    Args:
        driver: Selenium WebDriver instance
        results: Complete AxeResults from axe.run()
        screenshot_dir: Directory to save screenshots
        scroll_into_view: Whether to scroll elements into view (default: True)
        max_nodes_per_violation: Limit elements per violation (default: 10)
    
    Returns:
        Dict mapping violation_id -> screenshot file path
    """
    screenshot_dir = Path(screenshot_dir)
    screenshot_paths: dict[str, str] = {}
    
    violations: list[AxeViolation] = results.get("violations", [])
    
    for v_index, violation in enumerate(violations, start=1):
        screenshot_result = capture_violation_screenshot(
            driver,
            violation,
            v_index,
            screenshot_dir,
            scroll_into_view=scroll_into_view,
            max_nodes_per_violation=max_nodes_per_violation,
        )
        
        if screenshot_result:
            violation_id = violation.get("id", "unknown")
            screenshot_path_str = str(screenshot_result.screenshot_path)
            screenshot_paths[violation_id] = screenshot_path_str
            # Update violation dict in-place with screenshot path
            violation["screenshot_path"] = screenshot_path_str
    
    return screenshot_paths