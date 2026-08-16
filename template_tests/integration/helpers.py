from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_html(tmp_path: Path, name: str, html: str) -> str:
    """
    Write HTML content to a temporary file and return a file:// URI.

    Args:
        tmp_path: Pytest temporary directory fixture.
        name: File name to create.
        html: HTML content to write.

    Returns:
        file:// URI to the created HTML file.
    """
    path = tmp_path / name
    path.write_text(html.strip(), encoding="utf-8")
    return path.as_uri()


def load_json(path: Path) -> dict[str, Any]:
    """
    Load and parse a JSON file.

    Args:
        path: JSON file path.

    Returns:
        Parsed JSON object.
    """
    return json.loads(path.read_text(encoding="utf-8"))


def collect_rule_ids(results: dict[str, Any]) -> set[str]:
    """
    Collect rule ids from axe results.

    Args:
        results: Axe results payload.

    Returns:
        Set of violation ids.
    """
    return {
        rule_id
        for violation in results.get("violations", [])
        if (rule_id := violation.get("id"))
    }


def count_violations(results: dict[str, Any]) -> int:
    """
    Return number of axe violations.

    Args:
        results: Axe results payload.

    Returns:
        Violation count.
    """
    return len(results.get("violations", []))


def assert_axe_result_shape(results: dict[str, Any]) -> None:
    """
    Assert the standard top-level axe result sections exist.

    Args:
        results: Axe results payload.
    """
    expected_keys = {"violations", "passes", "incomplete", "inapplicable"}
    assert expected_keys.issubset(results.keys()), (
        f"Expected axe results to include keys {expected_keys}, got {set(results.keys())}"
    )
