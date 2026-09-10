from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.db_contact_worker import create_job, get_job, stop_job

router = APIRouter(prefix="/api/contact/db", tags=["contact-db"])


class DbJobRequest(BaseModel):
    batch_size: int = Field(default=100, ge=1, le=100)


@router.post("/run")
async def start_db_job(request: DbJobRequest):
    try:
        job_id = create_job(request.batch_size)
        return {"job_id": job_id, "status_url": f"/api/contact/db/status/{job_id}"}
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/status/{job_id}")
async def db_job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "Không tìm thấy job.")
    return job


@router.post("/stop/{job_id}")
async def stop_db_job(job_id: str):
    if not stop_job(job_id):
        raise HTTPException(404, "Job không còn đang chạy.")
    return {"stopped": True, "job_id": job_id}
