# STATUS

## What was built

A local-first Python CLI for authors to log KDP ad spend, sales, and
royalties by book. Built for Dylan Asdale / Asdale Dynamics, LLC
(Indiana, formed October 2026).

Files in this folder:

- `kdp_tracker/__init__.py` — package init, version 1.0.0
- `kdp_tracker/__main__.py` — enables `python3 -m kdp_tracker`
- `kdp_tracker/models.py` — `Book`, `AdSpend`, `Sale` data models
- `kdp_tracker/storage.py` — `Storage`: local JSON load/save, mutations,
  per-book profit summaries, totals
- `kdp_tracker/cli.py` — argparse CLI with subcommands
- `tests/test_tracker.py` — 16 tests (totals, dates, dry-run, export,
  persistence)
- `README.md` — usage and credits
- `LICENSE` — MIT, Copyright (c) 2026 Asdale Dynamics, LLC
- `.gitignore` — ignores `__pycache__`, `kdp_data.json`, venv, etc.
- `STATUS.md` — this file

Subcommands:

- `add-book TITLE [--author NAME] [--asin ID]`
- `log-spend TITLE DATE AMOUNT`
- `log-sales TITLE DATE UNITS [--royalties AMOUNT]`
- `summary [--book TITLE]`
- `export FILE.csv`
- `list-books`

Global flag `--data PATH` sets the JSON storage file (default:
`kdp_data.json` in the current folder). Every mutating command supports
`--dry-run` to validate and preview without saving.

Design principles: local-first, no API keys, no network, no secrets, no
personal data, MIT licensed, credited to Asdale Dynamics, LLC in README
and LICENSE.

## How to run it

Requires Python 3.8+ (tested with Python 3.13.5). No dependencies
outside the standard library.

From this folder:

```bash
python3 -m kdp_tracker add-book "The Massive AI Manual" --author "Dylan Asdale" --asin B0DEMO1234
python3 -m kdp_tracker log-spend "The Massive AI Manual" 2026-10-28 42.50
python3 -m kdp_tracker log-sales "The Massive AI Manual" 2026-10-28 12 --royalties 34.80
python3 -m kdp_tracker summary
python3 -m kdp_tracker export kdp_ledger.csv
python3 -m kdp_tracker log-spend "Title" 2026-10-29 10.00 --dry-run
```

Run the test suite:

```bash
python3 -m unittest discover -t . -s tests
```

## Verification results

- `python3 -m py_compile` on all modules: OK
- `python3 -m unittest discover -t . -s tests`: 16 tests, OK (covers
  date validation, amount/units parsing, per-book totals and profit,
  date filtering by book, all-book summaries, JSON persistence round
  trip, dry-run not writing, CSV export contents, CLI error paths)
- Manual end-to-end run in `/tmp/kilo-e2e`: add-book, log-spend
  (including --dry-run), log-sales, summary, export all worked; output
  CSV contained spend/sale/summary rows; `kdp_data.json` written
  locally only

No lint/typecheck tooling is configured in this project (stdlib only,
no third-party dependencies), so there is no lint or typecheck command
to run.

## Known gaps

- Currency is hard-coded to dollars ($); no currency setting.
- Book titles are matched case-insensitively; duplicate titles with
  different casing collapse into one book.
- ASIN/author are stored but not validated or used in summaries.
- No edit/delete commands for spend or sale entries; edit `kdp_data.json`
  by hand or delete and re-log.
- Summary table can misalign with very long book titles.
- Export writes a single CSV with transactions followed by a summary
  section (separated by a blank row).
- No configuration file; data path set via `--data` on each invocation.
- No GUI or web interface; CLI only.

## Git

Initialized as a local git repo, commit `275bd33` on branch `master`
(identity: Dylan Asdale <dylanasdale@users.noreply.github.com>). No
remote, no push, no tags.
