"""Run all scrapers and write the result JSON to docs/data.json.

This is the CI/cron entrypoint for the public web build. It is independent
of the Flask app and can be run from a clean checkout via:

    python scripts/scrape_to_json.py

Exit codes:
    0 — JSON written successfully
    1 — fatal error (no JSON written)

The script never fails on individual site errors; failed sites are simply
omitted from the output, and the resulting page shows a "-" for those cells.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scrapers.apple import scrape_apple  # noqa: E402
from scrapers.base import open_browser  # noqa: E402
from scrapers.ichome import scrape_ichome  # noqa: E402
from scrapers.iosys import scrape_iosys  # noqa: E402
from scrapers.mobile_mix import scrape_mobile_mix  # noqa: E402


CONFIG_PATH = ROOT / "config.yaml"
OUTPUT_PATH = ROOT / "docs" / "data.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s | %(message)s")
log = logging.getLogger("scrape_to_json")


JST = timezone(timedelta(hours=9))


def _unwrap(value, default):
    if isinstance(value, Exception):
        log.warning("scraper raised: %s", value)
        return default
    return value


async def run(cfg: dict) -> dict:
    apple_cfg = cfg["scrapers"]["apple"]
    iosys_cfg = cfg["scrapers"]["iosys"]
    mobile_mix_cfg = cfg["scrapers"]["mobile_mix"]
    ichome_cfg = cfg["scrapers"]["ichome"]

    async with open_browser() as context:
        results = await asyncio.gather(
            scrape_apple(context, cfg["apple_models"], apple_cfg["base_url"]),
            scrape_iosys(context, iosys_cfg["url"]) if iosys_cfg.get("enabled") else asyncio.sleep(0, result=[]),
            scrape_mobile_mix(context, mobile_mix_cfg["candidate_urls"]) if mobile_mix_cfg.get("enabled") else asyncio.sleep(0, result=[]),
            scrape_ichome(context, ichome_cfg["candidate_urls"]) if ichome_cfg.get("enabled") else asyncio.sleep(0, result=[]),
            return_exceptions=True,
        )

    apple_models = _unwrap(results[0], [])
    iosys_quotes = _unwrap(results[1], [])
    mm_quotes = _unwrap(results[2], [])
    ichome_quotes = _unwrap(results[3], [])

    return {
        "fetched_at": datetime.now(JST).isoformat(timespec="seconds"),
        "apple_models": [
            {
                "name": m.key.name,
                "capacity": m.key.capacity,
                "price_jpy": m.price_jpy,
                "url": m.url,
                "is_fallback": m.is_fallback,
            }
            for m in apple_models
        ],
        "quotes": [
            {
                "site": q.site,
                "name": q.key.name,
                "capacity": q.key.capacity,
                "price_jpy": q.price_jpy,
                "source_url": q.source_url,
            }
            for q in iosys_quotes + mm_quotes + ichome_quotes
        ],
    }


def main() -> int:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    try:
        payload = asyncio.run(run(cfg))
    except Exception:
        log.exception("scrape failed fatally")
        return 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    apple_n = len(payload["apple_models"])
    apple_scraped = sum(1 for m in payload["apple_models"] if not m["is_fallback"])
    quote_n = len(payload["quotes"])
    by_site = {}
    for q in payload["quotes"]:
        by_site[q["site"]] = by_site.get(q["site"], 0) + 1

    log.info("wrote %s", OUTPUT_PATH)
    log.info("apple: %d models (%d scraped, %d fallback)", apple_n, apple_scraped, apple_n - apple_scraped)
    log.info("quotes: %d total — %s", quote_n, by_site)
    return 0


if __name__ == "__main__":
    sys.exit(main())
