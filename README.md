# Business Listings Dashboard

A full-stack data project: **scrape** business listings → **store** them in MySQL → **serve** aggregated reports with FastAPI → **visualise** them in a React dashboard.

```
 ┌──────────────┐  clean + dedupe   ┌─────────────────┐   SQL    ┌─────────┐
 │  scraper/    │ ── POST /bulk ──▶ │  backend/       │ ───────▶ │  MySQL  │
 │  (Python)    │   (batches of     │  FastAPI        │ ◀─────── │listing_ │
 │ OSM Overpass │      200)         │  SQLAlchemy     │ GROUP BY │ master  │
 └──────────────┘                   └────────▲────────┘          └─────────┘
                                             │ JSON (/api/dashboard/*, /api/listings)
                                    ┌────────┴────────┐
                                    │  frontend/      │
                                    │  React+Recharts │
                                    └─────────────────┘
```

## Tech stack

| Layer | Tech |
|-------|------|
| Frontend | React 18, Vite, Recharts (plain CSS, light/dark aware) |
| Backend | FastAPI, SQLAlchemy 2.0, Pydantic v2, PyMySQL |
| Database | MySQL 8 (`listing_master`) |
| Scraper | Python, `requests`, OpenStreetMap Overpass API |

## Project structure

```
backend/    FastAPI app (config, models, schemas, crud, routers)
frontend/   React dashboard
scraper/    Data collection + cleaning + uploader CLI
database/   schema.sql, export_dump.sh, listings_dump.sql (generated)
data/       listings.csv + by_task/*.csv written by the scraper (submit these)
```

## Setup

**Prerequisites:** Python 3.10+, Node 18+, MySQL 8 (or Docker).

### 1. Database
```bash
# Option A – local MySQL
mysql -u root -p < database/schema.sql

# Option B – Docker (schema loads automatically on first start)
docker compose up -d
```
This creates `listings_db`, table `listing_master`, and user `listings_user / listings_pass`.

### 2. Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # edit DATABASE_URL if needed
uvicorn app.main:app --reload                          # http://localhost:8000/docs
```

### 3. Collect data (500+ listings, 100+ per scraping task)
Each **scraping task = one city**, and every task must return **at least 100 rows** (the brief asks for 80–100+).
```bash
cd scraper
pip install -r requirements.txt                        # (inside the same venv is fine)
python scrape.py --source osm --per-city 150 --contact you@email.com   # 8 cities x up to 150 rows
```
`--contact` puts your real email in the User-Agent (Overpass blocks anonymous clients with HTTP 406). Finished cities are cached in `data/raw/`, so if the run is interrupted or a city fails, just run the same command again - it resumes. Use `--refresh` to re-fetch everything.
Outputs (cleaned, structured, UTF-8 CSV with header `business_name,category,city,address,phone,source`):
```
data/listings.csv                    all rows combined
data/by_task/listings_<city>.csv     one CSV per scraping task
```
Before uploading, `validate.py` runs a **quality gate**: ≥ 100 rows per task, no empty name/city/source, valid phone format, no duplicates. If it fails, nothing is uploaded and the report shows which task is short. Re-check any CSV at any time with `python validate.py ../data/listings.csv`.
Other useful flags:
```bash
python scrape.py --source osm --cities Pune Mumbai --per-city 300
python scrape.py --source osm --cities Delhi --merge   # redo/add ONE city, keep the others already saved
python scrape.py --source osm --no-upload              # only write the CSV files
python scrape.py --source osm --min-per-task 80        # relax the per-task minimum
python scrape.py --from-csv ../data/listings.csv       # upload a saved CSV later
python scrape.py --source mock --per-city 80           # offline sample data (labelled "Sample Data")
```

### 4. Frontend
```bash
cd frontend
npm install
npm run dev                                            # http://localhost:5173
```
The Vite dev server proxies `/api` to `localhost:8000`, so no CORS setup is needed in dev.

### 5. Create the database dump
```bash
./database/export_dump.sh            # -> database/listings_dump.sql
```
Restore anywhere with `mysql -u root -p < database/listings_dump.sql`.

## Scraping approach

* **Source: OpenStreetMap (Overpass API).** Google Maps and Justdial prohibit automated scraping in their Terms of Service and actively block bots, so I avoided them. OSM is open data (ODbL) with an official query API, which makes collection legal, stable and reproducible. Attribution: © OpenStreetMap contributors.
* **Query:** one request per city bounding box for named places tagged `amenity=*` (restaurant, cafe, bank, pharmacy, …) or `shop=*` (supermarket, clothes, electronics, …).
* **Field mapping:** `name → business_name`, `amenity/shop → category` (title-cased), configured city → `city`, `addr:*` tags joined → `address`, `phone / contact:phone → phone`, `source = "OpenStreetMap"`.
* **Cleaning (`cleaning.py`):** collapse whitespace; keep the first phone number, strip punctuation, reject numbers that are not 8–15 digits; drop rows with no name/city; remove duplicates.
* **Quality + balance:** records with an address and/or phone are preferred, then capped per city so one city does not dominate.
* **Politeness / resilience:** descriptive User-Agent, delay between cities, retries with back-off on 429/504, fallback mirror server.
* **Mock fallback:** if the network is blocked, `--source mock` generates reproducible sample rows tagged `Sample Data`, so they can never be mistaken for scraped data.

## Database design

`listing_master` follows the suggested schema plus one helper column:

| Column | Type | Notes |
|--------|------|-------|
| id | INT UNSIGNED PK AUTO_INCREMENT | |
| business_name | VARCHAR(255) NOT NULL | |
| category | VARCHAR(100) NOT NULL | indexed |
| city | VARCHAR(100) NOT NULL | indexed |
| address | TEXT NULL | |
| phone | VARCHAR(50) NULL | optional per the brief |
| source | VARCHAR(50) NOT NULL | indexed |
| **dedupe_hash** | CHAR(64) UNIQUE | `sha256(name\|city\|address\|source)` – makes inserts idempotent |
| created_at | DATETIME DEFAULT CURRENT_TIMESTAMP | |

Indexes on `city`, `category`, `source` keep the `GROUP BY` reports fast.

## API reference

Interactive docs: `http://localhost:8000/docs`

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/listings/bulk` | **Bulk insert** up to 1000 listings. Returns `{received, inserted, duplicates_skipped}` |
| GET | `/api/dashboard/cities` | **City-wise count** (`?limit=` top-N) |
| GET | `/api/dashboard/categories` | **Category-wise count** |
| GET | `/api/dashboard/sources` | **Source-wise count** |
| GET | `/api/dashboard/summary` | Totals: listings, cities, categories, sources, with-phone |
| GET | `/api/dashboard/insights` | Story data: category mix per city, address/phone coverage per city, most repeated business names |
| GET | `/api/listings` | Paginated browse; `q`, `city`, `category`, `source`, `page`, `page_size` |
| GET | `/health` | Liveness + DB connectivity |

All dashboard endpoints accept optional `city`, `category`, `source` filters (this powers click-to-filter in the UI).

Example:
```bash
curl "http://localhost:8000/api/dashboard/categories?limit=5&city=Pune"
# {"data":[{"label":"Restaurant","count":42}, ...],"total_groups":15}
```

## Dashboard storyline

The page is written as a short data story rather than a wall of charts. Every sentence is **generated from the API numbers** (nothing hard-coded), so it changes when you filter.

1. **Headline findings** (top of page): biggest category, the city whose mix is most distinctive, the most repeated business name, and data-quality gaps.
2. **What we collected**: listings per city and per source. If the per-city bars are nearly equal, the page says so: collection was capped per city, so city *size* is not a finding.
3. **What kind of businesses**: top categories + a 100%-stacked chart of what each city is made of (compare the shape of the bars, not their length).
4. **Who shows up again and again**: repeated names reveal chains and multi-branch networks.
5. **How complete is the data**: address and phone coverage per city.
6. **Explore**: searchable, paginated table.

Click any bar or slice to filter the whole page (findings, charts and table all re-query the API).

## Key design decisions

* **Idempotent bulk insert.** `INSERT IGNORE` + a UNIQUE hash means re-running the scraper never creates duplicates and never fails; the response reports how many were skipped.
* **Thin routers, logic in `crud.py`.** One `count_by()` function serves all three reports; the column is chosen from a whitelist so user input never becomes SQL.
* **Aggregation in SQL, not Python.** `GROUP BY` on indexed columns; the frontend only receives `{label, count}`.
* **Validation at the edge.** Pydantic trims text, enforces lengths and the 1000-row batch cap (422 on bad input).
* **One filter state in React.** Clicking a bar/slice sets a filter; charts, summary cards and table all re-query the API. Stale responses are ignored (`cancelled` flag), search is debounced.

## Challenges faced

1. **Choosing a legal data source.** Google Maps/Justdial restrict scraping, so I used OpenStreetMap's official API and documented the reasoning.
2. **Patchy data quality.** OSM entries often lack address or phone (in my run ~90% had an address but only ~25% a phone number, so phone is optional). I made both optional, normalised phones, and ranked records by completeness before capping per city.
3. **A city failing silently.** One city returned HTTP 502/504 and the first version of the quality check ignored it. The check now takes the list of requested cities and fails if any has fewer than 100 rows; `--merge` re-fetches only that city.
4. **Duplicates on re-runs.** Solved with a hash + UNIQUE key and `INSERT IGNORE`, then verified: second upload → `inserted: 0`.
5. **SQLAlchemy 2.0 `rowcount`.** `Session.execute()` with a list of rows returned a result without `.rowcount`; executing through `db.connection()` fixed it so the API reports accurate insert counts.
6. **Overpass rejecting / timing out.** The main server answered `406 Not Acceptable` to an anonymous User-Agent and large city queries timed out on a mirror. Fixed by sending a real contact in the User-Agent, skipping servers that reject the request, rotating over 4 servers, splitting each city into 4 smaller tiles, and caching finished cities so reruns resume.
7. **Making the dashboard say something.** The first version only displayed counts. I added an insights endpoint (city x category matrix, completeness per city, repeated names) and generated the narrative from the data. I also noticed the per-city cap makes city bars equal, so the UI detects that and tells the reader to compare mix instead of size.
8. **Readable charts.** Ten cities/categories at most (`limit`), horizontal bars for long category names, and an "x of N" subtitle so nothing is hidden silently.

## Testing performed

Scraper quality gate checked: 80 rows/task is rejected (no upload), 120 rows/task passes and writes 8 per-task CSVs + 1 combined CSV. Backend checked against a real MariaDB/MySQL-compatible server: schema creation, 640-row bulk insert, repeat upload (0 inserted / 640 skipped), all report endpoints, filters, pagination/search, and 422 validation. Frontend production build compiles (`npm run build`).

## Possible improvements

Alembic migrations, automated tests (pytest + Vitest), scheduled scraping, an additional source (e.g. Sulekha where terms allow), CSV export button, authentication on the insert endpoint.
