import asyncio

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.repositories.admin_repo import delete_all_companies
from app.repositories.company_repo import search_companies
from app.repositories.visited_repo import clear_visited
from app.schemas import CompanyOut
from app.models.company import Company
from app.industry_normalizer import main_industry
from fastapi import HTTPException, Request
from pydantic import BaseModel

class CompanyFieldUpdate(BaseModel):
    field: str
    value: str = ""

router = APIRouter(prefix="/api", tags=["companies"])
_industry_normalize_task: asyncio.Task | None = None
_industry_normalize_state = {"status": "idle", "changed": 0, "error": ""}


@router.get("/companies/count")
def company_count(db: Session = Depends(get_db)):
    return {"total": db.query(func.count(Company.id)).scalar() or 0}


@router.get("/companies", response_model=list[CompanyOut])
def list_companies(
    q: str = Query(default=""),
    country: str = Query(default=""),
    industry: str = Query(default=""),
    limit: int = Query(default=100, ge=1, le=25000),
    db: Session = Depends(get_db),
):
    return search_companies(db, q=q, country=country, industry=industry, limit=limit)


@router.get("/countries")
def list_countries(db: Session = Depends(get_db)):
    values = db.query(Company.country).filter(Company.country != "").distinct().all()
    return sorted({str(value[0]).strip() for value in values if str(value[0]).strip()}, key=str.casefold)


@router.get("/industries")
def list_industries(db: Session = Depends(get_db)):
    values = db.query(Company.industry).filter(Company.industry != "").distinct().all()
    return sorted({str(value[0]).strip() for value in values if str(value[0]).strip()}, key=str.casefold)


def _normalize_industries_sync() -> int:
    db = SessionLocal()
    changed = 0
    try:
        for company in db.query(Company).yield_per(1000):
            current = (company.industry or "").strip()
            if not current:
                continue
            normalized = main_industry(current)
            if normalized != current:
                if not (company.industry_raw or "").strip():
                    company.industry_raw = current
                company.industry = normalized
                changed += 1
            if changed and changed % 1000 == 0:
                db.commit()
        db.commit()
        return changed
    finally:
        db.close()


async def _run_industry_normalize() -> None:
    try:
        changed = await asyncio.to_thread(_normalize_industries_sync)
        _industry_normalize_state.update(status="done", changed=changed, error="")
    except Exception as exc:
        _industry_normalize_state.update(status="error", error=str(exc))


@router.get("/companies/normalize-industries/status")
def normalize_industries_status(request: Request):
    if not request.session.get("user", {}).get("is_admin"):
        raise HTTPException(403, "Chỉ admin được chuẩn hóa ngành.")
    return {"ok": _industry_normalize_state["status"] != "error", **_industry_normalize_state}


@router.post("/companies/normalize-industries")
async def normalize_industries(request: Request):
    global _industry_normalize_task
    if not request.session.get("user", {}).get("is_admin"):
        raise HTTPException(403, "Chỉ admin được chuẩn hóa ngành.")
    if _industry_normalize_task and not _industry_normalize_task.done():
        return {"ok": True, **_industry_normalize_state}
    _industry_normalize_state.update(status="running", changed=0, error="")
    _industry_normalize_task = asyncio.create_task(_run_industry_normalize())
    return {"ok": True, **_industry_normalize_state}


@router.patch("/companies/{company_id}")
def update_company_field(company_id: int, payload: CompanyFieldUpdate, request: Request, db: Session = Depends(get_db)):
    if not request.session.get("user", {}).get("is_admin"):
        raise HTTPException(403, "Chỉ admin được sửa dữ liệu.")
    editable = {"name", "address", "city", "state", "website", "contact", "email", "email_2", "phone", "short_description", "facebook", "facebook_alt", "youtube", "x", "linkedin", "truth", "country", "industry", "source_url"}
    if payload.field not in editable:
        raise HTTPException(400, "Trường dữ liệu không được phép sửa.")
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(404, "Không tìm thấy doanh nghiệp.")
    value = payload.value.strip()
    if payload.field == "industry" and value:
        value = main_industry(value)
    setattr(company, payload.field, value)
    db.commit()
    return {"ok": True, "id": company.id, "field": payload.field, "value": getattr(company, payload.field)}

@router.delete("/companies")
def delete_companies(db: Session = Depends(get_db)):
    deleted_companies = delete_all_companies(db)
    deleted_visited = clear_visited(db)
    return {"deleted_companies": deleted_companies, "deleted_visited": deleted_visited}
