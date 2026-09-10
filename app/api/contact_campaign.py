from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.contact_forms import inspect_url
from app.database import get_db, SessionLocal
from app.models.company import Company
from app.models.emkt import ContactList, ContactListMember, ContactRun, ContactScenario

router = APIRouter(prefix="/api/contact-campaign", tags=["contact-campaign"])
_jobs: dict[int, dict] = {}


class ScenarioRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    fields: dict[str, str] = {}


class RunRequest(BaseModel):
    list_ids: list[int] = []
    scenario_id: int


class ContactListRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    country_filter: str = ""
    industry_filter: str = ""


def _scenario_out(item):
    return {"id": item.id, "name": item.name, "fields": item.fields or {}, "created_at": item.created_at, "updated_at": item.updated_at}


@router.get("/scenarios")
def scenarios(db: Session = Depends(get_db)):
    return [_scenario_out(x) for x in db.query(ContactScenario).order_by(ContactScenario.id.desc()).all()]


@router.post("/scenarios")
def create_scenario(request: ScenarioRequest, db: Session = Depends(get_db)):
    item = ContactScenario(name=request.name.strip(), fields=request.fields)
    db.add(item)
    try:
        db.commit(); db.refresh(item)
    except Exception as exc:
        db.rollback(); raise HTTPException(400, f"Không lưu được kịch bản: {exc}") from exc
    return _scenario_out(item)


@router.put("/scenarios/{scenario_id}")
def update_scenario(scenario_id: int, request: ScenarioRequest, db: Session = Depends(get_db)):
    item = db.get(ContactScenario, scenario_id)
    if not item: raise HTTPException(404, "Không tìm thấy kịch bản.")
    item.name = request.name.strip(); item.fields = request.fields
    db.commit(); db.refresh(item)
    return _scenario_out(item)


@router.delete("/scenarios/{scenario_id}")
def delete_scenario(scenario_id: int, db: Session = Depends(get_db)):
    item = db.get(ContactScenario, scenario_id)
    if not item: raise HTTPException(404, "Không tìm thấy kịch bản.")
    db.delete(item); db.commit(); return {"deleted": scenario_id}


@router.get("/lists")
def contact_lists(db: Session = Depends(get_db)):
    result = []
    for item in db.query(ContactList).order_by(ContactList.name):
        count = (db.query(ContactListMember).join(Company, Company.id == ContactListMember.company_id)
                 .filter(ContactListMember.list_id == item.id, Company.contact.ilike("ok")).count())
        result.append({"id": item.id, "name": item.name, "country_filter": item.country_filter, "industry_filter": item.industry_filter, "customer_count": count})
    return result


@router.get("/facets")
def contact_facets(db: Session = Depends(get_db)):
    countries, industries = {}, {}
    for company in db.query(Company).filter(Company.contact.ilike("ok")).yield_per(1000):
        if company.country: countries[company.country] = countries.get(company.country, 0) + 1
        if company.industry: industries[company.industry] = industries.get(company.industry, 0) + 1
    return {"countries": countries, "industries": industries}


@router.post("/lists")
def create_contact_list(request: ContactListRequest, db: Session = Depends(get_db)):
    item = ContactList(name=request.name.strip(), country_filter=request.country_filter.strip(), industry_filter=request.industry_filter.strip())
    db.add(item); db.flush()
    query = db.query(Company.id).filter(Company.contact.ilike("ok"))
    if item.country_filter: query = query.filter(Company.country.ilike(f"%{item.country_filter}%"))
    if item.industry_filter: query = query.filter(Company.industry.ilike(f"%{item.industry_filter}%"))
    for (company_id,) in query.all(): db.add(ContactListMember(list_id=item.id, company_id=company_id))
    try:
        db.commit(); db.refresh(item)
    except Exception as exc:
        db.rollback(); raise HTTPException(400, f"Không tạo được list contact: {exc}") from exc
    return {"id": item.id, "name": item.name, "country_filter": item.country_filter, "industry_filter": item.industry_filter, "customer_count": db.query(ContactListMember).filter(ContactListMember.list_id == item.id).count()}


def _refresh_contact_list(db: Session, item: ContactList) -> int:
    db.query(ContactListMember).filter(ContactListMember.list_id == item.id).delete(synchronize_session=False)
    query = db.query(Company.id).filter(Company.contact.ilike("ok"))
    if item.country_filter: query = query.filter(or_(*[Company.country.ilike(f"%{x.strip()}%") for x in item.country_filter.split(",") if x.strip()]))
    if item.industry_filter: query = query.filter(or_(*[Company.industry.ilike(f"%{x.strip()}%") for x in item.industry_filter.split(",") if x.strip()]))
    ids = [x[0] for x in query.all()]
    for company_id in ids: db.add(ContactListMember(list_id=item.id, company_id=company_id))
    db.flush()
    return len(ids)


@router.put("/lists/{list_id}")
def update_contact_list(list_id: int, request: ContactListRequest, db: Session = Depends(get_db)):
    item = db.get(ContactList, list_id)
    if not item: raise HTTPException(404, "Không tìm thấy list contact.")
    item.name = request.name.strip(); item.country_filter = request.country_filter.strip(); item.industry_filter = request.industry_filter.strip()
    try:
        count = _refresh_contact_list(db, item); db.commit()
    except Exception as exc:
        db.rollback(); raise HTTPException(400, f"Không cập nhật được list contact: {exc}") from exc
    return {"id": item.id, "name": item.name, "customer_count": count, "country_filter": item.country_filter, "industry_filter": item.industry_filter}


@router.delete("/lists/{list_id}")
def delete_contact_list(list_id: int, db: Session = Depends(get_db)):
    item = db.get(ContactList, list_id)
    if not item: raise HTTPException(404, "Không tìm thấy list contact.")
    db.query(ContactListMember).filter(ContactListMember.list_id == list_id).delete(synchronize_session=False); db.delete(item); db.commit()
    return {"deleted": list_id}


@router.get("/lists/{list_id}/customers")
def contact_list_customers(list_id: int, db: Session = Depends(get_db)):
    if not db.get(ContactList, list_id): raise HTTPException(404, "Không tìm thấy list contact.")
    rows = db.query(Company).join(ContactListMember, ContactListMember.company_id == Company.id).filter(ContactListMember.list_id == list_id, Company.contact.ilike("ok")).order_by(Company.name).all()
    return [{"id": x.id, "name": x.name, "email": x.email or x.email_2, "website": x.website, "country": x.country, "industry": x.industry} for x in rows]


@router.get("/runs")
def contact_runs(db: Session = Depends(get_db)):
    return [{"id": x.id, "scenario_id": x.scenario_id, "list_ids": json.loads(x.list_ids or "[]"), "started_at": x.started_at, "completed_at": x.completed_at, "status": x.status, "total": x.total, "processed": x.processed, "success": x.success, "failed": x.failed, "captcha": x.captcha} for x in db.query(ContactRun).order_by(ContactRun.id.desc()).limit(100)]


async def _run_contact(run_id: int, company_ids: list[int], fields: dict[str, str]):
    from app.api.contact import submit_contact
    db = SessionLocal(); run = db.get(ContactRun, run_id); run.status = "running"; db.commit()
    sem = asyncio.Semaphore(5)
    async def one(company_id):
        async with sem:
            company = db.get(Company, company_id)
            try:
                result = await asyncio.wait_for(inspect_url(company.website), timeout=30)
                form = next((x for x in result.get("forms", []) if not x.get("has_captcha")), None)
                if not form:
                    return "captcha" if any(x.get("has_captcha") for x in result.get("forms", [])) else "failed"
                values = {key: str(value).replace("{{company_name}}", company.name).replace("{{website}}", company.website) for key, value in fields.items()}
                payload = type("Request", (), {"page_url": form["page_url"], "action": form["action"], "form_index": form["form_index"], "fields": values, "confirm": True})()
                await submit_contact(payload)
                return "success"
            except Exception:
                return "failed"
    try:
        results = await asyncio.gather(*(one(x) for x in company_ids))
        run.processed = len(results); run.success = results.count("success"); run.captcha = results.count("captcha"); run.failed = results.count("failed")
        run.status = "completed"; run.completed_at = datetime.now(timezone.utc); db.commit()
    except Exception:
        run.status = "failed"; db.commit()
    finally: db.close()


@router.post("/run")
async def start_run(request: RunRequest, db: Session = Depends(get_db)):
    if not request.list_ids: raise HTTPException(400, "Hãy chọn ít nhất một list contact.")
    if not db.get(ContactScenario, request.scenario_id): raise HTTPException(404, "Không tìm thấy kịch bản.")
    ids = [x[0] for x in db.query(ContactListMember.company_id).join(Company, Company.id == ContactListMember.company_id).filter(ContactListMember.list_id.in_(request.list_ids), Company.contact.ilike("ok")).distinct().all()]
    run = ContactRun(scenario_id=request.scenario_id, list_ids=json.dumps(request.list_ids), total=len(ids))
    db.add(run); db.commit(); db.refresh(run)
    scenario = db.get(ContactScenario, request.scenario_id)
    asyncio.create_task(_run_contact(run.id, ids, scenario.fields or {}))
    return {"run_id": run.id, "status": "queued", "total": len(ids)}


@router.get("/run/{run_id}")
def run_status(run_id: int, db: Session = Depends(get_db)):
    run = db.get(ContactRun, run_id)
    if not run: raise HTTPException(404, "Không tìm thấy lần chạy.")
    return {"status": run.status, "total": run.total, "processed": run.processed, "success": run.success, "failed": run.failed, "captcha": run.captcha}
