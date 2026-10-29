"""Command-line interface for the KDP tracker."""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import date
from typing import List, Optional, Sequence

from .models import AdSpend, Book, Sale
from .storage import DEFAULT_DATA_FILE, Storage


DATE_FORMAT = "%Y-%m-%d"


def parse_date(value: str) -> str:
    """Validate and normalize a date string to YYYY-MM-DD."""
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"invalid date '{value}': use YYYY-MM-DD (e.g. 2026-10-29)"
        ) from exc
    return parsed.strftime(DATE_FORMAT)


def parse_amount(value: str) -> float:
    try:
        amount = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid amount '{value}': must be a number") from exc
    if amount < 0:
        raise argparse.ArgumentTypeError(f"invalid amount '{value}': must not be negative")
    return amount


def parse_units(value: str) -> int:
    try:
        units = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid units '{value}': must be a whole number") from exc
    if units < 0:
        raise argparse.ArgumentTypeError(f"invalid units '{value}': must not be negative")
    return units


def require_book(storage: Storage, title: str) -> Book:
    book = storage.find_book(title)
    if book is None:
        titles = ", ".join(storage.all_titles()) or "(none yet)"
        raise SystemExit(
            f"error: book '{title}' not found. Known books: {titles}\n"
            f"Add it first: kdp-tracker add-book \"{title}\""
        )
    return book


def cmd_add_book(args: argparse.Namespace, storage: Storage) -> None:
    book = Book(title=args.title, author=args.author, asin=args.asin)
    if storage.find_book(args.title):
        print(f"notice: book '{args.title}' already exists; skipping.")
        return
    if args.dry_run:
        print(f"[dry-run] would add book: {book.title!r}"
              + (f" (author={book.author!r})" if book.author else "")
              + (f" (asin={book.asin!r})" if book.asin else ""))
        return
    storage.add_book(book)
    storage.save()
    print(f"added book: {args.title}")


def cmd_log_spend(args: argparse.Namespace, storage: Storage) -> None:
    require_book(storage, args.title)
    entry = AdSpend(book=args.title, date=args.date, amount=args.amount)
    if args.dry_run:
        print(f"[dry-run] would log spend: {args.title} | {args.date} | ${args.amount:.2f}")
        return
    storage.record_spend(entry)
    storage.save()
    print(f"logged spend: ${args.amount:.2f} for '{args.title}' on {args.date}")


def cmd_log_sales(args: argparse.Namespace, storage: Storage) -> None:
    require_book(storage, args.title)
    entry = Sale(book=args.title, date=args.date, units=args.units, royalties=args.royalties)
    if args.dry_run:
        print(
            f"[dry-run] would log sales: {args.title} | {args.date} | "
            f"{args.units} units | ${args.royalties:.2f} royalties"
        )
        return
    storage.record_sale(entry)
    storage.save()
    print(
        f"logged sales: {args.units} unit(s), ${args.royalties:.2f} royalties "
        f"for '{args.title}' on {args.date}"
    )


def cmd_summary(args: argparse.Namespace, storage: Storage) -> None:
    if args.book:
        summaries = [storage.summary_for_book(args.book)]
    else:
        summaries = storage.all_summaries()

    if not summaries:
        print("no books tracked yet. Add one with: kdp-tracker add-book \"Title\"")
        return

    print(f"{'Book':<30} {'Spend':>10} {'Units':>7} {'Royalties':>11} {'Profit':>10}")
    print("-" * 72)
    for summary in summaries:
        print(
            f"{summary['book']:<30} "
            f"${summary['total_spend']:>9.2f} "
            f"{summary['total_units']:>7} "
            f"${summary['total_royalties']:>10.2f} "
            f"${summary['profit']:>9.2f}"
        )

    if not args.book:
        total_spend = sum(s["total_spend"] for s in summaries)
        total_units = sum(s["total_units"] for s in summaries)
        total_royalties = sum(s["total_royalties"] for s in summaries)
        total_profit = total_royalties - total_spend
        print("-" * 72)
        print(
            f"{'TOTAL':<30} "
            f"${total_spend:>9.2f} "
            f"{total_units:>7} "
            f"${total_royalties:>10.2f} "
            f"${total_profit:>9.2f}"
        )


def cmd_export(args: argparse.Namespace, storage: Storage) -> None:
    path = args.file
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["record_type", "book", "date", "amount", "units", "royalties"]
        )
        for entry in storage.spend:
            writer.writerow(["spend", entry.book, entry.date, f"{entry.amount:.2f}", "", ""])
        for entry in storage.sales:
            writer.writerow(["sale", entry.book, entry.date, "", entry.units, f"{entry.royalties:.2f}"])

        writer.writerow([])
        writer.writerow(["summary", "book", "total_spend", "total_units", "total_royalties", "profit"])
        for summary in storage.all_summaries():
            writer.writerow(
                [
                    "summary",
                    summary["book"],
                    f"{summary['total_spend']:.2f}",
                    summary["total_units"],
                    f"{summary['total_royalties']:.2f}",
                    f"{summary['profit']:.2f}",
                ]
            )
    print(f"exported to {path}")


def cmd_list_books(args: argparse.Namespace, storage: Storage) -> None:
    titles = storage.all_titles()
    if not titles:
        print("no books tracked yet.")
        return
    print("tracked books:")
    for title in titles:
        print(f"  - {title}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kdp-tracker",
        description=(
            "Log KDP ad spend, sales, and royalties by book with local JSON "
            "storage, CSV export, and profit summaries. Local-first: no keys, "
            "no network."
        ),
    )
    parser.add_argument(
        "--data",
        default=DEFAULT_DATA_FILE,
        help="path to the JSON data file (default: kdp_data.json in the current folder)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_dry_run(sub: argparse.ArgumentParser) -> None:
        sub.add_argument(
            "--dry-run",
            action="store_true",
            help="validate and print what would happen without saving changes",
        )

    # add-book
    p = subparsers.add_parser("add-book", help="register a book to track")
    p.add_argument("title", help="book title")
    p.add_argument("--author", help="author name")
    p.add_argument("--asin", help="Amazon ASIN")
    add_dry_run(p)
    p.set_defaults(func=cmd_add_book)

    # log-spend
    p = subparsers.add_parser("log-spend", help="log ad spend for a book")
    p.add_argument("title", help="book title")
    p.add_argument("date", type=parse_date, help="date (YYYY-MM-DD)")
    p.add_argument("amount", type=parse_amount, help="amount spent in dollars")
    add_dry_run(p)
    p.set_defaults(func=cmd_log_spend)

    # log-sales
    p = subparsers.add_parser("log-sales", help="log sales and royalties for a book")
    p.add_argument("title", help="book title")
    p.add_argument("date", type=parse_date, help="date (YYYY-MM-DD)")
    p.add_argument("units", type=parse_units, help="units sold")
    p.add_argument("--royalties", type=parse_amount, default=0.0, help="royalties earned in dollars")
    add_dry_run(p)
    p.set_defaults(func=cmd_log_sales)

    # summary
    p = subparsers.add_parser("summary", help="show profit summary by book")
    p.add_argument("--book", help="show summary for one book only")
    p.set_defaults(func=cmd_summary)

    # export
    p = subparsers.add_parser("export", help="export all records to a CSV file")
    p.add_argument("file", help="output CSV file path")
    p.set_defaults(func=cmd_export)

    # list-books
    p = subparsers.add_parser("list-books", help="list tracked books")
    p.set_defaults(func=cmd_list_books)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    storage = Storage(args.data)
    try:
        args.func(args, storage)
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 - report friendly errors to the user
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
