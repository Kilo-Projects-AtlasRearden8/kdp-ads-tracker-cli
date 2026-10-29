"""KDP ad spend, sales, and royalty tracker for authors."""

from .models import AdSpend, Book, Sale
from .storage import Storage

__all__ = ["AdSpend", "Book", "Sale", "Storage"]
__version__ = "1.0.0"
