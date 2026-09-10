from __future__ import annotations

import asyncio
import uuid
from typing import Any

from app.contact_forms import inspect_url
from app.database import SessionLocal
from app.models.company import Company
from app.industry_normalizer import main_industry

_jobs: dict[str, dict[str, Any]] = {}
_tasks: dict[str, asyncio.Task] = {}


def _classify(result: dict) -> str:
    if result.get("error"):
        return "Lỗi"
    if any(form.get("has_captcha") for form in result.get("forms", [])):
        return "captcha"
    return "ok"


async def run_db_job(job_id: str, batch_size: int) -> None:
    job = _jobs[job_id]
    db = SessionLocal()
    try:
        pending = db.query(Company).filter(
            Company.website != "",
            (Company.contact == "") | (Company.contact.is_(None)) |
            (Company.industry == "") | (Company.industry.is_(None)) |
            (Company.industry == "Khác"),
        ).all()
        job.update(total=len(pending), status="running")
        print(f"[db-contact] job={job_id} pending={len(pending)}", flush=True)
        for offset in range(0, len(pending), batch_size):
            batch = pending[offset : offset + batch_size]
            sem = asyncio.Semaphore(20)

            async def process(company: Company):
                async with sem:
                    try:
                        result = await asyncio.wait_for(inspect_url(company.website), timeout=30)
                        return company, _classify(result), main_industry(f"{company.name} {company.address} {result.get('page_text', '')}")
                    except Exception as exc:
                        print(f"[db-contact] id={company.id} error={exc}", flush=True)
                        return company, "Lỗi", ""

            results = await asyncio.gather(*(process(company) for company in batch))
            for company, status, industry in results:
                if not (company.contact or "").strip():
                    company.contact = status
                if industry and industry != "Khác" and (not company.industry or company.industry == "Khác"):
                    company.industry = industry
            db.commit()
            job["processed"] += len(results)
            job["last_batch"] = {"count": len(results)}
            print(f"[db-contact] job={job_id} processed={job['processed']}/{job['total']}", flush=True)
        if job.get("status") != "stopped":
            job["status"] = "done"
    except asyncio.CancelledError:
        db.rollback()
        job["status"] = "stopped"
        raise
    except Exception as exc:
        db.rollback()
        job.update(status="error", error=str(exc))
        print(f"[db-contact] job={job_id} failed: {exc}", flush=True)
    finally:
        db.close()


def create_job(batch_size: int = 100) -> str:
    job_id = uuid.uuid4().hex
    _jobs[job_id] = {"job_id": job_id, "status": "queued", "total": 0, "processed": 0, "last_batch": None, "error": None}
    _tasks[job_id] = asyncio.create_task(run_db_job(job_id, batch_size))
    return job_id


def get_job(job_id: str) -> dict[str, Any] | None:
    return _jobs.get(job_id)


def stop_job(job_id: str) -> bool:
    job = _jobs.get(job_id)
    task = _tasks.get(job_id)
    if not job or not task or task.done():
        return False
    job["status"] = "stopped"
    task.cancel()
    return True
