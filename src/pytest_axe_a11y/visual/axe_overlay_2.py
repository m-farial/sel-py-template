# from __future__ import annotations

# from dataclasses import dataclass
# from typing import Any

# from selenium.webdriver.remote.webdriver import WebDriver

# from pytest_axe_a11y.types import AxeResults

# _MARK_JS = """
# const selector = arguments[0];
# const badgeText = arguments[1];

# const el = document.querySelector(selector);
# if (!el) {
#   return {ok: false, selector, reason: "not_found"};
# }

# // Outline inline (reliable)
# el.style.outline = "4px solid #b00020";
# el.style.outlineOffset = "2px";

# // Add a badge near the element (attach to body; works for <input>)
# const rect = el.getBoundingClientRect();
# const badge = document.createElement("div");
# badge.textContent = badgeText;
# badge.setAttribute("data-pytest-a11y", "badge");
# badge.style.position = "fixed";
# badge.style.left = `${Math.max(0, rect.left)}px`;
# badge.style.top = `${Math.max(0, rect.top - 20)}px`;
# badge.style.zIndex = "2147483647";
# badge.style.background = "#b00020";
# badge.style.color = "#fff";
# badge.style.fontSize = "12px";
# badge.style.padding = "2px 6px";
# badge.style.borderRadius = "4px";
# badge.style.fontFamily = "Arial, sans-serif";
# badge.style.pointerEvents = "none";
# document.body.appendChild(badge);

# return {ok: true, selector, tag: el.tagName, id: el.id};
# """

# _AXE_OVERLAY_BOOTSTRAP_JS: str = r"""
# (() => {
#   if (document.getElementById("__pytest_a11y_overlay_style__")) return;

#   const style = document.createElement("style");
#   style.id = "__pytest_a11y_overlay_style__";
#   style.textContent = `
#     .__a11y_outline__ {
#       outline: 3px solid #b00020 !important;
#       outline-offset: 2px !important;
#     }
#     .__a11y_badge__ {
#       position: fixed !important;
#       background: #b00020 !important;
#       color: #fff !important;
#       font-size: 12px !important;
#       padding: 2px 6px !important;
#       z-index: 2147483647 !important;
#       border-radius: 4px !important;
#       font-family: Arial, sans-serif !important;
#       line-height: 1.2 !important;
#       white-space: nowrap !important;
#       box-shadow: 0 1px 3px rgba(0,0,0,.25) !important;
#       pointer-events: none !important;
#     }
#   `;
#   document.head.appendChild(style);
# })();
# """

# # NOTE: Creates a floating badge positioned near the element (works for <input/>)
# _AXE_OVERLAY_MARK_ELEMENT_JS: str = r"""
# ((selector, badgeText) => {
#   const el = document.querySelector(selector);
#   if (!el) return { ok: false, reason: "not_found" };

#   // Outline the element itself
#   el.classList.add("__a11y_outline__");

#   // Compute position (fixed) relative to viewport
#   const rect = el.getBoundingClientRect();

#   // Create badge and attach to body (works even for void elements like <input>)
#   const badge = document.createElement("div");
#   badge.className = "__a11y_badge__";
#   badge.textContent = badgeText;

#   // Position badge near top-left of the element; clamp to viewport
#   const left = Math.max(0, Math.min(window.innerWidth - 10, rect.left));
#   const top  = Math.max(0, Math.min(window.innerHeight - 10, rect.top));

#   badge.style.left = `${left}px`;
#   badge.style.top  = `${Math.max(0, top - 18)}px`;

#   document.body.appendChild(badge);

#   return { ok: true, rect: { left: rect.left, top: rect.top, width: rect.width, height: rect.height } };
# })();
# """

# _AXE_OVERLAY_CLEAR_JS: str = r"""
# (() => {
#   document.querySelectorAll(".__a11y_badge__").forEach(b => b.remove());
#   document.querySelectorAll(".__a11y_outline__").forEach(el => el.classList.remove("__a11y_outline__"));
#   const style = document.getElementById("__pytest_a11y_overlay_style__");
#   if (style) style.remove();
# })();
# """


# @dataclass(frozen=True)
# class OverlayStats:
#     """Summary stats for overlay application."""

#     attempted: int
#     marked: int


# def install_overlay_styles(driver: WebDriver) -> None:
#     """Inject overlay CSS into the current page (idempotent per page load)."""
#     driver.execute_script(_AXE_OVERLAY_BOOTSTRAP_JS)


# def clear_overlay(driver: WebDriver) -> None:
#     """Remove overlays + styles from the current page."""
#     driver.execute_script(_AXE_OVERLAY_CLEAR_JS)


# def highlight_axe_violations(
#     driver: WebDriver,
#     results: AxeResults,
#     *,
#     max_nodes_per_violation: int = 10,
#     scroll_into_view: bool = True,
# ) -> OverlayStats:
#     """
#     Highlight axe violations on the page by outlining elements and adding floating badges.

#     Args:
#         driver: Selenium WebDriver instance.
#         results: axe results dict (must contain "violations").
#         max_nodes_per_violation: Limit per violation to avoid noisy screenshots.
#         scroll_into_view: If True, scroll each target element into view before marking.

#     Returns:
#         OverlayStats with attempted vs marked targets.
#     """
#     breakpoint()
#     install_overlay_styles(driver)

#     # violations: list[dict[str, Any]] = results.get("violations", [])
#     attempted = 0
#     marked = 0

#     # for v_index, violation in enumerate(violations, start=1):
#     #   rule_id = str(violation.get("id", "unknown"))
#     #   nodes: list[dict[str, Any]] = violation.get("nodes", [])

#     #   for node in nodes[:max_nodes_per_violation]:
#     #     targets: Sequence[str] = node.get("target", [])
#     #     for selector in targets:
#     #       attempted += 1
#     violations: list[dict[str, Any]] = results.get("violations", [])
#     for idx, violation in enumerate(violations, start=1):
#         rule_id = str(violation.get("id", "unknown"))
#         nodes: list[dict[str, Any]] = violation.get("nodes", [])

#         for node in nodes:
#             targets = node.get("target")
#             if not isinstance(targets, list):
#                 continue

#             for selector in targets:
#                 attempted += 1
#                 if not isinstance(selector, str):
#                     continue

#                 sel = selector.strip()
#                 if sel.lower() in ("html", "body", "*"):
#                     continue

#             if scroll_into_view:
#                 driver.execute_script(
#                     """
#             const el = document.querySelector(arguments[0]);
#             if (el) el.scrollIntoView({block: 'center', inline: 'center'});
#             """,
#                     selector,
#                 )

#             badge_text = f"{idx}: {rule_id}"
#             # TEMP debug
#             res = driver.execute_script(_MARK_JS, selector, badge_text)
#             print("OVERLAY:", selector, res)
#             if isinstance(res, dict) and res.get("ok"):
#                 marked += 1

#     return OverlayStats(attempted=attempted, marked=marked)
