from __future__ import annotations

from app.database import SessionLocal
from app.address_parser import split_address
from app.core.url_utils import is_blocked_url, normalize_url_for_index
from app.models.company import Company
from app.models.crawl_visited import CrawlVisited
from app.sheet_contact_worker import _client, _spreadsheet_id


def sync_company_sheet(spreadsheet_url: str, sheet_name: str = "company") -> dict:
    service = _client()
    sid = _spreadsheet_id(spreadsheet_url)
    values = service.spreadsheets().values().get(
        spreadsheetId=sid, range=f"'{sheet_name}'!A:K", majorDimension="ROWS"
    ).execute().get("values", [])
    if not values:
        raise RuntimeError("Sheet không có dữ liệu.")
    headers = [str(value).strip().lower() for value in values[0]]
    required = {"tên", "website"}
    if not required.issubset(headers):
        raise RuntimeError(f"Thiếu cột bắt buộc: {', '.join(sorted(required - set(headers)))}")

    def get(row, header, default=""):
        try:
            index = headers.index(header)
        except ValueError:
            return default
        return str(row[index]).strip() if index < len(row) else default

    records = []
    seen = set()
    for row in values[1:]:
        name, website = get(row, "tên"), get(row, "website")
        if not name and not website:
            continue
        key = (name, website)
        if key in seen:
            continue
        seen.add(key)
        website = normalize_url_for_index(website)
        if is_blocked_url(website):
            continue
        address = get(row, "địa chỉ")
        city, state = split_address(address, get(row, "quốc gia"))
        records.append({
            "name": name or website[:255], "address": address, "city": city, "state": state,
            "website": website, "contact": get(row, "contact"), "email": get(row, "email"),
            "phone": get(row, "phone"), "short_description": "", "facebook": get(row, "facebook"),
            "facebook_alt": get(row, "facebook", ""), "youtube": "", "x": "", "linkedin": get(row, "linkedin"),
            "truth": "", "country": get(row, "quốc gia"), "region": "", "industry": get(row, "lĩnh vực"),
            "source_url": website,
        })

    db = SessionLocal()
    try:
        deleted_companies = db.query(Company).delete(synchronize_session=False)
        deleted_visited = db.query(CrawlVisited).delete(synchronize_session=False)
        if records:
            db.bulk_insert_mappings(Company, records)
        db.commit()
        return {"rows_read": len(values) - 1, "inserted": len(records), "deleted_companies": deleted_companies, "deleted_visited": deleted_visited}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
