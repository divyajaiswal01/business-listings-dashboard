"""Source: OpenStreetMap via the public Overpass API.

WHY THIS SOURCE?
Google Maps and Justdial forbid automated scraping in their Terms of Service (and block
bots). OpenStreetMap is an open database (ODbL licence) with an official query API, so
we can collect real business data legally and reliably. Credit: (c) OpenStreetMap contributors.

HOW IT WORKS
1. Each city bounding box is split into 2x2 tiles (small queries do not time out).
2. Each tile is one Overpass query for named shops / amenities (restaurants, banks, ...).
3. Requests rotate over several public servers; a server that answers 403/406 (it rejects
   our User-Agent) is skipped for the rest of the run, 429/5xx/timeouts are retried.
4. OSM tags are mapped to our fields; the best (most complete) records are kept per city.
5. Each finished city is cached in <out-dir>/raw/<city>.json, so a re-run resumes where it stopped.
"""
import json
import os
import time
from pathlib import Path

import requests

SOURCE_NAME = "OpenStreetMap"

ENDPOINTS = [  # tried in order; blocked / failing ones are skipped
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

# Overpass admins block anonymous / generic clients. Put a REAL contact here, or set
# the env var SCRAPER_CONTACT, or pass --contact you@email.com to scrape.py.
CONTACT = os.environ.get("SCRAPER_CONTACT", "")

# city -> (south, west, north, east)
CITY_BBOXES = {
    "Pune": (18.43, 73.75, 18.63, 73.98),
    "Mumbai": (18.89, 72.77, 19.27, 72.99),
    "Delhi": (28.50, 77.05, 28.74, 77.35),
    "Bengaluru": (12.85, 77.48, 13.10, 77.75),
    "Hyderabad": (17.30, 78.35, 17.50, 78.60),
    "Chennai": (12.92, 80.15, 13.15, 80.31),
    "Kolkata": (22.48, 88.28, 22.64, 88.45),
    "Ahmedabad": (22.95, 72.50, 23.10, 72.67),
}

# Business-like OSM values we keep (keeps the category chart readable).
AMENITIES = "restaurant|cafe|fast_food|bank|pharmacy|clinic|dentist|hospital|school|college|cinema|gym|fuel|bar|veterinary"
SHOPS = "supermarket|clothes|electronics|mobile_phone|bakery|jewelry|hairdresser|beauty|furniture|books|car_repair|convenience|hardware|optician|shoes"

_blocked: set[str] = set()  # endpoints that rejected us this run


def _headers() -> dict:
    who = f" contact: {CONTACT}" if CONTACT else ""
    return {
        "User-Agent": f"business-listings-dashboard/1.1 (student internship assignment;{who})",
        "Accept": "application/json",
        "Referer": "https://github.com/",
    }


def _tiles(bbox, n: int = 2):
    s, w, nn, e = bbox
    dlat, dlon = (nn - s) / n, (e - w) / n
    for i in range(n):
        for j in range(n):
            yield (s + i * dlat, w + j * dlon, s + (i + 1) * dlat, w + (j + 1) * dlon)


def build_query(bbox, limit: int) -> str:
    s, w, n, e = (round(x, 5) for x in bbox)
    area = f"({s},{w},{n},{e})"
    return (
        f'[out:json][timeout:60];\n(\n'
        f'  nwr["name"]["amenity"~"^({AMENITIES})$"]{area};\n'
        f'  nwr["name"]["shop"~"^({SHOPS})$"]{area};\n'
        f');\nout tags center {limit};'
    )


def run_query(query: str, rounds: int = 3) -> list[dict] | None:
    """POST one query, rotating over servers. Returns elements, or None if every server failed."""
    for rnd in range(rounds):
        live = [u for u in ENDPOINTS if u not in _blocked]
        if not live:
            print("  x every server rejected the request. Set a real contact "
                  "(--contact you@email.com) or try again later.")
            return None
        for url in live:
            host = url.split("/")[2]
            try:
                resp = requests.post(url, data={"data": query}, headers=_headers(), timeout=100)
            except requests.RequestException as err:
                print(f"    ! {host}: {type(err).__name__} - trying next server")
                continue
            if resp.status_code in (403, 406):
                _blocked.add(url)
                print(f"    ! {host}: HTTP {resp.status_code} (request rejected) - skipping this server")
                continue
            if resp.status_code in (429, 502, 503, 504):
                print(f"    ! {host}: HTTP {resp.status_code} (busy) - trying next server")
                continue
            try:
                resp.raise_for_status()
                return resp.json().get("elements", [])
            except (requests.RequestException, ValueError) as err:
                print(f"    ! {host}: {err} - trying next server")
        wait = 15 * (rnd + 1)
        print(f"    all servers failed this round; waiting {wait}s")
        time.sleep(wait)
    return None


def _address(tags: dict) -> str | None:
    if tags.get("addr:full"):
        return tags["addr:full"]
    parts = [
        tags.get("addr:housenumber"), tags.get("addr:street"),
        tags.get("addr:suburb") or tags.get("addr:neighbourhood"),
        tags.get("addr:city"), tags.get("addr:postcode"),
    ]
    parts = [p for p in parts if p]
    return ", ".join(parts) if parts else None


def _category(tags: dict) -> str:
    value = tags.get("amenity") or tags.get("shop") or "other"
    return value.replace("_", " ").title()


def _completeness(rec: dict) -> int:
    """Used to keep the most useful records when we cap per city."""
    return int(bool(rec["address"])) + int(bool(rec["phone"]))


def fetch_city(city: str, bbox, per_city: int, tile_delay: float = 2.0) -> list[dict]:
    seen: set[tuple] = set()
    records: list[dict] = []
    tiles_ok = 0
    for k, tile in enumerate(_tiles(bbox), start=1):
        elements = run_query(build_query(tile, limit=per_city * 2))
        if elements is None:
            print(f"  tile {k}/4: failed")
            continue
        tiles_ok += 1
        fresh = 0
        for el in elements:
            key = (el.get("type"), el.get("id"))
            tags = el.get("tags", {})
            if key in seen or not tags.get("name"):
                continue
            seen.add(key)
            fresh += 1
            records.append({
                "business_name": tags["name"],
                "category": _category(tags),
                "city": city,
                "address": _address(tags),
                "phone": tags.get("phone") or tags.get("contact:phone"),
                "source": SOURCE_NAME,
            })
        print(f"  tile {k}/4: {fresh} new records")
        time.sleep(tile_delay)  # be polite to the public servers
    if tiles_ok == 0:
        return []
    records.sort(key=_completeness, reverse=True)  # best records first
    return records[:per_city]


def scrape(cities: list[str], per_city: int, cache_dir: Path | None = None, refresh: bool = False) -> list[dict]:
    out: list[dict] = []
    for city in cities:
        cache = cache_dir / f"{city.lower()}.json" if cache_dir else None
        if cache and cache.exists() and not refresh:
            recs = json.loads(cache.read_text(encoding="utf-8"))
            print(f"[{SOURCE_NAME}] {city}: {len(recs)} records from cache ({cache.name}); use --refresh to re-fetch")
        else:
            print(f"[{SOURCE_NAME}] {city} ...")
            recs = fetch_city(city, CITY_BBOXES[city], per_city)
            if cache and recs:  # only cache successes, so failed cities are retried next run
                cache.parent.mkdir(parents=True, exist_ok=True)
                cache.write_text(json.dumps(recs, ensure_ascii=False), encoding="utf-8")
        print(f"  -> {len(recs)} records for {city}")
        out.extend(recs)
    return out
