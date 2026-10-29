"""Quality gate for scraped data.  Run on its own:  python validate.py ../data/listings.csv

Checks (each failure is reported, nothing is silently fixed):
  1. every scraping task (= city) has at least MIN_PER_TASK rows (and every requested city exists)
  2. required columns exist and business_name / city / source are never empty
  3. no duplicate rows (name + city + address + source)
  4. phone numbers, when present, are 8-15 digits with an optional leading '+'
"""
import csv
import re
import sys
from collections import Counter
from pathlib import Path

import cleaning

PHONE_RE = re.compile(r"^\+?\d{8,15}$")


def validate(records: list[dict], min_per_task: int = 100, expected_tasks: list[str] | None = None) -> tuple[list[str], dict]:
    problems: list[str] = []
    by_city = Counter(r["city"] for r in records if r.get("city"))
    for city in expected_tasks or []:  # a task that returned nothing must not pass silently
        by_city.setdefault(city, 0)

    for city, n in sorted(by_city.items()):
        if n < min_per_task:
            problems.append(f"Task '{city}' has {n} rows (< {min_per_task} required)")

    for i, r in enumerate(records, start=2):  # row 1 of the CSV is the header
        for col in ("business_name", "city", "source"):
            if not r.get(col):
                problems.append(f"Row {i}: '{col}' is empty")
        if r.get("phone") and not PHONE_RE.match(r["phone"]):
            problems.append(f"Row {i}: invalid phone '{r['phone']}'")

    if len(cleaning.dedupe(records)) != len(records):
        problems.append("Duplicate rows found")

    n = len(records) or 1
    stats = {
        "total_rows": len(records),
        "rows_per_task": dict(by_city),
        "with_phone_pct": round(100 * sum(bool(r.get("phone")) for r in records) / n, 1),
        "with_address_pct": round(100 * sum(bool(r.get("address")) for r in records) / n, 1),
        "distinct_categories": len({r.get("category") for r in records}),
    }
    return problems, stats


def print_report(problems: list[str], stats: dict, min_per_task: int) -> None:
    print("\n=== Data quality report ===")
    print(f"Total rows            : {stats['total_rows']}")
    print(f"Distinct categories   : {stats['distinct_categories']}")
    print(f"Rows with address     : {stats['with_address_pct']}%")
    print(f"Rows with phone       : {stats['with_phone_pct']}%")
    print(f"Rows per task (min {min_per_task}):")
    for city, n in sorted(stats["rows_per_task"].items()):
        print(f"  {'OK ' if n >= min_per_task else 'LOW'} {city:<12} {n}")
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems[:15]:
            print(f"  - {p}")
        if len(problems) > 15:
            print(f"  ... and {len(problems) - 15} more")
    else:
        print("\nAll checks passed.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python validate.py <file.csv> [min_per_task]")
    min_n = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    with Path(sys.argv[1]).open(encoding="utf-8-sig") as fh:
        rows = [{k: (v or None) for k, v in row.items()} for row in csv.DictReader(fh)]
    probs, st = validate(rows, min_n)
    print_report(probs, st, min_n)
    sys.exit(1 if probs else 0)
