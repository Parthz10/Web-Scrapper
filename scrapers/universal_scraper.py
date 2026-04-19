"""
scrapers/universal_scraper.py
──────────────────────────────
The heart of omni-scraper-core.

Usage
-----
    from scrapers.universal_scraper import UniversalScraper

    async with UniversalScraper() as scraper:
        results = await scraper.scrape(
            url="https://quotes.toscrape.com",
            target_selectors={
                "quotes": ".quote .text",
                "authors": ".quote .author",
            }
        )
"""

from __future__ import annotations

import asyncio
from typing import Any

from bs4 import BeautifulSoup
from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)
from tenacity import retry, stop_after_attempt, wait_exponential

from utils.config_loader import CONFIG
from utils.logger import log
from utils.stealth import stealth

# ── Config shortcuts ───────────────────────────────────────────────────────────
_BROWSER_CFG: dict[str, Any] = CONFIG.get("browser", {})
_RETRY_CFG: dict[str, Any] = CONFIG.get("retry", {})
_MAX_ATTEMPTS: int = _RETRY_CFG.get("max_attempts", 3)
_WAIT_SECONDS: int = _RETRY_CFG.get("wait_seconds", 2)


class UniversalScraper:
    """
    A Playwright + BeautifulSoup4 scraper with built-in stealth mode,
    automatic retries, and a clean async-context-manager interface.

    Parameters
    ----------
    headless : bool
        Override the config headless setting (default: from config.yaml).
    """

    def __init__(self, headless: bool | None = None) -> None:
        self._headless: bool = (
            headless
            if headless is not None
            else _BROWSER_CFG.get("headless", True)
        )
        self._timeout: int = _BROWSER_CFG.get("timeout", 30_000)
        self._viewport: dict[str, int] = _BROWSER_CFG.get(
            "viewport", {"width": 1280, "height": 800}
        )
        self._slow_mo: int = _BROWSER_CFG.get("slow_mo", 0)

        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    # ── Async context manager ──────────────────────────────────────────────────

    async def __aenter__(self) -> "UniversalScraper":
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self._headless,
            slow_mo=self._slow_mo,
        )
        log.info(f"Browser launched (headless={self._headless})")
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        log.info("Browser closed.")

    # ── Internal helpers ───────────────────────────────────────────────────────

    async def _new_context(self) -> BrowserContext:
        """Create a fresh browser context with stealth headers applied."""
        assert self._browser, "Browser not started – use `async with UniversalScraper()`"
        headers = stealth.build_headers()
        context = await self._browser.new_context(
            viewport=self._viewport,
            extra_http_headers=headers,
            java_script_enabled=True,
        )
        return context

    async def _auto_load_content(self, page: Page) -> None:
        """Automatically scroll or click 'Load More' until data is fully loaded."""
        last_height = await page.evaluate("document.body.scrollHeight")
        no_change_count = 0
        total_iterations = 0
        
        while no_change_count < 3 and total_iterations < 5:
            total_iterations += 1
            # Scroll down
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            
            # Try to find and click "Load More" buttons
            clicked = False
            try:
                # Common selectors for load more
                buttons = await page.locator("button, a").all()
                for btn in buttons:
                    if await btn.is_visible():
                        text = (await btn.text_content() or "").strip().lower()
                        if text in ["load more", "show more", "more", "load more products", "load more results"]:
                            await btn.click(timeout=2000)
                            await page.wait_for_timeout(2000)
                            clicked = True
                            break
            except Exception:
                pass
                
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height and not clicked:
                no_change_count += 1
            else:
                no_change_count = 0
                last_height = new_height

    async def _fetch_html(self, page: Page, url: str) -> str:
        """Navigate to *url* and return the fully-rendered HTML."""
        await page.goto(url, wait_until="domcontentloaded", timeout=self._timeout)
        # Allow JS-heavy pages a moment to settle
        await page.wait_for_timeout(800)
        await self._auto_load_content(page)
        return await page.content()

    @staticmethod
    def _parse(html: str, selectors: dict[str, str]) -> dict[str, list[dict]]:
        """
        Parse *html* with BeautifulSoup and extract text for every CSS
        selector in *selectors*.

        Parameters
        ----------
        html      : Full page HTML string.
        selectors : Mapping of { label → CSS selector }.

        Returns
        -------
        dict mapping each label to a list of extracted dictionaries.
        """
        soup = BeautifulSoup(html, "lxml")
        results: dict[str, list[dict]] = {}
        for label, selector in selectors.items():
            elements = soup.select(selector)
            parsed_elements = []
            for el in elements:
                item = {"text": el.get_text(strip=True)}
                if el.name == "a" and el.has_attr("href"):
                    item["href"] = el["href"]
                # Also check parent if element itself is not an 'a' tag but we need link
                elif el.parent and el.parent.name == "a" and el.parent.has_attr("href"):
                    item["href"] = el.parent["href"]
                parsed_elements.append(item)
            results[label] = parsed_elements
            log.debug(f"  [{label}] → {len(elements)} element(s) found")
        return results

    # ── Public API ─────────────────────────────────────────────────────────────

    @retry(
        stop=stop_after_attempt(_MAX_ATTEMPTS),
        wait=wait_exponential(multiplier=_WAIT_SECONDS, min=1, max=30),
        reraise=True,
    )
    async def scrape(
        self,
        url: str,
        target_selectors: dict[str, str],
        *,
        wait_for_selector: str | None = None,
    ) -> dict[str, Any]:
        """
        Navigate to *url*, wait for the page to load, and extract data.

        Parameters
        ----------
        url              : Target page URL.
        target_selectors : {label: css_selector} mapping – e.g.
                           {"titles": "h2.title", "prices": "p.price"}.
        wait_for_selector: Optional CSS selector to wait for before
                           parsing (useful for SPAs).

        Returns
        -------
        {
            "url"     : str,
            "data"    : {label: [text, ...]},
            "metadata": {"user_agent": str, "selector_hits": int}
        }
        """
        log.info(f"Scraping → {url}")
        context = await self._new_context()

        try:
            page: Page = await context.new_page()

            if wait_for_selector:
                await page.goto(url, timeout=self._timeout)
                await page.wait_for_selector(
                    wait_for_selector, timeout=self._timeout
                )
                await self._auto_load_content(page)
                html = await page.content()
            else:
                html = await self._fetch_html(page, url)

            extracted = self._parse(html, target_selectors)

            total_hits = sum(len(v) for v in extracted.values())
            log.success(
                f"Done: {total_hits} total element(s) across "
                f"{len(target_selectors)} selector(s) on {url}"
            )

            ua = (await context.cookies())  # context cookies as proxy for UA; grab from headers instead
            return {
                "url": url,
                "data": extracted,
                "metadata": {
                    "user_agent": stealth.build_headers().get("User-Agent", "unknown"),
                    "selector_hits": total_hits,
                },
            }

        except Exception as exc:
            log.error(f"Error scraping {url}: {exc}")
            raise

        finally:
            await context.close()

    async def scrape_many(
        self,
        urls: list[str],
        target_selectors: dict[str, str],
        *,
        concurrency: int = 3,
    ) -> list[dict[str, Any]]:
        """
        Scrape multiple URLs concurrently.

        Parameters
        ----------
        urls             : List of target URLs.
        target_selectors : Shared selector map applied to every URL.
        concurrency      : Max parallel pages (default 3).
        """
        semaphore = asyncio.Semaphore(concurrency)

        async def _guarded(url: str) -> dict[str, Any]:
            async with semaphore:
                return await self.scrape(url, target_selectors)

        tasks = [_guarded(u) for u in urls]
        return await asyncio.gather(*tasks, return_exceptions=False)
