"""Import a Google Maps Scraper CSV into the local companies SQLite database."""
from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
from pathlib import Path
from urllib.parse import urlsplit


SKIP_HOSTS = ("facebook.com", "instagram.com", "linkedin.com", "yelp.com", "yellowpages.com")


def root_url(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if not re.match(r"^https?://", value, re.I):
        value = "https://" + value
    host = (urlsplit(value).hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return f"https://{host}/" if host else ""


def country_from_row(row: dict[str, str]) -> str:
    value = (row.get("country") or "").strip()
    try:
        value = str(json.loads(row.get("complete_address") or "{}").get("country") or value).strip()
    except (json.JSONDecodeError, TypeError):
        pass
    return {"US": "Hoa Kỳ", "USA": "Hoa Kỳ", "United States": "Hoa Kỳ", "CA": "Canada"}.get(value, value)


def candidates(csv_file: Path):
    with csv_file.open(encoding="utf-8-sig", newline="", errors="replace") as handle:
        for raw in csv.DictReader(handle):
            website = root_url(raw.get("website", ""))
            if not website or any(host in website for host in SKIP_HOSTS):
                continue
            yield {
                "name": (raw.get("title") or "").strip(),
                "address": (raw.get("address") or "").strip(),
                "website": website,
                "email": (raw.get("emails") or raw.get("email") or "").strip(),
                "phone": (raw.get("phone") or "").strip(),
                "industry": (raw.get("category") or "").strip(),
                "country": country_from_row(raw),
            }


def import_file(csv_file: Path, database: Path, query: str) -> dict[str, int]:
    if not database.is_file():
        raise FileNotFoundError(f"Không tìm thấy database: {database}")
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    inserted = updated = skipped = 0
    try:
        by_website: dict[str, int] = {}
        by_name_address: dict[tuple[str, str], int] = {}
        for existing_row in connection.execute("SELECT id, name, address, website FROM companies ORDER BY id"):
            website_key = root_url(existing_row["website"])
            if website_key and website_key not in by_website:
                by_website[website_key] = existing_row["id"]
            identity = ((existing_row["name"] or "").strip().casefold(), (existing_row["address"] or "").strip().casefold())
            if all(identity) and identity not in by_name_address:
                by_name_address[identity] = existing_row["id"]
        for row in candidates(csv_file):
            if not row["name"]:
                skipped += 1
                continue
            identity = (row["name"].casefold(), row["address"].casefold())
            existing_id = by_website.get(row["website"]) or by_name_address.get(identity)
            if existing_id:
                connection.execute(
                    """UPDATE companies SET
                        email = CASE WHEN email = '' THEN ? ELSE email END,
                        phone = CASE WHEN phone = '' THEN ? ELSE phone END,
                        industry = CASE WHEN industry = '' THEN ? ELSE industry END,
                        country = CASE WHEN country = '' THEN ? ELSE country END,
                        source_url = CASE WHEN source_url = '' THEN ? ELSE source_url END
                    WHERE id = ?""",
                    (row["email"], row["phone"], row["industry"], row["country"], query, existing_id),
                )
                updated += 1
            else:
                connection.execute(
                    """INSERT INTO companies
                    (name, address, city, state, website, email, phone, short_description,
                     facebook, youtube, x, linkedin, truth, country, industry, source_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (row["name"], row["address"], "", "", row["website"], row["email"], row["phone"], "",
                     "", "", "", "", "", row["country"], row["industry"], query),
                )
                new_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
                by_website[row["website"]] = new_id
                if all(identity):
                    by_name_address[identity] = new_id
                inserted += 1
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return {"inserted": inserted, "updated": updated, "skipped": skipped}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--query", default="")
    args = parser.parse_args()
    print(json.dumps(import_file(Path(args.input), Path(args.database), args.query), ensure_ascii=False))


if __name__ == "__main__":
    main()
