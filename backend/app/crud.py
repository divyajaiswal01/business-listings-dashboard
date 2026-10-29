"""All database logic lives here so routers stay thin and easy to read."""
import hashlib
from dataclasses import dataclass

from sqlalchemy import func, or_, select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.orm import Session

from .models import Listing
from .schemas import ListingIn


# ---------------------------------------------------------------- filters
@dataclass
class Filters:
    """Optional filters shared by the dashboard endpoints and the listings table."""
    city: str | None = None
    category: str | None = None
    source: str | None = None
    q: str | None = None  # free-text search on name / address


def apply_filters(stmt, f: Filters):
    if f.city:
        stmt = stmt.where(Listing.city == f.city)
    if f.category:
        stmt = stmt.where(Listing.category == f.category)
    if f.source:
        stmt = stmt.where(Listing.source == f.source)
    if f.q:
        like = f"%{f.q}%"
        stmt = stmt.where(or_(Listing.business_name.like(like), Listing.address.like(like)))
    return stmt


# ---------------------------------------------------------------- insert
def make_hash(item: ListingIn) -> str:
    """Identity of a listing = same name + city + address + source (case-insensitive)."""
    key = "|".join(
        (x or "").strip().lower() for x in (item.business_name, item.city, item.address, item.source)
    )
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def bulk_insert(db: Session, items: list[ListingIn]) -> dict:
    """Insert many rows in ONE statement, skipping duplicates.

    1. Build row dicts and de-duplicate inside the payload (by hash).
    2. `INSERT IGNORE` lets MySQL skip rows that violate the UNIQUE(dedupe_hash)
       index, so rows already in the DB do not raise an error.
    3. rowcount = rows actually inserted -> duplicates = received - inserted.
    """
    rows: dict[str, dict] = {}
    for item in items:
        h = make_hash(item)
        rows.setdefault(h, {**item.model_dump(), "dedupe_hash": h})

    inserted = 0
    if rows:
        # Use the connection (Core) so we get a CursorResult that exposes .rowcount.
        result = db.connection().execute(
            mysql_insert(Listing).prefix_with("IGNORE"), list(rows.values())
        )
        inserted = result.rowcount
        db.commit()
    return {"received": len(items), "inserted": inserted, "duplicates_skipped": len(items) - inserted}


# ---------------------------------------------------------------- reads
# Whitelist: the API never builds SQL from user-supplied column names.
GROUP_COLUMNS = {"city": Listing.city, "category": Listing.category, "source": Listing.source}


def count_by(db: Session, column_key: str, f: Filters, limit: int | None) -> dict:
    col = GROUP_COLUMNS[column_key]
    n = func.count(Listing.id).label("n")

    stmt = apply_filters(select(col, n), f).group_by(col).order_by(n.desc(), col.asc())
    if limit:
        stmt = stmt.limit(limit)
    data = [{"label": label, "count": count} for label, count in db.execute(stmt)]

    total_groups = db.scalar(
        apply_filters(select(func.count(func.distinct(col))), f)
    ) or 0
    return {"data": data, "total_groups": total_groups}


def summary(db: Session, f: Filters) -> dict:
    stmt = apply_filters(
        select(
            func.count(Listing.id),
            func.count(func.distinct(Listing.city)),
            func.count(func.distinct(Listing.category)),
            func.count(func.distinct(Listing.source)),
            func.count(Listing.phone),  # COUNT(col) ignores NULLs -> listings with a phone
            func.max(Listing.created_at),
        ),
        f,
    )
    total, cities, cats, sources, with_phone, last = db.execute(stmt).one()
    return {
        "total_listings": total, "cities": cities, "categories": cats,
        "sources": sources, "with_phone": with_phone, "last_updated": last,
    }


def list_listings(db: Session, f: Filters, page: int, page_size: int) -> dict:
    base = apply_filters(select(Listing), f)
    total = db.scalar(apply_filters(select(func.count(Listing.id)), f)) or 0
    items = db.scalars(
        base.order_by(Listing.id.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def insights(db: Session, f: Filters, top_cities: int = 8, top_cats: int = 6, chain_limit: int = 8) -> dict:
    """Extra aggregates that power the dashboard's storyline (all respect the same filters)."""
    n = func.count(Listing.id)

    # 1) which cities / categories are the "headline" ones
    city_rows = db.execute(
        apply_filters(select(Listing.city, n), f).group_by(Listing.city).order_by(n.desc(), Listing.city).limit(top_cities)
    ).all()
    categories = [c for c, _ in db.execute(
        apply_filters(select(Listing.category, n), f).group_by(Listing.category).order_by(n.desc(), Listing.category).limit(top_cats)
    ).all()]

    # 2) city x category matrix (one query), plus an "other" bucket so each row sums to the city total
    matrix: dict[str, dict[str, int]] = {}
    cities = [c for c, _ in city_rows]
    if cities and categories:
        stmt = apply_filters(select(Listing.city, Listing.category, n), f).where(
            Listing.city.in_(cities), Listing.category.in_(categories)
        ).group_by(Listing.city, Listing.category)
        for city, cat, cnt in db.execute(stmt):
            matrix.setdefault(city, {})[cat] = cnt
    rows = []
    for city, total in city_rows:
        counts = {c: matrix.get(city, {}).get(c, 0) for c in categories}
        rows.append({"city": city, "total": total, "counts": counts, "other": total - sum(counts.values())})

    # 3) data completeness per city (COUNT(col) ignores NULLs)
    comp = db.execute(
        apply_filters(select(Listing.city, n, func.count(Listing.address), func.count(Listing.phone)), f)
        .group_by(Listing.city).order_by(n.desc(), Listing.city)
    ).all()
    completeness = [
        {"city": c, "total": t, "address_pct": round(100 * a / t, 1), "phone_pct": round(100 * p / t, 1)}
        for c, t, a, p in comp
    ]

    # 4) business names that occur more than once (chains / multi-branch networks)
    repeated = db.execute(
        apply_filters(select(Listing.business_name, n, func.count(func.distinct(Listing.city))), f)
        .group_by(Listing.business_name).having(n > 1)
        .order_by(n.desc(), Listing.business_name).limit(chain_limit)
    ).all()

    return {
        "category_mix": {"categories": categories, "rows": rows},
        "completeness": completeness,
        "repeated_names": [{"name": name, "count": c, "cities": k} for name, c, k in repeated],
    }
