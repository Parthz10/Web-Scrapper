"""
utils/config_loader.py
Loads config/config.yaml and exposes a typed Config dataclass.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

# ── Locate the config file relative to *this* file ───────────────────────────
_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "config.yaml"


def load_config(path: str | Path = _CONFIG_PATH) -> dict[str, Any]:
    """Return the raw YAML config as a plain dict."""
    with open(path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    return cfg


# Convenience singleton loaded at import time
CONFIG: dict[str, Any] = load_config()
