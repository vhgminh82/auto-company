from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.company_source_import import import_company_source


router = APIRouter(prefix="/api/company-source", tags=["company-source"])


class CompanySourceImportRequest(BaseModel):
    spreadsheet_url: str = Field(min_length=20, max_length=2048)


@router.post("/import")
def import_source(request: CompanySourceImportRequest):
    try:
        return import_company_source(request.spreadsheet_url)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc
