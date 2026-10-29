"""Local JSON storage for the KDP tracker."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from typing import Dict, List, Optional

from .models import AdSpend, Book, Sale

DEFAULT_DATA_FILE = "kdp_data.json"


class Storage:
    """Loads and saves tracker state to a local JSON file.

    The store is local-first: nothing is sent over the network, no API keys
    are required, and all data lives in a single JSON file you control.
    """

    def __init__(self, path: str = DEFAULT_DATA_FILE) -> None:
        self.path = path
        self.books: List[Book] = []
        self.spend: List[AdSpend] = []
        self.sales: List[Sale] = []
        self.load()

    def load(self) -> None:
        """Load state from disk, starting empty if the file is missing."""
        if not os.path.exists(self.path):
            return
        with open(self.path, "r", encoding="utf-8") as handle:
            data: Dict = json.load(handle)
        self.books = [Book(**item) for item in data.get("books", [])]
        self.spend = [AdSpend(**item) for item in data.get("spend", [])]
        self.sales = [Sale(**item) for item in data.get("sales", [])]

    def save(self) -> None:
        """Persist current state to the JSON data file."""
        data: Dict = {
            "books": [asdict(book) for book in self.books],
            "spend": [asdict(entry) for entry in self.spend],
            "sales": [asdict(entry) for entry in self.sales],
        }
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def add_book(self, book: Book) -> None:
        self.books.append(book)

    def find_book(self, title: str) -> Optional[Book]:
        for book in self.books:
            if book.title.lower() == title.lower():
                return book
        return None

    def record_spend(self, entry: AdSpend) -> None:
        self.spend.append(entry)

    def record_sale(self, entry: Sale) -> None:
        self.sales.append(entry)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def spend_for_book(self, title: str) -> List[AdSpend]:
        return [entry for entry in self.spend if entry.book.lower() == title.lower()]

    def sales_for_book(self, title: str) -> List[Sale]:
        return [entry for entry in self.sales if entry.book.lower() == title.lower()]

    def all_titles(self) -> List[str]:
        return [book.title for book in self.books]

    def summary_for_book(self, title: str) -> Dict:
        spend_entries = self.spend_for_book(title)
        sale_entries = self.sales_for_book(title)
        total_spend = sum(entry.amount for entry in spend_entries)
        total_units = sum(entry.units for entry in sale_entries)
        total_royalties = sum(entry.royalties for entry in sale_entries)
        return {
            "book": title,
            "total_spend": round(total_spend, 2),
            "total_units": total_units,
            "total_royalties": round(total_royalties, 2),
            "profit": round(total_royalties - total_spend, 2),
            "spend_count": len(spend_entries),
            "sale_count": len(sale_entries),
        }

    def all_summaries(self) -> List[Dict]:
        return [self.summary_for_book(book.title) for book in self.books]
