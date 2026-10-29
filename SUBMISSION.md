# Submission checklist - Honeybee Digital

Send to: **career@honeybeedigital.com**

## Requirements from the brief -> where they are met
| Requirement | How it is met |
|-------------|---------------|
| Each scraping task has 80-100+ entries | One task = one city; `--min-per-task 100` gate in `scraper/validate.py` blocks short tasks |
| Results saved as CSV, cleaned + structured | `data/listings.csv` + `data/by_task/listings_<city>.csv`, fixed 6-column header, UTF-8 |
| Code / scripts included | `scraper/`, `backend/`, `frontend/` |
| 500+ listings, MySQL, FastAPI, React | Whole repo; see README |
| GitHub repo, demo video, SQL dump, README | See below |

## Final steps
1. `cd scraper && python scrape.py --source osm --per-city 150`  -> must end with "All checks passed."
2. Open 2-3 CSVs in Excel / Sheets and eyeball them (names, phones, addresses look sane).
3. `./database/export_dump.sh` -> `database/listings_dump.sql`
4. Record the demo (see DEMO_SCRIPT.md), push to GitHub (commit `data/` too - the CSVs are deliverables).
5. Email the files below.

## Attach / link in the email
- `data/listings.csv` and the `data/by_task/*.csv` files
- `database/listings_dump.sql`
- Code: GitHub link (and a ZIP of `scraper/`, `backend/`, `frontend/` as backup)
- Demo video link

## Email draft
**Subject:** Data Science Intern Assignment - <Your Name>

Hi Team Honeybee Digital,

Please find my assignment submission attached/linked below.

- GitHub repository: <link>
- Demo video (about 4 min): <link>
- Data: `listings.csv` (<N> cleaned rows) plus one CSV per scraping task (<8> cities, 100+ rows each)
- Database dump: `listings_dump.sql`

Summary: I collected business listings from OpenStreetMap's Overpass API (Google Maps and Justdial restrict automated scraping), cleaned and de-duplicated them, validated that every scraping task has at least 100 rows, stored them in MySQL through a FastAPI bulk-insert endpoint, and built a React dashboard showing city-, category- and source-wise counts. Setup steps are in the README.

Thank you for the opportunity.

Best regards,
<Divya Jaiswal>
<diyajaiswal9096@gmail.com>
