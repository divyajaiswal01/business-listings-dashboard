"""Normalisation + de-duplication shared by every source.

Each source returns raw dicts; this module turns them into the exact shape the API expects.
"""
import re

FIELDS = ("business_name", "category", "city", "address", "phone", "source")


def clean_text(value) -> str | None:
    if value is None:
        return None
    value = " ".join(str(value).split())
    return value or None


def clean_phone(value) -> str | None:
    """Keep the first number, strip everything except digits and a leading '+'.
    OSM often stores several numbers separated by ';' or ','."""
    value = clean_text(value)
    if not value:
        return None
    first = re.split(r"[;,/]", value)[0]
    digits = re.sub(r"\D", "", first)
    if not 8 <= len(digits) <= 15:  # reject obviously invalid numbers
        return None
    return ("+" if first.strip().startswith("+") else "") + digits


def normalise(raw: dict) -> dict | None:
    """Return a clean record or None if it is unusable (no name/city)."""
    rec = {
        "business_name": clean_text(raw.get("business_name")),
        "category": clean_text(raw.get("category")) or "Uncategorized",
        "city": clean_text(raw.get("city")),
        "address": clean_text(raw.get("address")),
        "phone": clean_phone(raw.get("phone")),
        "source": clean_text(raw.get("source")),
    }
    if not rec["business_name"] or not rec["city"] or not rec["source"]:
        return None
    return rec


def dedupe(records: list[dict]) -> list[dict]:
    seen, out = set(), []
    for r in records:
        key = (r["business_name"].lower(), r["city"].lower(), (r["address"] or "").lower(), r["source"].lower())
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out
