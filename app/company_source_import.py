from __future__ import annotations

import re
from urllib.parse import urlsplit

from app.address_parser import split_address
from app.core.url_utils import is_blocked_source_url, is_blocked_url, normalize_url_for_index
from app.database import SessionLocal
from app.models.company import Company
from app.sheet_contact_worker import _client, _spreadsheet_id


SOURCE_TABS = {"Canada": "Canada", "Trung đông": "Trung Đông", "USA": "Hoa Kỳ"}


def _root_url(value: str) -> str:
    value = str(value or "").strip()
    return "" if not value or value.startswith("/") else normalize_url_for_index(value)


def _read_tab(service, spreadsheet_id: str, tab: str, max_rows: int) -> list[list[str]]:
    header = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=f"'{tab}'!A1:AA1", majorDimension="ROWS"
    ).execute().get("values", [[]])[0]
    rows = [header]
    for start in range(2, max_rows + 1, 1000):
        end = min(start + 999, max_rows)
        values = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=f"'{tab}'!A{start}:AA{end}", majorDimension="ROWS"
        ).execute().get("values", [])
        rows.extend(values)
    return rows


def _record(tab: str, headers: list[str], row: list[str], default_country: str, source_url: str) -> dict[str, str] | None:
    values = {headers[index]: str(row[index]).strip() if index < len(row) else "" for index in range(len(headers))}
    if tab == "Canada":
        name, website, email = values.get("name", ""), values.get("website", ""), values.get("email", "")
        address, phone = values.get("address", ""), values.get("phone", "")
        industry, facebook = values.get("type", ""), values.get("facebook", "")
        description = ""
    elif tab == "USA":
        name, website, email = values.get("name", ""), values.get("website", ""), values.get("email", "")
        address, phone = values.get("address", ""), values.get("phone", "")
        industry, facebook, description = values.get("nguồn", ""), values.get("facebook", ""), ""
    else:
        name, website, email = values.get("tên doanh nghiệp", ""), values.get("website", ""), values.get("email", "")
        address, phone = values.get("địa chỉ", ""), values.get("điện thoại", "")
        industry, facebook = "", ""
        description = values.get("nhóm mặt hàng nhập khẩu chính & ghi chú", "")
    website = _root_url(website)
    if is_blocked_url(website) or is_blocked_source_url(source_url) or (not name and not website):
        return None
    city, state = split_address(address, default_country)
    return {
        "name": name or website[:255], "website": website, "address": address, "email": email,
        "phone": phone, "industry": industry, "facebook": facebook, "short_description": description,
        "industry_raw": industry,
        "country": default_country, "city": city, "state": state, "source_url": source_url,
    }


def import_company_source(spreadsheet_url: str) -> dict[str, int]:
    service = _client()
    spreadsheet_id = _spreadsheet_id(spreadsheet_url)
    metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id, fields="sheets.properties").execute()
    tabs = {item["properties"]["title"]: item["properties"]["gridProperties"].get("rowCount", 0) for item in metadata["sheets"]}
    missing = [tab for tab in SOURCE_TABS if tab not in tabs]
    if missing:
        raise RuntimeError(f"Không tìm thấy tab: {', '.join(missing)}")

    records: list[dict[str, str]] = []
    for tab, country in SOURCE_TABS.items():
        values = _read_tab(service, spreadsheet_id, tab, tabs[tab])
        if not values:
            continue
        headers = [str(value).strip().casefold() for value in values[0]]
        for row in values[1:]:
            record = _record(tab, headers, row, country, spreadsheet_url)
            if record:
                records.append(record)

    db = SessionLocal()
    inserted = updated = duplicates = 0
    try:
        # Load existing keys once. Querying the database per source row becomes
        # prohibitively slow when importing several thousand records.
        existing_rows = db.query(Company).all()
        by_website = {_root_url(item.website).casefold(): item for item in existing_rows if _root_url(item.website)}
        by_name_address = {
            (item.name.strip().casefold(), item.address.strip().casefold()): item
            for item in existing_rows
            if item.name.strip()
        }
        for row in records:
            website_key = row["website"].casefold()
            name_address_key = (row["name"].casefold(), row["address"].casefold())
            existing = by_website.get(website_key) if website_key else None
            existing = existing or by_name_address.get(name_address_key)
            if not existing:
                existing = Company(**row)
                db.add(existing)
                if website_key:
                    by_website[website_key] = existing
                by_name_address[name_address_key] = existing
                inserted += 1
                continue
            changed = False
            for field, value in row.items():
                if field in {"name", "website", "address", "source_url"} or not value:
                    continue
                if not getattr(existing, field, ""):
                    setattr(existing, field, value)
                    changed = True
            if changed:
                updated += 1
            else:
                duplicates += 1
        db.commit()
        return {"rows_read": len(records), "inserted": inserted, "updated": updated, "duplicates_kept": duplicates}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
