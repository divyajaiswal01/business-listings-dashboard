# Demo video script (3–5 minutes)

| Time | Show | Say |
|------|------|-----|
| 0:00–0:30 | Repo tree | "Three folders: `scraper`, `backend` (FastAPI), `frontend` (React), plus `database` with schema and dump." |
| 0:30–1:45 | `scraper/sources/overpass.py`, then run `python scrape.py --source osm` | Why OpenStreetMap (Google Maps/Justdial ToS forbid scraping). One Overpass query per city bounding box -> OSM tags mapped to my fields -> clean phone/whitespace -> de-duplicate -> CSV -> POST to API in batches of 200. Mention retries, mirror fallback, polite delay. |
| 1:45–2:30 | `http://localhost:8000/docs` | Run `POST /api/listings/bulk` twice: first inserts N rows, second shows `duplicates_skipped = N` (UNIQUE `dedupe_hash` + `INSERT IGNORE`). Then try `/api/dashboard/cities`, `/categories`, `/sources`, and add `?source=...` to show filters. |
| 2:30–3:00 | MySQL shell | `SELECT COUNT(*) FROM listing_master;` and `SELECT city, COUNT(*) ... GROUP BY city;` — numbers match the API. |
| 3:00–4:30 | Dashboard | Summary cards, three charts, click a city bar -> everything re-filters, chip appears, click again to clear. Search the table, paginate. |
| 4:30–5:00 | README | Challenges + what you would improve next. |
