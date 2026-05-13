from __future__ import annotations

import re
from typing import Optional

from .models import ModelKey

CANONICAL_MODELS = [
    "iPhone 17 Pro Max",
    "iPhone 17 Pro",
    "iPhone 17e",
    "iPhone 17",
    "iPhone Air",
    "iPhone 16 Pro Max",
    "iPhone 16 Pro",
    "iPhone 16 Plus",
    "iPhone 16e",
    "iPhone 16",
    "iPhone 15 Pro Max",
    "iPhone 15 Pro",
    "iPhone 15 Plus",
    "iPhone 15",
]

_MODEL_PATTERNS: list[tuple[re.Pattern, str]] = []
for canonical in CANONICAL_MODELS:
    pattern_str = canonical.replace("iPhone ", r"iPhone\s*").replace(" ", r"\s*")
    _MODEL_PATTERNS.append((re.compile(pattern_str, re.IGNORECASE), canonical))

_CAPACITY_RE = re.compile(r"(\d+)\s*(TB|GB)", re.IGNORECASE)


def normalize_model_name(text: str) -> Optional[str]:
    if not text:
        return None
    for pattern, canonical in _MODEL_PATTERNS:
        if pattern.search(text):
            return canonical
    return None


def normalize_capacity(text: str) -> Optional[str]:
    if not text:
        return None
    m = _CAPACITY_RE.search(text)
    if not m:
        return None
    return f"{m.group(1)}{m.group(2).upper()}"


def parse_model_key(text: str) -> Optional[ModelKey]:
    name = normalize_model_name(text)
    capacity = normalize_capacity(text)
    if name and capacity:
        return ModelKey(name=name, capacity=capacity)
    return None


_PRICE_RE = re.compile(r"([0-9][0-9,]*)\s*円")


def parse_price_jpy(text: str) -> Optional[int]:
    if not text:
        return None
    m = _PRICE_RE.search(text)
    if not m:
        return None
    try:
        return int(m.group(1).replace(",", ""))
    except ValueError:
        return None
