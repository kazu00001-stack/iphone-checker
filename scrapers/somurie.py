from __future__ import annotations

import logging
import re
from urllib.parse import urljoin, urlparse, parse_qs

from bs4 import BeautifulSoup
from playwright.async_api import BrowserContext

from core.models import BuybackQuote, ModelKey
from core.normalize import normalize_capacity, normalize_model_name

from .base import fetch_html

log = logging.getLogger(__name__)

SITE = "somurie"
BASE_URL = "https://somurie-kaitori.com"

_TITLE_RE = re.compile(r"^iPhone .+\d+(?:GB|TB)\s+\S")
_PRICE_RE = re.compile(r"^(\d{1,3}(?:,\d{3})*)$")
_SUBCATEGORY_RE = re.compile(r"subcategory=(\d+)")


async def scrape_somurie(context: BrowserContext, candidate_urls: list[str]) -> list[BuybackQuote]:
    seed_urls = candidate_urls or [f"{BASE_URL}/products?category=1"]
    subcategory_urls = await _discover_subcategory_urls(context, seed_urls)
    if not subcategory_urls:
        log.warning("somurie: no subcategory URLs discovered")
        return []

    best: dict[tuple[str, str], tuple[int, str]] = {}
    for url in subcategory_urls:
        try:
            html = await fetch_html(context, url, timeout_ms=45000)
        except Exception as e:
            log.warning("somurie fetch failed for %s: %s", url, e)
            continue
        for model, capacity, price in _extract_rows(html):
            key = (model, capacity)
            if key not in best or price > best[key][0]:
                best[key] = (price, url)

    rows = [
        BuybackQuote(
            key=ModelKey(name=model, capacity=capacity),
            site=SITE,
            price_jpy=price,
            source_url=source_url,
        )
        for (model, capacity), (price, source_url) in best.items()
    ]
    log.info("somurie: extracted %d quotes from %d subcategories", len(rows), len(subcategory_urls))
    return rows


async def _discover_subcategory_urls(context: BrowserContext, seed_urls: list[str]) -> list[str]:
    discovered: dict[int, str] = {}
    for seed in seed_urls:
        try:
            html = await fetch_html(context, seed, timeout_ms=45000)
        except Exception as e:
            log.warning("somurie discovery fetch failed for %s: %s", seed, e)
            continue
        for url in _parse_subcategory_links(html, seed):
            sub_id = _subcategory_id(url)
            if sub_id is not None:
                discovered[sub_id] = url
        if discovered:
            break

    if not discovered:
        return []

    return [discovered[k] for k in sorted(discovered)]


def _parse_subcategory_links(html: str, page_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "subcategory=" not in href or "category=1" not in href:
            continue
        text = a.get_text(strip=True)
        if not text.startswith("iPhone"):
            continue
        full = urljoin(page_url, href)
        if full in seen:
            continue
        seen.add(full)
        urls.append(full)
    return urls


def _subcategory_id(url: str) -> int | None:
    query = parse_qs(urlparse(url).query)
    raw = query.get("subcategory", [None])[0]
    if raw is None:
        m = _SUBCATEGORY_RE.search(url)
        if not m:
            return None
        raw = m.group(1)
    try:
        return int(raw)
    except ValueError:
        return None


def _extract_rows(html: str) -> list[tuple[str, str, int]]:
    soup = BeautifulSoup(html, "html.parser")
    lines = [_preprocess(l) for l in soup.get_text("\n", strip=True).split("\n") if l.strip()]

    best: dict[tuple[str, str], int] = {}
    for i, line in enumerate(lines):
        if not _TITLE_RE.match(line):
            continue
        model = normalize_model_name(line)
        capacity = normalize_capacity(line)
        if not (model and capacity):
            continue
        price = _price_after_title(lines, i)
        if price is None:
            continue
        key = (model, capacity)
        best[key] = max(best.get(key, 0), price)

    return [(model, capacity, price) for (model, capacity), price in best.items()]


def _preprocess(text: str) -> str:
    return text.replace("iPhone 17 e", "iPhone 17e")


def _price_after_title(lines: list[str], title_index: int) -> int | None:
    for j in range(title_index + 1, min(title_index + 8, len(lines))):
        m = _PRICE_RE.match(lines[j])
        if not m:
            continue
        try:
            return int(m.group(1).replace(",", ""))
        except ValueError:
            return None
    return None
