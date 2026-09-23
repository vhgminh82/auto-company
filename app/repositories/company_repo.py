from typing import Any

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.constants import COMPANY_EXPORT_COLUMNS
from app.core.url_utils import is_blocked_source_url, is_blocked_url, normalize_url_for_index
from app.models.company import Company
from app.industry_normalizer import main_industry


def _to_company_payload(record: dict[str, Any]) -> dict[str, str]:
    return {
        "name": str(record.get("name", ""))[:255],
        "address": str(record.get("address", ""))[:512],
        "city": str(record.get("city", ""))[:128],
        "state": str(record.get("state", ""))[:128],
        "website": normalize_url_for_index(str(record.get("website", "")))[:512],
        "contact": str(record.get("contact", ""))[:64],
        "email": str(record.get("email", ""))[:255],
        "email_2": str(record.get("email_2", ""))[:255],
        "phone": str(record.get("phone", ""))[:64],
        "short_description": str(record.get("short_description", ""))[:1000],
        "facebook": str(record.get("facebook", ""))[:512],
        "facebook_alt": str(record.get("facebook_alt", ""))[:512],
        "youtube": str(record.get("youtube", ""))[:512],
        "x": str(record.get("x", ""))[:512],
        "linkedin": str(record.get("linkedin", ""))[:512],
        "truth": str(record.get("truth", ""))[:512],
        "country": str(record.get("country", ""))[:128],
        "industry": main_industry(record.get("industry", ""))[:128] if str(record.get("industry", "")).strip() else "",
        "source_url": str(record.get("source_url", ""))[:512],
    }


def insert_many_ignore_duplicates(db: Session, records: list[dict[str, Any]]) -> int:
    inserted = 0
    for record in records:
        if is_blocked_url(record.get("website", "")) or is_blocked_source_url(record.get("source_url", "")):
            continue
        company = Company(**_to_company_payload(record))
        db.add(company)
        try:
            db.commit()
            inserted += 1
        except IntegrityError:
            db.rollback()
    return inserted


def search_companies(db: Session, q: str, country: str, industry: str, limit: int) -> list[Company]:
    query = db.query(Company)

    if q:
        like_q = f"%{q}%"
        query = query.filter(
            or_(
                Company.name.ilike(like_q),
                Company.short_description.ilike(like_q),
                Company.website.ilike(like_q),
                Company.address.ilike(like_q),
                Company.city.ilike(like_q),
                Company.state.ilike(like_q),
                Company.country.ilike(like_q),
                Company.industry.ilike(like_q),
                Company.contact.ilike(like_q),
                Company.email.ilike(like_q),
                Company.email_2.ilike(like_q),
                Company.phone.ilike(like_q),
                Company.facebook.ilike(like_q),
                Company.facebook_alt.ilike(like_q),
                Company.youtube.ilike(like_q),
                Company.x.ilike(like_q),
                Company.linkedin.ilike(like_q),
                Company.truth.ilike(like_q),
            )
        )
    if country:
        query = query.filter(Company.country.ilike(f"%{country}%"))
    if industry:
        query = query.filter(Company.industry.ilike(f"%{industry}%"))

    return query.order_by(Company.id.desc()).limit(limit).all()


def list_for_export(db: Session) -> list[dict[str, str]]:
    rows = db.query(Company).order_by(Company.id.desc()).all()
    return [{col: getattr(row, col, "") for col in COMPANY_EXPORT_COLUMNS} for row in rows]
