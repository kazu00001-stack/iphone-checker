from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass(frozen=True)
class ModelKey:
    name: str
    capacity: str

    def as_tuple(self) -> tuple[str, str]:
        return (self.name, self.capacity)


@dataclass
class AppleModel:
    key: ModelKey
    price_jpy: int
    url: str
    is_fallback: bool = False


@dataclass
class BuybackQuote:
    key: ModelKey
    site: str
    price_jpy: int
    source_url: str


@dataclass
class ComparisonRow:
    key: ModelKey
    apple_price: int
    apple_is_fallback: bool
    quotes: dict[str, int] = field(default_factory=dict)
    best_site: Optional[str] = None
    best_price: Optional[int] = None
    profit: Optional[int] = None
    miles: int = 0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["model"] = self.key.name
        d["capacity"] = self.key.capacity
        del d["key"]
        return d
