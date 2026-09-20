from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request

from app.ai_enrichment_worker import create_job, get_job, stop_job

router = APIRouter(prefix="/api/ai-enrichment", tags=["ai-enrichment"])
_job_id: str | None = None
logger = logging.getLogger(__name__)


def _admin(request: Request) -> None:
    if not request.session.get("user", {}).get("is_admin"):
        raise HTTPException(403, "Chỉ admin được hoàn thiện data bằng AI.")


@router.post("/start")
async def start(request: Request):
    global _job_id
    _admin(request)
    current = get_job(_job_id)
    if current and current.get("status") in {"queued", "running"}:
        return {"started": False, **current}
    try:
        _job_id = create_job()
    except Exception as exc:
        logger.exception("Could not create AI enrichment job")
        raise HTTPException(500, f"Không thể tạo job AI: {exc}") from exc
    return {"started": True, **get_job(_job_id)}


@router.get("/status")
async def status():
    job = get_job(_job_id)
    if not job:
        return {"status": "idle", "current": 0, "total": 0, "remaining": 0, "found": 0, "latest": ""}
    return {"status": {"queued": "running", "running": "running", "done": "completed", "error": "failed"}.get(job["status"], job["status"]), "current": job["processed"], "total": job["total"], "remaining": max(0, job["total"] - job["processed"]), "found": job["found"], "latest": job["latest"], "error": job.get("error"), "last_note": job.get("last_note", "")}


@router.post("/stop")
async def stop(request: Request):
    _admin(request)
    stop_job(_job_id)
    return {"stopped": True}
