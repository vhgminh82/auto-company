from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import insert, literal, or_, select, text
from sqlalchemy.orm import Session

from app.database import get_db
from app.emkt_service import valid_email
from app.models.company import Company
from app.models.emkt import EmktList, EmktListMember

router = APIRouter(prefix="/api/emkt/lists", tags=["emkt-lists"])


class ListRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    country_filter: str = Field(default="", max_length=10000)
    industry_filter: str = Field(default="", max_length=10000)
    query_filter: str = Field(default="", max_length=255)
    blacklist: bool = False
    manual_emails: str = Field(default="", max_length=10000)
    blacklist_emails: str = Field(default="", max_length=10000)


class MemberEmailRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)


def _company_query(db: Session, item: EmktList):
    query = db.query(Company).filter(Company.website != "")
    if item.country_filter:
        countries = [value.strip() for value in item.country_filter.split(",") if value.strip()]
        query = query.filter(or_(*[Company.country.ilike(f"%{value}%") for value in countries]))
    if item.industry_filter:
        industries = [value.strip() for value in item.industry_filter.split(",") if value.strip()]
        query = query.filter(or_(*[Company.industry.ilike(f"%{value}%") for value in industries]))
    if item.query_filter:
        term = f"%{item.query_filter}%"
        query = query.filter(or_(Company.name.ilike(term), Company.website.ilike(term), Company.short_description.ilike(term)))
    return query.order_by(Company.id)


def _has_email(company: Company) -> bool:
    return valid_email(company.email) or valid_email(company.email_2)


def _has_list_selection(item) -> bool:
    return bool((item.country_filter or '').strip() or (item.industry_filter or '').strip() or (item.query_filter or '').strip())


def _manual_emails(value: str) -> set[str]:
    return {email.strip().lower() for email in re.split(r"[,;\s]+", value or "") if valid_email(email.strip())}


def _manual_company_query(db: Session, emails: set[str]):
    if not emails:
        return []
    return db.query(Company).filter(
        Company.website != "",
        or_(Company.email.in_(emails), Company.email_2.in_(emails)),
    ).all()


def _manual_only_count(db: Session, item: EmktList) -> int:
    manual = _manual_emails(item.manual_emails)
    if not manual:
        return 0
    member_ids = [row.company_id for row in db.query(EmktListMember).filter(EmktListMember.list_id == item.id).all()]
    matched = set()
    if member_ids:
        for company in db.query(Company).filter(Company.id.in_(member_ids)).all():
            matched.update(value.strip().lower() for value in (company.email, company.email_2) if valid_email(value))
    return len(manual - matched)


@router.get("/preview")
def preview_list(country_filter: str = "", industry_filter: str = "", query_filter: str = "", manual_emails: str = "", db: Session = Depends(get_db)):
    class PreviewList:
        pass
    item = PreviewList()
    item.country_filter = country_filter.strip(); item.industry_filter = industry_filter.strip(); item.query_filter = query_filter.strip()
    ids = set()
    if _has_list_selection(item):
        ids = {company.id for company in _company_query(db, item).yield_per(1000) if _has_email(company)}
    manual = _manual_emails(manual_emails)
    matched_manual = set()
    if manual:
        for company in _manual_company_query(db, manual):
            company_emails = {str(company.email or '').strip().lower(), str(company.email_2 or '').strip().lower()}
            if company_emails & manual:
                ids.add(company.id)
                matched_manual.update(company_emails & manual)
    return {"valid_email_customers": len(ids) + len(manual - matched_manual)}


@router.get("/facet-counts")
def facet_counts(db: Session = Depends(get_db)):
    countries, industries = {}, {}
    for company in db.query(Company).filter(Company.website != "").yield_per(1000):
        if not _has_email(company):
            continue
        country = (company.country or "").strip()
        industry = (company.industry or "").strip()
        if country:
            countries[country] = countries.get(country, 0) + 1
        if industry:
            industries[industry] = industries.get(industry, 0) + 1
    return {"countries": countries, "industries": industries}


def _sync_company_list_column(db: Session, company_id: int) -> None:
    company = db.get(Company, company_id)
    if not company:
        return
    names = (
        db.query(EmktList.name)
        .join(EmktListMember, EmktListMember.list_id == EmktList.id)
        .filter(EmktListMember.company_id == company_id)
        .order_by(EmktList.name)
        .all()
    )
    company.list = ", ".join(row[0] for row in names)


def _sync_company_list_columns(db: Session, company_ids: set[int]) -> None:
    if not company_ids:
        return
    placeholders = ", ".join(f":company_{index}" for index in range(len(company_ids)))
    params = {f"company_{index}": company_id for index, company_id in enumerate(company_ids)}
    db.execute(text(f"""
        UPDATE companies
        SET list = COALESCE((
            SELECT group_concat(emkt_lists.name, ', ')
            FROM emkt_list_members
            JOIN emkt_lists ON emkt_lists.id = emkt_list_members.list_id
            WHERE emkt_list_members.company_id = companies.id
        ), '')
        WHERE companies.id IN ({placeholders})
    """), params)


def _refresh_members(db: Session, item: EmktList) -> int:
    db.query(EmktListMember).filter(EmktListMember.list_id == item.id).delete(synchronize_session=False)
    if _has_list_selection(item):
        email_condition = or_(
            (Company.email.ilike('%@%') & Company.email.ilike('%.%')),
            (Company.email_2.ilike('%@%') & Company.email_2.ilike('%.%')),
        )
        company_select = _company_query(db, item).order_by(None).filter(email_condition).with_entities(Company.id).subquery()
        db.execute(insert(EmktListMember).from_select(
            ["list_id", "company_id", "custom_email"],
            select(literal(item.id), company_select.c.id, literal("")),
        ))
    manual_emails = _manual_emails(item.manual_emails)
    matched_manual = set()
    for company in _manual_company_query(db, manual_emails):
        company_emails = {str(company.email or '').strip().lower(), str(company.email_2 or '').strip().lower()}
        if company_emails & manual_emails:
            matched_manual.update(company_emails & manual_emails)
            if not db.query(EmktListMember).filter(EmktListMember.list_id == item.id, EmktListMember.company_id == company.id).first():
                db.add(EmktListMember(list_id=item.id, company_id=company.id, custom_email=""))
    db.flush()
    member_count = db.query(EmktListMember).filter(EmktListMember.list_id == item.id).count()
    return member_count + len(manual_emails - matched_manual)


def _out(db: Session, item: EmktList) -> dict:
    members = db.query(EmktListMember).filter(EmktListMember.list_id == item.id).all()
    return {"id": item.id, "name": item.name, "country_filter": item.country_filter, "industry_filter": item.industry_filter, "query_filter": item.query_filter, "blacklist": bool(item.blacklist), "manual_emails": item.manual_emails, "blacklist_emails": item.blacklist_emails, "customer_count": len(members) + _manual_only_count(db, item), "created_at": item.created_at, "updated_at": item.updated_at}


@router.get("")
def list_lists(db: Session = Depends(get_db)):
    return [_out(db, item) for item in db.query(EmktList).order_by(EmktList.id.desc()).all()]


@router.post("")
def create_list(request: ListRequest, db: Session = Depends(get_db)):
    item = EmktList(name=request.name.strip(), country_filter=request.country_filter.strip(), industry_filter=request.industry_filter.strip(), query_filter=request.query_filter.strip(), blacklist=int(request.blacklist), manual_emails=request.manual_emails.strip(), blacklist_emails=request.blacklist_emails.strip())
    db.add(item)
    try:
        db.flush()
        count = _refresh_members(db, item)
        db.commit(); db.refresh(item)
    except Exception as exc:
        db.rollback()
        raise HTTPException(400, f"Không tạo được list: {exc}") from exc
    result = _out(db, item); result["customer_count"] = count
    return result


@router.put("/{list_id}")
def update_list(list_id: int, request: ListRequest, db: Session = Depends(get_db)):
    item = db.get(EmktList, list_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy list.")
    item.name = request.name.strip(); item.country_filter = request.country_filter.strip(); item.industry_filter = request.industry_filter.strip(); item.query_filter = request.query_filter.strip(); item.blacklist = int(request.blacklist); item.manual_emails = request.manual_emails.strip(); item.blacklist_emails = request.blacklist_emails.strip()
    try:
        count = _refresh_members(db, item)
        db.commit(); db.refresh(item)
    except Exception as exc:
        db.rollback(); raise HTTPException(400, f"Không cập nhật được list: {exc}") from exc
    result = _out(db, item); result["customer_count"] = count
    return result


@router.delete("/{list_id}")
def delete_list(list_id: int, db: Session = Depends(get_db)):
    item = db.get(EmktList, list_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy list.")
    company_ids = [row.company_id for row in db.query(EmktListMember).filter(EmktListMember.list_id == list_id).all()]
    db.query(EmktListMember).filter(EmktListMember.list_id == list_id).delete(synchronize_session=False)
    db.delete(item)
    _sync_company_list_columns(db, set(company_ids))
    db.commit()
    return {"deleted": list_id}


@router.get("/{list_id}/customers")
def list_customers(list_id: int, db: Session = Depends(get_db)):
    item = db.get(EmktList, list_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy list.")
    rows = db.query(EmktListMember, Company).join(Company, Company.id == EmktListMember.company_id).filter(EmktListMember.list_id == list_id).order_by(Company.name).all()
    result = [{"id": company.id, "name": company.name, "email": member.custom_email or company.email or company.email_2, "email_2": company.email_2, "website": company.website, "country": company.country, "industry": company.industry, "blacklisted": bool(member.blacklisted)} for member, company in rows]
    represented = {value.strip().lower() for row in result for value in (row.get("email"), row.get("email_2")) if valid_email(value)}
    blacklisted = _manual_emails(item.blacklist_emails)
    result.extend({"id": None, "name": "Email tự thêm", "email": email, "email_2": "", "website": "", "country": "", "industry": "", "manual": True, "blacklisted": email in blacklisted} for email in sorted(_manual_emails(item.manual_emails) - represented))
    return result


class BlacklistRequest(BaseModel):
    blacklisted: bool


@router.patch("/{list_id}/customers/{company_id}/blacklist")
def set_customer_blacklist(list_id: int, company_id: int, request: BlacklistRequest, db: Session = Depends(get_db)):
    member = db.query(EmktListMember).filter(EmktListMember.list_id == list_id, EmktListMember.company_id == company_id).first()
    if not member:
        raise HTTPException(404, "Khách hàng không thuộc list này.")
    member.blacklisted = int(request.blacklisted)
    db.commit()
    return {"updated": True, "blacklisted": bool(member.blacklisted)}


@router.put("/{list_id}/customers/{company_id}")
def update_customer_email(list_id: int, company_id: int, request: MemberEmailRequest, db: Session = Depends(get_db)):
    if not valid_email(request.email):
        raise HTTPException(400, "Email không hợp lệ.")
    member = db.query(EmktListMember).filter(EmktListMember.list_id == list_id, EmktListMember.company_id == company_id).first()
    if not member:
        raise HTTPException(404, "Khách hàng không thuộc list này.")
    member.custom_email = request.email.strip().lower(); db.commit()
    return {"updated": True, "email": member.custom_email}


@router.delete("/{list_id}/customers/{company_id}")
def remove_customer(list_id: int, company_id: int, db: Session = Depends(get_db)):
    member = db.query(EmktListMember).filter(EmktListMember.list_id == list_id, EmktListMember.company_id == company_id).first()
    if not member:
        raise HTTPException(404, "Khách hàng không thuộc list này.")
    db.delete(member); _sync_company_list_columns(db, {company_id}); db.commit()
    return {"removed": True}
