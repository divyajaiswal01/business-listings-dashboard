"""CLI: collect listings -> clean -> validate -> save CSVs -> POST to the FastAPI bulk endpoint.

One SCRAPING TASK = one city. Every task must yield at least --min-per-task rows (default 100).

Output (in --out-dir, default ../data):
  listings.csv                 all cleaned rows combined
  by_task/listings_<city>.csv  one CSV per scraping task

Examples
  python scrape.py --source osm --per-city 150            # real data (needs internet)
  python scrape.py --source mock --per-city 120           # offline sample data
  python scrape.py --source osm --no-upload               # only write the CSVs
  python scrape.py --from-csv ../data/listings.csv        # validate + upload a saved CSV
"""
import argparse
import csv
import sys
from pathlib import Path

import requests

import cleaning
import validate
from sources import mock, overpass

DEFAULT_OUT = Path(__file__).resolve().parent.parent / "data"
BATCH_SIZE = 200  # API accepts up to 1000 per call


def save_csv(records: list[dict], path: Path) -> None:
    """utf-8-sig = UTF-8 with BOM, so Excel shows non-English names correctly."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=cleaning.FIELDS)
        writer.writeheader()
        writer.writerows(records)
    print(f"Saved {len(records)} rows -> {path}")


def save_all(records: list[dict], out_dir: Path) -> None:
    save_csv(records, out_dir / "listings.csv")
    for city in sorted({r["city"] for r in records}):
        rows = [r for r in records if r["city"] == city]
        save_csv(rows, out_dir / "by_task" / f"listings_{city.lower().replace(' ', '_')}.csv")


def load_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as fh:
        return [{k: (v or None) for k, v in row.items()} for row in csv.DictReader(fh)]


def upload(records: list[dict], api_url: str) -> None:
    endpoint = f"{api_url.rstrip('/')}/api/listings/bulk"
    totals = {"received": 0, "inserted": 0, "duplicates_skipped": 0}
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i : i + BATCH_SIZE]
        resp = requests.post(endpoint, json={"listings": batch}, timeout=60)
        resp.raise_for_status()
        for k, v in resp.json().items():
            totals[k] += v
        print(f"  batch {i // BATCH_SIZE + 1}: {resp.json()}")
    print(f"Upload finished: {totals}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--source", choices=["osm", "mock"], default="osm")
    p.add_argument("--cities", nargs="+", help="Default: all configured cities")
    p.add_argument("--per-city", type=int, default=150, help="Target records per city (task)")
    p.add_argument("--min-per-task", type=int, default=100, help="Minimum rows each task must have")
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT, help="Folder for the CSV files")
    p.add_argument("--allow-short", action="store_true", help="Upload even if validation fails")
    p.add_argument("--contact", help="Your real email (sent in the User-Agent; Overpass blocks anonymous clients)")
    p.add_argument("--merge", action="store_true",
                   help="Keep other cities already saved in <out-dir>/by_task (use to add/redo a single city)")
    p.add_argument("--refresh", action="store_true", help="Ignore cached city results in <out-dir>/raw")
    p.add_argument("--from-csv", type=Path, help="Skip scraping; upload this CSV instead")
    p.add_argument("--api-url", default="http://localhost:8000")
    p.add_argument("--no-upload", action="store_true")
    args = p.parse_args()

    expected = None  # cities that MUST be present for the quality gate
    if args.from_csv:
        records = load_csv(args.from_csv)
    else:
        if args.source == "osm":
            cities = args.cities or list(overpass.CITY_BBOXES)
            expected = cities
            unknown = [c for c in cities if c not in overpass.CITY_BBOXES]
            if unknown:
                sys.exit(f"Unknown city {unknown}. Choose from: {', '.join(overpass.CITY_BBOXES)}")
            if args.contact:
                overpass.CONTACT = args.contact
            if not overpass.CONTACT:
                print("TIP: pass --contact you@email.com (or set SCRAPER_CONTACT) - "
                      "public Overpass servers may reject anonymous clients with HTTP 406.")
            raw = overpass.scrape(cities, args.per_city, cache_dir=args.out_dir / "raw", refresh=args.refresh)
        else:
            raw = mock.scrape(args.cities, args.per_city)
            expected = args.cities or mock.CITIES

        cleaned = [r for r in (cleaning.normalise(x) for x in raw) if r]
        records = cleaning.dedupe(cleaned)
        print(f"Raw {len(raw)} -> cleaned {len(cleaned)} -> unique {len(records)}")
        if args.merge:  # add the other cities that are already on disk
            fresh = {r["city"] for r in records}
            kept = [r for f in sorted((args.out_dir / "by_task").glob("listings_*.csv"))
                    for r in load_csv(f) if r["city"] not in fresh]
            records = cleaning.dedupe(records + kept)
            print(f"Merged with {len(kept)} saved rows from other cities -> {len(records)} total")
        save_all(records, args.out_dir)

    # Quality gate: every task >= min rows, no empty fields, valid phones, no duplicates.
    problems, stats = validate.validate(records, args.min_per_task, expected)
    validate.print_report(problems, stats, args.min_per_task)
    if len(records) < 500:
        problems.append(f"Only {len(records)} total records (500+ required)")
        print(f"WARNING: only {len(records)} total records (500+ required).")

    if problems and not args.allow_short:
        print("\nValidation failed -> NOT uploading. Fix the data (e.g. raise --per-city, add cities) "
              "or pass --allow-short.")
        return 1
    if not args.no_upload:
        upload(records, args.api_url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
