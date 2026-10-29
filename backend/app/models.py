"""ORM model for the `listing_master` table."""
from datetime import datetime

from sqlalchemy import CHAR, DateTime, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Listing(Base):
    __tablename__ = "listing_master"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="Uncategorized")
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    # sha256(name|city|address|source). A UNIQUE index on this column lets MySQL
    # silently skip duplicates (INSERT IGNORE) so re-running the scraper is safe.
    dedupe_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_listing_city", "city"),
        Index("ix_listing_category", "category"),
        Index("ix_listing_source", "source"),
    )
