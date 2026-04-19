# 🕷️ omni-scraper-core

> A modular, stealth-ready Python web scraping boilerplate  
> powered by **Playwright** + **BeautifulSoup4**.

---

## 📁 Project Structure

```
omni-scraper-core/
├── main.py                   ← CLI entry-point / demo runner
├── requirements.txt
├── config/
│   └── config.yaml           ← All settings (headless, UA, retry, etc.)
├── scrapers/
│   └── universal_scraper.py  ← UniversalScraper class
├── utils/
│   ├── config_loader.py      ← YAML loader
│   ├── stealth.py            ← User-Agent rotation & headers
│   ├── logger.py             ← Loguru logger
│   └── exporter.py           ← JSON / CSV output
└── output/                   ← Auto-created at runtime
```

---

## ⚡ Quick Start

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install Playwright browsers (Chromium only)
playwright install chromium

# 4. Run the demo
python main.py
```

Results are saved to `output/results.json`.

---

## 🔧 Programmatic Usage

```python
import asyncio
from scrapers.universal_scraper import UniversalScraper

async def main():
    async with UniversalScraper() as scraper:
        # Single page
        result = await scraper.scrape(
            url="https://quotes.toscrape.com",
            target_selectors={
                "quotes":  ".quote .text",
                "authors": ".quote .author",
            }
        )
        print(result["data"])

        # Multiple pages concurrently
        results = await scraper.scrape_many(
            urls=["https://example.com/page/1", "https://example.com/page/2"],
            target_selectors={"titles": "h1", "paragraphs": "p"},
            concurrency=2,
        )

asyncio.run(main())
```

---

## ⚙️ Configuration (`config/config.yaml`)

| Key | Default | Description |
|---|---|---|
| `browser.headless` | `true` | Run browser in headless mode |
| `browser.timeout` | `30000` | Page-load timeout in ms |
| `stealth.enabled` | `true` | Enable stealth headers |
| `stealth.rotate_user_agent` | `true` | Rotate UA on each session |
| `retry.max_attempts` | `3` | Auto-retry on failure |
| `retry.wait_seconds` | `2` | Base wait between retries |
| `output.directory` | `output` | Where to save results |

---

## 🛡️ Stealth Mode

When `stealth.enabled: true`, every browser context receives:
- A **randomly-rotated User-Agent** from the configured pool
- Extra HTTP headers (`Accept-Language`, `DNT`, etc.)

Add more User-Agent strings to the `stealth.user_agents` list in `config.yaml`.

---

## 🤖 Antigravity Extension Points

After handing off to **Antigravity**, the agent can:
1. Install and activate the venv via terminal
2. Add a **Vision Skill** (Gemini) to handle selector-miss fallback
3. Run browser tests against the demo targets
4. Record a video artifact of the session
5. Output `test_results.json`

---

## 📄 License
MIT – use freely, scrape responsibly.
