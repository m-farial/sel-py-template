"""
Per-violation screenshot strategy for a11y violations.

Instead of one screenshot with all violations highlighted,
capture individual screenshots for each violation.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Any
from selenium.webdriver.remote.webdriver import WebDriver

from typing_extensions import TypedDict


# ============================================================================
# Types (updated)
# ============================================================================

class AxeNode(TypedDict, total=False):
    target: list[str]
    html: str
    impact: str | None
    failureSummary: str


class AxeViolation(TypedDict, total=False):
    id: str
    description: str
    impact: str | None
    help: str
    helpUrl: str
    nodes: list[AxeNode]
    page_url: str
    tags: list[str]
    screenshot_path: str | None  # NEW: path to per-violation screenshot


class AxeResults(TypedDict):
    violations: list[AxeViolation]


# ============================================================================
# Screenshot utilities
# ============================================================================

@dataclass
class ViolationScreenshot:
    """Result of capturing a violation screenshot."""
    violation_id: str
    violation_index: int
    screenshot_path: Path
    marked_count: int


def _iter_violation_selectors(
    violation: AxeViolation, *, max_nodes: int | None = None
) -> Iterable[str]:
    """
    Yield selectors for a single violation.
    
    Filters out non-list targets and global selectors.
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
    """Skip global/root selectors that don't help visually."""
    s = selector.strip().lower()
    return s in ("html", "body", "*")


def _severity_color(impact: str | None) -> str:
    """Map severity to a stable color."""
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
    Mark a single selector on the page.
    
    Returns True if element was found and marked.
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
    
    Args:
        driver: Selenium WebDriver instance.
        violation: Single AxeViolation dict.
        violation_index: Index of violation (for naming/labeling).
        screenshot_dir: Directory to save screenshot.
        scroll_into_view: Scroll targets into view before capture.
        max_nodes_per_violation: Limit targets per violation.
        cleanup_after: Remove badges/outlines after screenshot.
    
    Returns:
        ViolationScreenshot with path and stats, or None if capture failed.
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
    
    if marked_count == 0:
        # No targets found, skip screenshot
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


def _cleanup_violation_marks(driver: WebDriver) -> None:
    """Remove all violation badges and outlines from the page."""
    driver.execute_script(
        """
        // Remove badges
        document.querySelectorAll('.a11y-violation-badge').forEach(el => el.remove());
        
        // Remove outlines (this is best-effort, may not catch all)
        document.querySelectorAll('[style*="outline"]').forEach(el => {
            el.style.outline = '';
            el.style.outlineOffset = '';
        });
        """
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
    Capture individual screenshots for each violation.
    
    Returns dict mapping violation_id -> screenshot_path (as string).
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
            screenshot_paths[violation_id] = str(screenshot_result.screenshot_path)
            # Update the violation dict in-place
            violation["screenshot_path"] = str(screenshot_result.screenshot_path)
    
    return screenshot_paths