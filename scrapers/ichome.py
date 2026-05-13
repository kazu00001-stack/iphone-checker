from __future__ import annotations

import logging
import re

from bs4 import BeautifulSoup
from playwright.async_api import BrowserContext

from core.models import BuybackQuote, ModelKey
from core.normalize import normalize_capacity, normalize_model_name

from .base import fetch_html

log = logging.getLogger(__name__)

SITE = "ichome"

_PRICE_RE = re.compile(r"[¥￥]\s*([0-9][0-9,]+)")


async def scrape_ichome(context: BrowserContext, candidate_urls: list[str]) -> list[BuybackQuote]:
    for url in candidate_urls:
        try:
            html = await fetch_html(context, url, timeout_ms=45000)
        except Exception as e:
            log.warning("ichome fetch failed for %s: %s", url, e)
            continue
        rows = _parse(html, url)
        if rows:
            log.info("ichome: extracted %d quotes from %s", len(rows), url)
            return rows
    log.warning("ichome: no parsable price table found in candidate URLs")
    return []


def _parse(html: str, url: str) -> list[BuybackQuote]:
    """Parse 1-chome's price list. Each variant block looks like:

        iPhone 17 Pro Max 256GB
        新品
        JAN:
        未開封
        ¥217,200
        開封済未使用品
        ¥198,000
        カートに入れる

    We use 未開封 (sealed) as the "未使用品" buyback price.
    """
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    if "iPhone" not in text or "未開封" not in text:
        return []

    chunks = re.split(r"(?=iPhone\s+\S)", text)
    rows: list[BuybackQuote] = []
    seen: set[tuple[str, str]] = set()

    for chunk in chunks:
        if "未開封" not in chunk:
            continue
        header = chunk[:200]
        model = normalize_model_name(header)
        capacity = normalize_capacity(header)
        if not (model and capacity):
            continue
        idx = chunk.find("未開封")
        window = chunk[idx : idx + 200]
        m = _PRICE_RE.search(window)
        if not m:
            continue
        try:
            price = int(m.group(1).replace(",", ""))
        except ValueError:
            continue
        key = (model, capacity)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            BuybackQuote(
                key=ModelKey(name=model, capacity=capacity),
                site=SITE,
                price_jpy=price,
                source_url=url,
            )
        )
    return rows
