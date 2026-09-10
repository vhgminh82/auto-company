from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.sheet_contact_worker import create_job, get_job

router = APIRouter(prefix="/api/contact/sheet", tags=["contact-sheet"])


class SheetJobRequest(BaseModel):
    spreadsheet_url: str = Field(min_length=20, max_length=2048)
    sheet_name: str = Field(default="company", min_length=1, max_length=200)
    batch_size: int = Field(default=100, ge=1, le=100)


@router.post("/run")
async def start_sheet_job(request: SheetJobRequest):
    try:
        job_id = create_job(request.spreadsheet_url, request.sheet_name, request.batch_size)
        return {"job_id": job_id, "status_url": f"/api/contact/sheet/status/{job_id}"}
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/status/{job_id}")
async def sheet_job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "Không tìm thấy job.")
    return job
