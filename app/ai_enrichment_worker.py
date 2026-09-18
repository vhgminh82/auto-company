from __future__ import annotations

import asyncio
import json
import re
import uuid
from typing import Any

from app.ai_service import OpenRouterError, chat_completion
from app.contact_forms import inspect_url
from app.database import SessionLocal
from app.models.ai import AISetting
from app.models.company import Company

_jobs: dict[str, dict[str, Any]] = {}
_tasks: dict[str, asyncio.Task] = {}
FIELDS = ("address", "city", "state", "country", "industry", "email", "email_2", "phone", "facebook", "linkedin", "youtube", "x")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _ai_config(db) -> tuple[list[str], str]:
    defaults = ("nvidia/nemotron-3-ultra-550b-a55b", "poolside/laguna-s-2.1", "inclusionai/ling-3.0-flash-fin")
    item = db.get(AISetting, 1)
    models = [
        (item.primary_model if item else "").strip() or defaults[0],
        (item.fallback_model_1 if item else "").strip() or defaults[1],
        (item.fallback_model_2 if item else "").strip() or defaults[2],
    ]
    return list(dict.fromkeys(models)), (item.custom_prompt if item else "").strip()


async def _extract(models: list[str], custom: str, company: Company, page_text: str) -> dict[str, Any]:
    prompt = f"""Trích xuất dữ liệu doanh nghiệp từ thông tin dưới đây.
Chỉ trả về JSON object với đúng các key: address, city, state, country, industry, email, email_2, phone, facebook, linkedin, youtube, x, evidence.
Mỗi giá trị là chuỗi; nếu không thấy rõ thì để chuỗi rỗng. evidence là object chứa bằng chứng ngắn cho các giá trị đã trích xuất.
Tuyệt đối không suy đoán hoặc bịa dữ liệu. Chỉ lấy thông tin được nêu rõ trên website hoặc dữ liệu công ty.
country dùng tên tiếng Anh chuẩn; industry mô tả ngắn gọn bằng tiếng Việt.

Dữ liệu công ty: tên={company.name}; website={company.website}; dữ liệu hiện có={company.address}, {company.city}, {company.state}, {company.country}; ngành={company.industry}

Nội dung website:
{page_text[:12000]}"""
    if custom:
        prompt += f"\nHướng dẫn bổ sung của quản trị viên:\n{custom[:5000]}"
    errors = []
    for model in models:
        try:
            raw = await chat_completion([
                {"role": "system", "content": "Bạn là bộ máy trích xuất dữ liệu B2B chính xác, chỉ dùng bằng chứng được cung cấp."},
                {"role": "user", "content": prompt},
            ], model=model)
            result = json.loads(raw.strip().removeprefix("```json").removesuffix("```").strip())
            return result if isinstance(result, dict) else {}
        except (OpenRouterError, json.JSONDecodeError, TypeError, ValueError) as exc:
            errors.append(f"{model}: {exc}")
    raise OpenRouterError("AI enrichment thất bại: " + " | ".join(errors))


def _safe_result(result: dict[str, Any]) -> dict[str, str]:
    evidence = result.get("evidence") if isinstance(result.get("evidence"), dict) else {}
    cleaned = {field: str(result.get(field) or "").strip()[:512] if str(evidence.get(field) or "").strip() else "" for field in FIELDS}
    for field in ("email", "email_2"):
        if cleaned[field] and not EMAIL_RE.fullmatch(cleaned[field]):
            cleaned[field] = ""
    return cleaned


async def run_job(job_id: str) -> None:
    job = _jobs[job_id]
    db = SessionLocal()
    try:
        models, custom = _ai_config(db)
        pending = db.query(Company).filter(
            Company.website != "",
            ((Company.address == "") | (Company.address.is_(None)) | (Company.city == "") | (Company.city.is_(None)) |
             (Company.state == "") | (Company.state.is_(None)) | (Company.country == "") | (Company.country.is_(None)) |
             (Company.industry == "") | (Company.industry.is_(None)) | (Company.email == "") | (Company.email.is_(None)) |
             (Company.phone == "") | (Company.phone.is_(None)) | (Company.facebook == "") | (Company.facebook.is_(None)) |
             (Company.linkedin == "") | (Company.linkedin.is_(None)) | (Company.youtube == "") | (Company.youtube.is_(None)) |
             (Company.x == "") | (Company.x.is_(None))),
        ).all()
        pending.sort(key=lambda company: (-sum(not (getattr(company, field, "") or "").strip() for field in FIELDS), company.id))
        job.update(total=len(pending), status="running")
        sem = asyncio.Semaphore(2)

        async def process(company: Company):
            async with sem:
                try:
                    page = await asyncio.wait_for(inspect_url(company.website, allow_browser=False), timeout=25)
                except asyncio.TimeoutError:
                    return company.id, {}, "website_error: timeout"
                except Exception as exc:
                    return company.id, {}, f"website_error: {type(exc).__name__}"

                if page.get("error") or not page.get("page_text"):
                    return company.id, {}, "website_error: không tải được website"
                try:
                    result = await asyncio.wait_for(_extract(models, custom, company, page["page_text"]), timeout=65)
                    return company.id, _safe_result(result), "AI đã trích xuất"
                except Exception as exc:
                    return company.id, {}, f"lỗi: {type(exc).__name__}"

        for offset in range(0, len(pending), 2):
            results = await asyncio.gather(*(process(company) for company in pending[offset:offset + 2]))
            for company_id, result, note in results:
                company = db.get(Company, company_id)
                if not company:
                    continue
                changed = 0
                if note.startswith("website_error") and not (company.contact or "").strip():
                    company.contact = "404"
                    changed += 1
                for field in FIELDS:
                    if not (getattr(company, field, "") or "").strip() and result.get(field):
                        setattr(company, field, result[field])
                        changed += 1
                if changed:
                    job["found"] += changed
                    job["latest"] = company.name
                job["processed"] += 1
                job["last_note"] = f"{company.name}: {note}"
            db.commit()
        job["status"] = "done" if job.get("status") != "stopped" else "stopped"
    except asyncio.CancelledError:
        db.rollback()
        job["status"] = "stopped"
        raise
    except Exception as exc:
        db.rollback()
        job.update(status="error", error=str(exc))
    finally:
        db.close()


def create_job() -> str:
    job_id = uuid.uuid4().hex
    _jobs[job_id] = {"job_id": job_id, "status": "queued", "total": 0, "processed": 0, "found": 0, "latest": "", "last_note": "", "error": None}
    _tasks[job_id] = asyncio.create_task(run_job(job_id))
    return job_id


def get_job(job_id: str | None) -> dict[str, Any] | None:
    return _jobs.get(job_id) if job_id else None


def stop_job(job_id: str | None) -> bool:
    task = _tasks.get(job_id or "")
    job = get_job(job_id)
    if not task or not job or task.done():
        return False
    job["status"] = "stopped"
    task.cancel()
    return True
