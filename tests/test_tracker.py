# Tests for the KDP tracker

import argparse
import json
import os
import tempfile
import unittest

from kdp_tracker.models import AdSpend, Book, Sale
from kdp_tracker.storage import Storage
from kdp_tracker.cli import parse_date, parse_amount, parse_units, main


class TestDateParsing(unittest.TestCase):
    def test_valid_iso_dates(self):
        self.assertEqual(parse_date("2026-10-29"), "2026-10-29")
        self.assertEqual(parse_date("2026-01-01"), "2026-01-01")

    def test_invalid_dates_rejected(self):
        for bad in ["2026-13-01", "2026-02-30", "10-29-2026", "29/10/2026", "not-a-date", ""]:
            with self.assertRaises(argparse.ArgumentTypeError):
                parse_date(bad)


class TestAmountParsing(unittest.TestCase):
    def test_valid_amounts(self):
        self.assertEqual(parse_amount("10"), 10.0)
        self.assertEqual(parse_amount("42.50"), 42.5)
        self.assertEqual(parse_amount("0"), 0.0)

    def test_negative_and_invalid_rejected(self):
        for bad in ["-5", "abc", "10.5.2"]:
            with self.assertRaises(argparse.ArgumentTypeError):
                parse_amount(bad)


class TestUnitsParsing(unittest.TestCase):
    def test_valid_units(self):
        self.assertEqual(parse_units("3"), 3)
        self.assertEqual(parse_units("0"), 0)

    def test_invalid_units_rejected(self):
        for bad in ["-1", "3.5", "abc"]:
            with self.assertRaises(argparse.ArgumentTypeError):
                parse_units(bad)


class TestTotalsAndDates(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = os.path.join(self.tmpdir, "kdp_data.json")
        self.storage = Storage(self.path)
        self.storage.add_book(Book(title="The Massive AI Manual", author="Dylan Asdale", asin="B0DEMO"))
        self.storage.save()

    def test_summary_totals(self):
        self.storage.record_spend(AdSpend(book="The Massive AI Manual", date="2026-10-25", amount=50.00))
        self.storage.record_spend(AdSpend(book="The Massive AI Manual", date="2026-10-28", amount=25.00))
        self.storage.record_sale(Sale(book="The Massive AI Manual", date="2026-10-26", units=5, royalties=17.50))
        self.storage.record_sale(Sale(book="The Massive AI Manual", date="2026-10-29", units=3, royalties=10.50))
        self.storage.save()

        summary = self.storage.summary_for_book("The Massive AI Manual")
        self.assertEqual(summary["total_spend"], 75.00)
        self.assertEqual(summary["total_units"], 8)
        self.assertEqual(summary["total_royalties"], 28.00)
        self.assertEqual(summary["profit"], -47.00)
        self.assertEqual(summary["spend_count"], 2)
        self.assertEqual(summary["sale_count"], 2)

    def test_profit_positive_case(self):
        self.storage.record_spend(AdSpend(book="The Massive AI Manual", date="2026-10-25", amount=10.00))
        self.storage.record_sale(Sale(book="The Massive AI Manual", date="2026-10-26", units=10, royalties=35.00))
        summary = self.storage.summary_for_book("The Massive AI Manual")
        self.assertEqual(summary["profit"], 25.00)

    def test_date_filtering_by_book(self):
        self.storage.add_book(Book(title="Other Book"))
        self.storage.record_spend(AdSpend(book="The Massive AI Manual", date="2026-10-01", amount=5.00))
        self.storage.record_spend(AdSpend(book="Other Book", date="2026-10-02", amount=999.00))
        summary = self.storage.summary_for_book("The Massive AI Manual")
        self.assertEqual(summary["total_spend"], 5.00)
        self.assertEqual(summary["book"], "The Massive AI Manual")

    def test_all_summaries_includes_all_books(self):
        self.storage.add_book(Book(title="Second Book"))
        self.storage.record_spend(AdSpend(book="Second Book", date="2026-10-01", amount=4.00))
        summaries = self.storage.all_summaries()
        titles = {s["book"] for s in summaries}
        self.assertEqual(titles, {"The Massive AI Manual", "Second Book"})

    def test_persistence_round_trip(self):
        self.storage.record_spend(AdSpend(book="The Massive AI Manual", date="2026-10-01", amount=1.25))
        self.storage.save()
        loaded = Storage(self.path)
        self.assertEqual(len(loaded.spend), 1)
        self.assertEqual(loaded.spend[0].amount, 1.25)
        self.assertEqual(loaded.spend[0].date, "2026-10-01")

    def test_unknown_book_lookup_returns_none(self):
        self.assertIsNone(self.storage.find_book("Does Not Exist"))


class TestCliMain(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = os.path.join(self.tmpdir, "kdp_data.json")

    def run_cli(self, *args):
        return main(["--data", self.path, *list(args)])

    def test_add_book_then_summary(self):
        self.assertEqual(self.run_cli("add-book", "Demo Book"), 0)
        code = self.run_cli("summary", "--book", "Demo Book")
        self.assertEqual(code, 0)

    def test_log_spend_invalid_date_fails(self):
        with self.assertRaises(SystemExit):
            self.run_cli("log-spend", "Demo Book", "not-a-date", "10")

    def test_dry_run_does_not_write(self):
        self.run_cli("add-book", "Dry Run Book", "--dry-run")
        self.assertFalse(os.path.exists(self.path))

    def test_export_creates_csv(self):
        self.run_cli("add-book", "Demo Book")
        self.run_cli("log-spend", "Demo Book", "2026-10-01", "10.00")
        self.run_cli("log-sales", "Demo Book", "2026-10-02", "2", "--royalties", "7.00")
        out = os.path.join(self.tmpdir, "ledger.csv")
        self.assertEqual(self.run_cli("export", out), 0)
        self.assertTrue(os.path.exists(out))
        with open(out, encoding="utf-8") as handle:
            content = handle.read()
        self.assertIn("spend", content)
        self.assertIn("sale", content)
        self.assertIn("summary", content)


if __name__ == "__main__":
    unittest.main()
