from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.database import SessionLocal
from app.db_contact_worker import create_job, get_job, stop_job
from app.models.company import Company

router = APIRouter(prefix="/api/contact-enrichment", tags=["contact-enrichment"])
_job_id: str | None = None


def _remaining() -> int:
    db = SessionLocal()
    try:
        return db.query(Company).filter(
            Company.website != "",
            (Company.email == "") | (Company.email.is_(None)) |
            (Company.contact == "") | (Company.contact.is_(None)) |
            (Company.country == "") | (Company.country.is_(None)) |
            (Company.industry == "") | (Company.industry.is_(None)) |
            (Company.facebook == "") | (Company.facebook.is_(None)),
            (Company.youtube == "") | (Company.youtube.is_(None)) |
            (Company.x == "") | (Company.x.is_(None)) |
            (Company.linkedin == "") | (Company.linkedin.is_(None)) |
            (Company.address == "") | (Company.address.is_(None)),
        ).count()
    finally:
        db.close()


def _progress() -> dict:
    job = get_job(_job_id) if _job_id else None
    if not job:
        return {"state": "idle", "current": 0, "total": 0, "remaining": _remaining(), "found": 0, "latest": ""}
    return {
        "state": job.get("status", "idle"),
        "current": job.get("processed", 0),
        "total": job.get("total", 0),
        "remaining": max(0, job.get("total", 0) - job.get("processed", 0)),
        "found": job.get("found", 0),
        "latest": job.get("latest", ""),
        "error": job.get("error"),
    }


@router.post("/start")
async def start_enrichment(request: Request):
    if not request.session.get("user", {}).get("is_admin"):
        raise HTTPException(403, "Chỉ admin được hoàn thiện data.")
    global _job_id
    if _job_id:
        existing = get_job(_job_id)
        if existing and existing.get("status") in {"queued", "running"}:
            return {"started": False, "status": "running", **_progress()}
    # Keep batches small so the UI receives progress quickly on large datasets.
    _job_id = create_job(batch_size=4)
    return {"started": True, "status": "running", **_progress()}


@router.get("/status")
async def enrichment_status():
    progress = _progress()
    status = progress.get("state", "idle")
    public_status = "running" if status in {"queued", "running"} else ("failed" if status == "error" else status)
    return {"status": public_status, **progress}


@router.post("/stop")
async def stop_enrichment(request: Request):
    if not request.session.get("user", {}).get("is_admin"):
        raise HTTPException(403, "Chỉ admin được dừng hoàn thiện data.")
    if _job_id:
        stop_job(_job_id)
    return {"stopped": True, **_progress()}
