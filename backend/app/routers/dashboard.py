from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


def filters(city: str | None = None, category: str | None = None, source: str | None = None) -> crud.Filters:
    """Optional cross-filters, e.g. /cities?source=OpenStreetMap lets the UI drill down."""
    return crud.Filters(city=city, category=category, source=source)


Limit = Annotated[int | None, Query(ge=1, le=200, description="Top-N groups. Omit for all.")]


@router.get("/summary", response_model=schemas.SummaryResponse, summary="Headline numbers")
def get_summary(db: Session = Depends(get_db), f: crud.Filters = Depends(filters)):
    return crud.summary(db, f)


@router.get("/cities", response_model=schemas.CountResponse, summary="City-wise count")
def city_counts(db: Session = Depends(get_db), f: crud.Filters = Depends(filters), limit: Limit = None):
    return crud.count_by(db, "city", f, limit)


@router.get("/categories", response_model=schemas.CountResponse, summary="Category-wise count")
def category_counts(db: Session = Depends(get_db), f: crud.Filters = Depends(filters), limit: Limit = None):
    return crud.count_by(db, "category", f, limit)


@router.get("/sources", response_model=schemas.CountResponse, summary="Source-wise count")
def source_counts(db: Session = Depends(get_db), f: crud.Filters = Depends(filters), limit: Limit = None):
    return crud.count_by(db, "source", f, limit)


@router.get("/insights", response_model=schemas.InsightsResponse, summary="Category mix, data quality, repeated names")
def get_insights(db: Session = Depends(get_db), f: crud.Filters = Depends(filters)):
    """Aggregates behind the dashboard story: what each city is made of, how complete
    the data is, and which business names repeat (chains)."""
    return crud.insights(db, f)
