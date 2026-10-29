"""FastAPI entrypoint.  Run:  uvicorn app.main:app --reload"""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import settings
from .database import Base, engine, get_db
from .routers import dashboard, listings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Creates the table if it does not exist (no-op when database/schema.sql was already run).
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Business Listings API",
    description="Stores scraped business listings in MySQL and serves aggregated reports.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(listings.router)
app.include_router(dashboard.router)


@app.get("/health", tags=["Meta"])
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))  # fails with 500 if MySQL is unreachable
    return {"status": "ok"}
