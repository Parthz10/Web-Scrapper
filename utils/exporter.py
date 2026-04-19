"""
utils/exporter.py
Save scraped results to JSON and/or CSV.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from utils.config_loader import CONFIG
from utils.logger import log

_OUTPUT_DIR = Path(CONFIG.get("output", {}).get("directory", "output"))
_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def save_json(data: Any, filename: str | None = None) -> Path:
    filename = filename or f"results_{_timestamp()}.json"
    path = _OUTPUT_DIR / filename
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    log.info(f"JSON saved → {path}")
    return path


def save_csv(rows: list[dict[str, Any]], filename: str | None = None) -> Path:
    if not rows:
        log.warning("save_csv called with empty rows – nothing written.")
        return _OUTPUT_DIR / "empty.csv"

    filename = filename or f"results_{_timestamp()}.csv"
    path = _OUTPUT_DIR / filename
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    log.info(f"CSV saved  → {path}")
    return path


def export(data: Any, fmt: str = "json", filename: str | None = None) -> list[Path]:
    """Export data. fmt can be 'json', 'csv', or 'both'."""
    paths: list[Path] = []
    if fmt in ("json", "both"):
        paths.append(save_json(data, filename and filename.replace(".csv", ".json")))
    if fmt in ("csv", "both"):
        rows = data if isinstance(data, list) else [data]
        paths.append(save_csv(rows, filename and filename.replace(".json", ".csv")))
    return paths
