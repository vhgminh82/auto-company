import re
from urllib.parse import urlparse

from app.core.url_utils import normalize_url_for_index

LEGAL_SUFFIXES = [
    " co ltd", " ltd", " llc", " inc", " corp", " corporation", " company", " jsc", " plc",
]


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def normalize_domain(url: str) -> str:
    normalized = normalize_url_for_index(url)
    return urlparse(normalized).hostname or ""


def normalize_company_name(name: str) -> str:
    base = normalize_text(name).lower()
    for suffix in LEGAL_SUFFIXES:
        if base.endswith(suffix):
            base = base[: -len(suffix)]
            break
    return normalize_text(base)


def normalize_phone(phone: str) -> str:
    raw = phone or ""
    plus = raw.strip().startswith("+")
    digits = "".join(ch for ch in raw if ch.isdigit())
    if not digits:
        return ""
    return f"+{digits}" if plus else digits


def normalize_record(record: dict[str, str]) -> dict[str, str]:
    normalized = dict(record)
    normalized["name"] = normalize_text(record.get("name", ""))
    normalized["address"] = normalize_text(record.get("address", ""))
    normalized["city"] = normalize_text(record.get("city", ""))
    normalized["state"] = normalize_text(record.get("state", ""))
    normalized["country"] = normalize_text(record.get("country", ""))
    normalized["region"] = normalize_text(record.get("region", ""))
    normalized["industry"] = normalize_text(record.get("industry", ""))
    normalized["website"] = normalize_url_for_index(record.get("website", ""))
    normalized["email"] = normalize_text(record.get("email", "")).lower()
    normalized["phone"] = normalize_phone(record.get("phone", ""))
    normalized["_name_norm"] = normalize_company_name(record.get("name", ""))
    normalized["_domain_norm"] = normalize_domain(record.get("website", ""))
    return normalized
