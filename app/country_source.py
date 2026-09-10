from __future__ import annotations

import re
from pathlib import Path

from app.database import SessionLocal
from app.models.country_source import CountrySource
from app.models.country_keyword import CountryKeyword
from app.sheet_contact_worker import _client


def _normalise_query(value: str) -> str:
    value = re.sub(r"\([^)]*\)", "", value.lower())
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def _query_location(source: CountrySource) -> str:
    raw_city = source.city.strip().casefold()
    city = _normalise_query(source.city)
    state = _normalise_query(source.state)
    raw_country = source.country.strip().casefold()
    country = _normalise_query(source.country)
    # Các dòng cấp bang có Thành phố là "Toàn bang" / "Toàn quốc".
    # Một số nước dùng cột Bang để lặp lại tên quốc gia, ví dụ Malaysia (MY).
    # Không ghép phần này hai lần vào query.
    state_part = "" if state == country else state
    place = state_part if raw_city.startswith(("toàn ", "toan ")) else f"{city} {state_part}".strip()
    # File query hiện dùng USA thay cho tên tiếng Việt "Hoa Kỳ".
    country = "usa" if raw_country in {"hoa kỳ", "hoa ky", "united states", "usa"} else country
    return f"{place} {country}".strip()


def sync_completed_queries(completed_file: Path | None = None) -> dict:
    """Mark V for country-source keyword groups found in completed_queries.txt."""
    completed_file = completed_file or Path(__file__).resolve().parents[1] / "craw_country" / "completed_queries.txt"
    if not completed_file.is_file():
        raise FileNotFoundError(f"Không tìm thấy {completed_file.name}.")

    completed = {
        _normalise_query(line)
        for line in completed_file.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    }
    db = SessionLocal()
    try:
        keywords = db.query(CountryKeyword).filter(CountryKeyword.position.between(1, 16)).all()
        sources = db.query(CountrySource).all()
        lookup = {
            (_normalise_query(keyword.keyword), keyword.group_position): keyword
            for keyword in keywords
            if keyword.keyword.strip()
        }
        marked = 0
        for source in sources:
            location = _query_location(source)
            for (_, group_position), keyword in lookup.items():
                expected = f"{_normalise_query(keyword.keyword)} {location}".strip()
                if expected in completed and getattr(source, f"keyword_{group_position}") != "V":
                    setattr(source, f"keyword_{group_position}", "V")
                    marked += 1
        db.commit()
        return {"completed_queries": len(completed), "sources": len(sources), "cells_updated": marked}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _spreadsheet_id(value: str) -> str:
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", value)
    if not match:
        raise ValueError("Google Sheet URL không hợp lệ.")
    return match.group(1)


def sync_country_sheet(spreadsheet_url: str, sheet_name: str = "Quốc gia") -> dict:
    service = _client()
    values = service.spreadsheets().values().get(
        spreadsheetId=_spreadsheet_id(spreadsheet_url), range=f"'{sheet_name}'!A:U", majorDimension="ROWS"
    ).execute().get("values", [])
    if not values:
        raise RuntimeError("Tab Quốc gia không có dữ liệu.")

    rows = []
    keyword_headers = [str(value).strip() for value in (list(values[0]) + [""] * 21)[5:21]]
    for source in values[1:]:
        padded = list(source) + [""] * max(0, 21 - len(source))
        record = {
            "place_name": str(padded[0]).strip(), "country": str(padded[1]).strip(),
            "state": str(padded[2]).strip(), "city": str(padded[3]).strip(), "region": str(padded[4]).strip(),
        }
        record.update({f"keyword_{i}": str(padded[i + 4]).strip() for i in range(1, 17)})
        if any(record.values()):
            rows.append(record)

    db = SessionLocal()
    try:
        custom_keywords = [
            {"position": item.position, "group_position": item.group_position, "keyword": item.keyword, "active": item.active}
            for item in db.query(CountryKeyword).filter(CountryKeyword.position > 16).all()
        ]
        deleted = db.query(CountrySource).delete(synchronize_session=False)
        db.query(CountryKeyword).delete(synchronize_session=False)
        db.bulk_insert_mappings(CountryKeyword, [
            {"position": i + 1, "group_position": i + 1, "keyword": value, "active": 1}
            for i, value in enumerate(keyword_headers)
        ] + custom_keywords)
        db.bulk_insert_mappings(CountrySource, rows)
        db.commit()
        return {"rows_read": len(values) - 1, "inserted": len(rows), "keywords": len(keyword_headers), "deleted": deleted}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
