from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/api/listings", tags=["Listings"])


@router.post(
    "/bulk",
    response_model=schemas.BulkInsertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk insert scraped listings",
)
def insert_listings(payload: schemas.BulkInsertRequest, db: Session = Depends(get_db)):
    """Insert up to 1000 listings per call. Duplicates are skipped, not errored,
    so the scraper can be re-run safely (idempotent)."""
    return crud.bulk_insert(db, payload.listings)


@router.get("", response_model=schemas.ListingPage, summary="Browse listings (paginated)")
def get_listings(
    db: Session = Depends(get_db),
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    q: str | None = None,
    city: str | None = None,
    category: str | None = None,
    source: str | None = None,
):
    return crud.list_listings(db, crud.Filters(city, category, source, q), page, page_size)
