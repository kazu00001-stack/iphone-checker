from __future__ import annotations

from typing import Iterable

from .models import AppleModel, BuybackQuote, ComparisonRow, ModelKey


def build_rows(
    apple_models: Iterable[AppleModel],
    quotes: Iterable[BuybackQuote],
    mile_rate_percent: float,
) -> list[ComparisonRow]:
    apple_map: dict[ModelKey, AppleModel] = {m.key: m for m in apple_models}
    quote_map: dict[ModelKey, dict[str, int]] = {}
    for q in quotes:
        quote_map.setdefault(q.key, {})
        existing = quote_map[q.key].get(q.site)
        if existing is None or q.price_jpy > existing:
            quote_map[q.key][q.site] = q.price_jpy

    rows: list[ComparisonRow] = []
    for key, apple in apple_map.items():
        site_quotes = quote_map.get(key, {})
        best_site = None
        best_price = None
        if site_quotes:
            best_site, best_price = max(site_quotes.items(), key=lambda kv: kv[1])
        profit = best_price - apple.price_jpy if best_price is not None else None
        miles = round(apple.price_jpy * mile_rate_percent / 100.0)
        rows.append(
            ComparisonRow(
                key=key,
                apple_price=apple.price_jpy,
                apple_is_fallback=apple.is_fallback,
                quotes=site_quotes,
                best_site=best_site,
                best_price=best_price,
                profit=profit,
                miles=miles,
            )
        )

    rows.sort(key=lambda r: (r.key.name, _capacity_sort_key(r.key.capacity)))
    return rows


def _capacity_sort_key(capacity: str) -> int:
    digits = "".join(ch for ch in capacity if ch.isdigit())
    if not digits:
        return 0
    n = int(digits)
    if capacity.upper().endswith("TB"):
        n *= 1024
    return n
