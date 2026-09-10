from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.admin_repo import delete_all_companies
from app.repositories.company_repo import search_companies
from app.repositories.visited_repo import clear_visited
from app.schemas import CompanyOut
from app.models.company import Company

router = APIRouter(prefix="/api", tags=["companies"])


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


@router.delete("/companies")
def delete_companies(db: Session = Depends(get_db)):
    deleted_companies = delete_all_companies(db)
    deleted_visited = clear_visited(db)
    return {"deleted_companies": deleted_companies, "deleted_visited": deleted_visited}
