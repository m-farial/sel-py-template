# src/pytest_a11y/reporting/json_report.py
from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
from typing import Any

from src.utils.logger_util import LoggerFactory


def write_a11y_json_report(
    *,
    axe_results: dict[str, Any] | None,
    page_url: str,
    output_path: Path | str,
) -> Path:
    """
    Write a combined accessibility report in JSON format.

    Returns:
        The Path to the written report file.
    """
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    payload: dict[str, Any] = {
        "url": page_url,
        "axe": axe_results,
    }

    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def write_json_report(results, test_name):
    a11y_dir = LoggerFactory.get_a11y_dir() or os.getcwd()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{test_name}_{timestamp}.json"
    path = a11y_dir / filename

    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return str(path)
