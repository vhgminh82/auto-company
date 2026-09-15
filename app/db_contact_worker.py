from __future__ import annotations

import asyncio
import uuid
from typing import Any
from urllib.parse import urlsplit

from craw_data.craw_company_contacts import email_list, enrich_isolated
from app.address_parser import parse_address
from app.contact_forms import inspect_url
from app.core.url_utils import is_blocked_url
from app.database import SessionLocal
from app.industry_normalizer import main_industry
from app.models.company import Company

_jobs: dict[str, dict[str, Any]] = {}
_tasks: dict[str, asyncio.Task] = {}

DOMAIN_COUNTRIES = {
    ".vn": "Vietnam", ".ca": "Canada", ".au": "Australia", ".nz": "New Zealand",
    ".jp": "Japan", ".kr": "South Korea", ".in": "India", ".th": "Thailand",
    ".sg": "Singapore", ".de": "Germany", ".fr": "France", ".uk": "United Kingdom",
}


def _country_from_website(website: str) -> str:
    host = (urlsplit(website or "").hostname or "").casefold()
    for suffix, country in DOMAIN_COUNTRIES.items():
        if host.endswith(suffix):
            return country
    return ""


def _classify(result: dict) -> str:
    if result.get("error"):
        return "error"
    if any(form.get("has_captcha") for form in result.get("forms", [])):
        return "captcha"
    return "ok"


async def run_db_job(job_id: str, batch_size: int) -> None:
    job = _jobs[job_id]
    db = SessionLocal()
    try:
        pending = db.query(Company.id).filter(
            Company.website != "",
            ((Company.email == "") | (Company.email.is_(None)) |
             (Company.contact == "") | (Company.contact.is_(None)) |
             (Company.country == "") | (Company.country.is_(None)) |
             (Company.industry == "") | (Company.industry.is_(None)) |
             (Company.facebook == "") | (Company.facebook.is_(None)) |
             (Company.youtube == "") | (Company.youtube.is_(None)) |
             (Company.x == "") | (Company.x.is_(None)) |
             (Company.linkedin == "") | (Company.linkedin.is_(None)) |
             (Company.address == "") | (Company.address.is_(None))),
        ).all()
        pending_ids = [company_id for (company_id,) in pending]
        pending_ids = [
            company_id
            for company_id in pending_ids
            if (company := db.get(Company, company_id)) is not None
            and not is_blocked_url(company.website)
        ]
        job.update(total=len(pending_ids), status="running", found=0, latest="")
        print(f"[db-contact] job={job_id} pending={len(pending_ids)}", flush=True)

        for offset in range(0, len(pending_ids), batch_size):
            batch = pending_ids[offset:offset + batch_size]
            sem = asyncio.Semaphore(4)

            async def process(company_id: int):
                company = db.get(Company, company_id)
                if company is None or is_blocked_url(company.website):
                    return company_id, None
                async with sem:
                    try:
                        # Bulk enrichment is HTTP-only; Playwright is reserved for
                        # interactive contact-form inspection.
                        contact_result = await asyncio.wait_for(
                            inspect_url(company.website, allow_browser=False), timeout=20
                        )
                        email_result = await asyncio.wait_for(
                            asyncio.to_thread(enrich_isolated, company.website, 15, 0.1),
                            timeout=30,
                        )
                        industry = main_industry(
                            f"{company.name} {company.address} {contact_result.get('page_text', '')}"
                        )
                        country, _, _ = parse_address(company.address, company.country)
                        country = country or _country_from_website(company.website)
                        return company_id, _classify(contact_result), industry, country, email_result
                    except Exception as exc:
                        print(f"[db-contact] id={company_id} error={type(exc).__name__}: {exc}", flush=True)
                        return company_id, "error", "", "", {"emails": ""}

            results = await asyncio.gather(*(process(company) for company in batch))
            for company_id, status, industry, country, email_result in results:
                company = db.get(Company, company_id)
                if company is None or status is None or is_blocked_url(company.website):
                    continue
                if not (company.contact or "").strip():
                    company.contact = status if status != "error" else "chưa có"
                if not (company.industry or "").strip():
                    company.industry = industry if industry != "Khác" else "chưa có"
                if not (company.country or "").strip():
                    company.country = country or "chưa có"
                if not (company.address or "").strip():
                    company.address = (email_result.get("address") or "").strip() or "chưa có"

                facebook = (email_result.get("facebook") or "").strip()
                if facebook and not (company.facebook or "").strip():
                    company.facebook = facebook
                linkedin = (email_result.get("linkedin") or "").strip()
                if linkedin and not (company.linkedin or "").strip():
                    company.linkedin = linkedin
                if not (company.facebook or "").strip():
                    company.facebook = facebook or "chưa có"
                if not (company.youtube or "").strip():
                    company.youtube = (email_result.get("youtube") or "").strip() or "chưa có"
                if not (company.x or "").strip():
                    company.x = (email_result.get("x") or "").strip() or "chưa có"
                if not (company.linkedin or "").strip():
                    company.linkedin = linkedin or "chưa có"

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
                f"found={job['found']}", flush=True,
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
        "job_id": job_id, "status": "queued", "total": 0, "processed": 0,
        "found": 0, "latest": "", "last_batch": None, "error": None,
    }
    _tasks[job_id] = asyncio.create_task(run_db_job(job_id, min(batch_size, 4)))
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
