# kdp-tracker

Local-first CLI for authors to log KDP ad spend, sales, and royalties by book.

Built and maintained by **Asdale Dynamics, LLC** (Indiana, formed October 2026).
No API keys, no network calls, no accounts: everything lives in a single JSON
file on your machine.

## What it does

- `add-book` — register a book (title, author, ASIN)
- `log-spend` — record KDP ad spend by book and date
- `log-sales` — record units sold and royalties earned by book and date
- `summary` — profit summary per book (royalties minus spend) plus a grand total
- `export` — write all records and summaries to a CSV file you can open in
  Excel, Google Sheets, or Numbers
- `list-books` — list your tracked books
- `--dry-run` — validate and preview changes without saving anything

## Install

No installation required beyond Python 3.8+:

```bash
python3 -m kdp_tracker add-book "The Massive AI Manual" --author "Dylan Asdale" --asin B0XXXXXXXX
python3 -m kdp_tracker log-spend "The Massive AI Manual" 2026-10-28 42.50
python3 -m kdp_tracker log-sales "The Massive AI Manual" 2026-10-28 12 --royalties 34.80
python3 -m kdp_tracker summary
python3 -m kdp_tracker export kdp_ledger.csv
```

Run `python3 -m kdp_tracker --help` for full usage.

## Data storage

All data is stored locally in `kdp_data.json` in the folder where you run the
tool. You own it, you can back it up, edit it by hand, or delete it. Nothing
is ever transmitted anywhere.

## Dry-run mode

Pass `--dry-run` to any command that writes data. It validates your input and
prints what would happen, without touching the data file. Useful for checking
dates and amounts before they become permanent.

## Tests

Run the test suite with the standard library:

```bash
python3 -m unittest discover -s tests -v
```

## License

MIT License. Copyright (c) 2026 Asdale Dynamics, LLC.

See `LICENSE` for details.

## About Asdale Dynamics, LLC

Asdale Dynamics, LLC is an Indiana LLC (formed October 2026) founded by Dylan
Asdale, a registered nurse turned AI author. We make beginner-friendly AI
education, books, guides, and practical tools — including open-source apps and
templates for authors, small businesses, and anyone who wants technology
explained plain English, step by step, never condescending. Dylan's book *The
Massive AI Manual* and hub site dylanasdale.github.io explain AI "like a friend
would."
