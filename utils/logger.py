"""
utils/logger.py
Centralised Loguru logger.  Import `log` from anywhere in the project.
"""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from utils.config_loader import CONFIG

_log_cfg = CONFIG.get("logging", {})
_level: str = _log_cfg.get("level", "INFO")
_log_file: str = _log_cfg.get("log_file", "output/scraper.log")

# Remove default handler then add custom ones
logger.remove()
logger.add(sys.stderr, level=_level, colorize=True,
           format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")

Path(_log_file).parent.mkdir(parents=True, exist_ok=True)
logger.add(_log_file, level=_level, rotation="5 MB", retention="7 days",
           format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}")

log = logger
