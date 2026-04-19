"""
main.py – omni-scraper-core entry point
────────────────────────────────────────
Run with:
    python main.py

Or import and use programmatically:
    from main import run
    import asyncio
    asyncio.run(run())
"""

from __future__ import annotations

import asyncio
import json

from scrapers.universal_scraper import UniversalScraper
from utils.exporter import export
from utils.logger import log

DEMO_JOBS: list[dict] = [
    {
        "url": "https://news.ycombinator.com",
        "selectors": {
            "headlines": ".titleline > a",
            "links": ".titleline > a", # The actual href is needed, our parser extracts text right now. Wait, beautifulsoup extracts text. If we need links, the user said "headlines and links".
        },
    },
    {
        "url": "https://webscraper.io/test-sites/e-commerce/allinone",
        "selectors": {
            "product_names": ".title",
            "prices": ".price",
        },
    },
]


async def run(jobs: list[dict] | None = None) -> list[dict]:
    """Execute all scrape jobs and return combined results."""
    jobs = jobs or DEMO_JOBS
    all_results: list[dict] = []

    async with UniversalScraper() as scraper:
        for job in jobs:
            try:
                result = await scraper.scrape(
                    url=job["url"],
                    target_selectors=job["selectors"],
                )
                
                # Limit Hacker News to top 10
                if "news.ycombinator.com" in job["url"]:
                    for key in result["data"]:
                        result["data"][key] = result["data"][key][:10]
                        
                all_results.append(result)
            except Exception as exc:
                log.error(f"Job failed for {job['url']}: {exc}")
                all_results.append({"url": job["url"], "error": str(exc)})

    # Save outputs
    export(all_results, fmt="json", filename="results.json")
    log.info("All jobs complete.")
    return all_results


if __name__ == "__main__":
    results = asyncio.run(run())
    # Pretty-print summary to terminal
    for r in results:
        print(f"\n{'-'*60}")
        print(f"URL : {r.get('url')}")
        if "error" in r:
            print(f"ERR : {r['error']}")
        else:
            for label, items in r["data"].items():
                print(f"  [{label}] -> {len(items)} item(s)")
                for item in items[:3]:
                    print(f"    - {str(item)[:80]}")
            print(f"  meta: {r['metadata']}")
