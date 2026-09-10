from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.sheet_sync import sync_company_sheet

router = APIRouter(prefix="/api/sheet", tags=["sheet-sync"])


class SheetSyncRequest(BaseModel):
    spreadsheet_url: str = Field(min_length=20, max_length=2048)
    sheet_name: str = Field(default="company", min_length=1, max_length=200)


@router.post("/sync")
def sync_sheet(request: SheetSyncRequest):
    try:
        return sync_company_sheet(request.spreadsheet_url, request.sheet_name)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc
