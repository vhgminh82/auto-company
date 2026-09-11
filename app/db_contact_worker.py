from __future__ import annotations

import asyncio
import uuid
from typing import Any

from craw_data.craw_company_contacts import email_list, enrich_isolated
from app.contact_forms import inspect_url
from app.database import SessionLocal
from app.models.company import Company
from app.industry_normalizer import main_industry
from app.address_parser import parse_address

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
             ((Company.email == "") | (Company.email.is_(None)) |
             (Company.contact == "") | (Company.contact.is_(None)) |
             (Company.country == "") | (Company.country.is_(None)) |
             (Company.city == "") | (Company.city.is_(None)) |
             (Company.state == "") | (Company.state.is_(None))),
        ).all()
        job.update(total=len(pending), status="running", found=0, latest="")
        print(f"[db-contact] job={job_id} pending={len(pending)}", flush=True)

        for offset in range(0, len(pending), batch_size):
            batch = pending[offset:offset + batch_size]
            # inspect_url may start a Playwright browser; avoid exhausting
            # Chromium/process resources on the server.
            sem = asyncio.Semaphore(4)

            async def process(company: Company):
                async with sem:
                    try:
                        contact_result, email_result = await asyncio.gather(
                            asyncio.wait_for(inspect_url(company.website), timeout=30),
                            asyncio.wait_for(
                                asyncio.to_thread(enrich_isolated, company.website, 15, 0.1),
                                timeout=30,
                            ),
                        )
                        status = _classify(contact_result)
                        industry = main_industry(
                            f"{company.name} {company.address} {contact_result.get('page_text', '')}"
                        )
                        return company, status, industry, email_result
                    except Exception as exc:
                        print(f"[db-contact] id={company.id} error={type(exc).__name__}: {exc}", flush=True)
                        return company, "Lỗi", "", {"emails": ""}

            results = await asyncio.gather(*(process(company) for company in batch))
            for company, status, industry, email_result in results:
                parsed_country, parsed_city, parsed_state = parse_address(company.address, company.country)
                if parsed_country and not (company.country or "").strip():
                    company.country = parsed_country
                if parsed_city and not (company.city or "").strip():
                    company.city = parsed_city
                if parsed_state and not (company.state or "").strip():
                    company.state = parsed_state
                if not (company.contact or "").strip():
                    company.contact = status
                if industry and industry != "Khác" and (not company.industry or company.industry == "Khác"):
                    company.industry = industry

                emails = email_list(company.email or "", company.email_2 or "", email_result.get("emails", ""))
                if not (company.email or "").strip():
                    company.email = emails[0] if emails else "chưa có"
                    if emails:
                        job["found"] = job.get("found", 0) + 1
                if len(emails) > 1 and not (company.email_2 or "").strip():
                    company.email_2 = emails[1]
                    job["found"] = job.get("found", 0) + 1
                job["latest"] = company.name

            db.commit()
            job["processed"] += len(results)
            job["last_batch"] = {"count": len(results)}
            print(
                f"[db-contact] job={job_id} processed={job['processed']}/{job['total']} "
                f"found={job['found']}",
                flush=True,
            )

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
    _jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "total": 0,
        "processed": 0,
        "found": 0,
        "latest": "",
        "last_batch": None,
        "error": None,
    }
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
