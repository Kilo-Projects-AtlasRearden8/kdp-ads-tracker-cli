"""Data models for the KDP tracker."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Book:
    """A book tracked by the KDP tracker."""

    title: str
    author: Optional[str] = None
    asin: Optional[str] = None


@dataclass
class AdSpend:
    """A single KSP/KDP advertising spend entry."""

    book: str
    date: str  # ISO 8601 date, YYYY-MM-DD
    amount: float  # dollars spent


@dataclass
class Sale:
    """A single book sale / royalty entry."""

    book: str
    date: str  # ISO 8601 date, YYYY-MM-DD
    units: int = 0
    royalties: float = 0.0  # dollars earned
