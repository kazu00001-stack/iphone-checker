from __future__ import annotations

import logging
import re
from typing import Iterable

from playwright.async_api import BrowserContext

from core.models import AppleModel, ModelKey
from core.normalize import normalize_capacity, normalize_model_name

from .base import fetch_html

log = logging.getLogger(__name__)


_VARIANT_RE = re.compile(
    r'"sku"\s*:\s*"[^"]+"'
    r'\s*,\s*"partNumber"\s*:\s*"[^"]+"'
    r'\s*,\s*"price"\s*:\s*\{\s*"fullPrice"\s*:\s*([0-9.]+)\s*\}'
    r'\s*,\s*"category"\s*:\s*"iphone"'
    r'\s*,\s*"name"\s*:\s*"([^"]+)"'
)


async def scrape_apple(
    context: BrowserContext,
    apple_models_config: list[dict],
    base_url: str,
) -> list[AppleModel]:
    page_cache: dict[str, dict[tuple[str, str], int]] = {}
    page_urls: dict[str, str] = {}
    results: list[AppleModel] = []

    for model_cfg in apple_models_config:
        name = model_cfg["name"]
        slug = model_cfg["slug"]
        capacities = model_cfg["capacities"]
        fallbacks = model_cfg.get("fallback_prices", {})
        url = f"{base_url}/{slug}"

        if slug not in page_cache:
            try:
                html = await fetch_html(context, url, timeout_ms=45000)
                page_cache[slug] = _extract_variants(html)
                page_urls[slug] = url
            except Exception as e:
                log.warning("Apple fetch failed for %s: %s", url, e)
                page_cache[slug] = {}
                page_urls[slug] = url

        prices = page_cache[slug]

        for capacity in capacities:
            key = ModelKey(name=name, capacity=capacity)
            price = prices.get((name, capacity))
            if price is not None:
                results.append(
                    AppleModel(key=key, price_jpy=price, url=url, is_fallback=False)
                )
            elif capacity in fallbacks:
                results.append(
                    AppleModel(
                        key=key,
                        price_jpy=int(fallbacks[capacity]),
                        url=url,
                        is_fallback=True,
                    )
                )
            else:
                log.warning("No price for %s %s (page=%s)", name, capacity, slug)

    return results


def _extract_variants(html: str) -> dict[tuple[str, str], int]:
    """Parse Apple's embedded JSON variant list. The page contains entries like:

        {"sku":"...","partNumber":"...","price":{"fullPrice":194800.00},
         "category":"iphone","name":"iPhone 17 Pro Max 256GB Cosmic Orange"}

    We map (model, capacity) -> minimum fullPrice (colors are all the same price).
    """
    out: dict[tuple[str, str], int] = {}
    for m in _VARIANT_RE.finditer(html):
        try:
            price = int(float(m.group(1)))
        except ValueError:
            continue
        product_name = m.group(2)
        model = normalize_model_name(product_name)
        capacity = normalize_capacity(product_name)
        if not (model and capacity):
            continue
        key = (model, capacity)
        existing = out.get(key)
        if existing is None or price < existing:
            out[key] = price
    return out
