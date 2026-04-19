"""
utils/stealth.py
Stealth-mode helpers: User-Agent rotation & extra-header injection.
"""

from __future__ import annotations

import random
from typing import Any

from utils.config_loader import CONFIG


class StealthConfig:
    """Encapsulates stealth-mode settings read from config.yaml."""

    def __init__(self) -> None:
        stealth_cfg: dict[str, Any] = CONFIG.get("stealth", {})
        self.enabled: bool = stealth_cfg.get("enabled", True)
        self.rotate: bool = stealth_cfg.get("rotate_user_agent", True)
        self._agents: list[str] = stealth_cfg.get("user_agents", [])
        self.extra_headers: dict[str, str] = stealth_cfg.get("extra_headers", {})

    # ── Public helpers ──────────────────────────────────────────────────────

    def random_user_agent(self) -> str:
        """Return a random User-Agent string from the configured pool."""
        if not self._agents:
            # Reasonable fall-back if config is empty
            return (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        return random.choice(self._agents)

    def build_headers(self) -> dict[str, str]:
        """Return a full headers dict (UA + extras) ready for Playwright."""
        headers: dict[str, str] = dict(self.extra_headers)
        if self.enabled and self.rotate:
            headers["User-Agent"] = self.random_user_agent()
        return headers


# Module-level singleton – import and use directly
stealth = StealthConfig()
