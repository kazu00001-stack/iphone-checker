from __future__ import annotations

import logging
import re

from bs4 import BeautifulSoup
from playwright.async_api import BrowserContext

from core.models import BuybackQuote, ModelKey
from core.normalize import normalize_capacity, normalize_model_name

from .base import fetch_html

log = logging.getLogger(__name__)

SITE = "iosys"

_UNUSED_PRICE_RE = re.compile(r"未使用品買取価格\s*([0-9,]+)\s*円")
_CARRIER_LABEL_RE = re.compile(r"(docomo|au|SoftBank|Rakuten|国内|海外|Ymobile|UQmobile)版SIMフリー")


async def scrape_iosys(context: BrowserContext, url: str) -> list[BuybackQuote]:
    try:
        html = await fetch_html(context, url)
    except Exception as e:
        log.warning("iosys fetch failed: %s", e)
        return []

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    rows = _extract_rows(text)
    log.info("iosys: extracted %d quotes", len(rows))

    return [
        BuybackQuote(
            key=ModelKey(name=model, capacity=capacity),
            site=SITE,
            price_jpy=price,
            source_url=url,
        )
        for model, capacity, price in rows
    ]


def _extract_rows(text: str) -> list[tuple[str, str, int]]:
    """Walk the price-table text and yield (model, capacity, price) tuples.

    iosys structure repeats this pattern many times:
        docomo版SIMフリー
        iPhone17 Pro
        256GB
        未使用品買取価格
        157,000円
        ...
    We only keep '国内版SIMフリー' rows so the result matches Apple's SIM-free retail.
    """
    rows: list[tuple[str, str, int]] = []
    seen: set[tuple[str, str]] = set()

    carrier_positions = [(m.start(), m.group(1)) for m in _CARRIER_LABEL_RE.finditer(text)]
    if not carrier_positions:
        return rows

    for idx, (pos, carrier) in enumerate(carrier_positions):
        if carrier != "国内":
            continue
        end = carrier_positions[idx + 1][0] if idx + 1 < len(carrier_positions) else len(text)
        block = text[pos:end]
        model = normalize_model_name(block)
        capacity = normalize_capacity(block)
        if not (model and capacity):
            continue
        m = _UNUSED_PRICE_RE.search(block)
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
        rows.append((model, capacity, price))

    return rows
