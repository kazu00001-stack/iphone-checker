from __future__ import annotations

import logging
import re

from bs4 import BeautifulSoup
from playwright.async_api import BrowserContext

from core.models import BuybackQuote, ModelKey
from core.normalize import normalize_capacity, normalize_model_name

from .base import fetch_html

log = logging.getLogger(__name__)

SITE = "mobile_mix"


async def scrape_mobile_mix(context: BrowserContext, candidate_urls: list[str]) -> list[BuybackQuote]:
    for url in candidate_urls:
        try:
            html = await fetch_html(context, url)
        except Exception as e:
            log.warning("mobile_mix fetch failed for %s: %s", url, e)
            continue
        rows = _parse(html, url)
        if rows:
            return rows
    log.warning("mobile_mix: no parsable price table found in candidate URLs")
    return []


_PRICE_RE = re.compile(r"([0-9][0-9,]{2,})\s*円")


def _parse(html: str, url: str) -> list[BuybackQuote]:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    if "iPhone" not in text:
        return []

    results: list[BuybackQuote] = []
    seen: set[tuple[str, str]] = set()

    chunks = re.split(r"(?=iPhone\s*[A-Za-z0-9]+)", text)
    for chunk in chunks:
        if "iPhone" not in chunk:
            continue
        if not _looks_like_simfree_or_neutral(chunk):
            continue
        model = normalize_model_name(chunk)
        capacity = normalize_capacity(chunk)
        if not model or not capacity:
            continue
        price = _pick_unused_price(chunk)
        if price is None:
            continue
        if (model, capacity) in seen:
            continue
        seen.add((model, capacity))
        results.append(
            BuybackQuote(
                key=ModelKey(name=model, capacity=capacity),
                site=SITE,
                price_jpy=price,
                source_url=url,
            )
        )
    return results


def _looks_like_simfree_or_neutral(chunk: str) -> bool:
    if "docomo" in chunk or "ドコモ" in chunk or "au" in chunk.lower() or "SoftBank" in chunk or "ソフトバンク" in chunk:
        return "SIMフリー" in chunk or "SIMフリ" in chunk
    return True


def _pick_unused_price(chunk: str) -> int | None:
    idx = chunk.find("未使用")
    if idx >= 0:
        window = chunk[idx : idx + 80]
        m = _PRICE_RE.search(window)
        if m:
            try:
                return int(m.group(1).replace(",", ""))
            except ValueError:
                return None
    prices = [int(p.group(1).replace(",", "")) for p in _PRICE_RE.finditer(chunk)]
    if not prices:
        return None
    return max(prices)
