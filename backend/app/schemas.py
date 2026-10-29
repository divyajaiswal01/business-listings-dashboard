"""Pydantic schemas = the API contract (validation + OpenAPI docs)."""
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

MAX_BULK = 1000  # protects the API from huge payloads; the scraper batches below this


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = " ".join(value.split())  # collapse whitespace/newlines
    return value or None


class ListingIn(BaseModel):
    business_name: str = Field(min_length=1, max_length=255)
    category: str = Field(default="Uncategorized", max_length=100)
    city: str = Field(min_length=1, max_length=100)
    address: str | None = None
    phone: str | None = Field(default=None, max_length=50)
    source: str = Field(min_length=1, max_length=50)

    @field_validator("business_name", "category", "city", "address", "phone", "source", mode="before")
    @classmethod
    def strip_text(cls, v):
        return _clean(v) if isinstance(v, str) or v is None else v


class BulkInsertRequest(BaseModel):
    listings: list[ListingIn] = Field(min_length=1, max_length=MAX_BULK)


class BulkInsertResponse(BaseModel):
    received: int
    inserted: int
    duplicates_skipped: int


class ListingOut(ListingIn):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ListingPage(BaseModel):
    items: list[ListingOut]
    total: int
    page: int
    page_size: int


class CountItem(BaseModel):
    label: str
    count: int


class CountResponse(BaseModel):
    data: list[CountItem]
    total_groups: int  # how many distinct groups exist (data may be truncated by `limit`)


class SummaryResponse(BaseModel):
    total_listings: int
    cities: int
    categories: int
    sources: int
    with_phone: int
    last_updated: datetime | None


# ---------------------------------------------------------------- insights
class CityCategoryRow(BaseModel):
    city: str
    total: int
    counts: dict[str, int]  # count per top category
    other: int              # everything outside the top categories


class CityCategoryMix(BaseModel):
    categories: list[str]
    rows: list[CityCategoryRow]


class CompletenessRow(BaseModel):
    city: str
    total: int
    address_pct: float
    phone_pct: float


class ChainRow(BaseModel):
    name: str
    count: int
    cities: int


class InsightsResponse(BaseModel):
    category_mix: CityCategoryMix
    completeness: list[CompletenessRow]
    repeated_names: list[ChainRow]
