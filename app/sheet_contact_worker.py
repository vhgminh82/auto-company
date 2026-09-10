from __future__ import annotations

import asyncio
import json
import os
import re
import uuid
from typing import Any

from app.contact_forms import inspect_url

_jobs: dict[str, dict[str, Any]] = {}


def _spreadsheet_id(value: str) -> str:
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", value)
    if not match:
        raise ValueError("Google Sheet URL không hợp lệ.")
    return match.group(1)


def _client():
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError("Thiếu google-api-python-client và google-auth.") from exc
    raw = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    filename = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    if raw:
        info = json.loads(raw)
        credentials = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    elif filename:
        credentials = Credentials.from_service_account_file(filename, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    else:
        raise RuntimeError("Chưa cấu hình GOOGLE_SERVICE_ACCOUNT_JSON hoặc GOOGLE_SERVICE_ACCOUNT_FILE.")
    return build("sheets", "v4", credentials=credentials, cache_discovery=False)


def _classify(result: dict) -> str:
    if result.get("error"):
        return "Lỗi"
    if any(form.get("has_captcha") for form in result.get("forms", [])):
        return "captcha"
    return "ok"


async def run_sheet_job(job_id: str, spreadsheet_url: str, sheet_name: str, batch_size: int) -> None:
    job = _jobs[job_id]
    try:
        service = _client()
        sid = _spreadsheet_id(spreadsheet_url)
        response = service.spreadsheets().values().get(
            spreadsheetId=sid, range=f"'{sheet_name}'!A:E", majorDimension="ROWS"
        ).execute()
        rows = response.get("values", [])
        pending = []
        for row_number, row in enumerate(rows[1:], start=2):
            website = str(row[3]).strip() if len(row) > 3 else ""
            contact = str(row[4]).strip() if len(row) > 4 else ""
            if website and not contact:
                pending.append((row_number, website))
        job.update(total=len(pending), status="running")
        print(f"[sheet] job={job_id} pending={len(pending)}", flush=True)

        for offset in range(0, len(pending), batch_size):
            batch = pending[offset : offset + batch_size]
            sem = asyncio.Semaphore(20)

            async def process(item):
                async with sem:
                    row_number, website = item
                    try:
                        status = _classify(await asyncio.wait_for(inspect_url(website), timeout=30))
                    except Exception as exc:
                        print(f"[sheet] row={row_number} error={exc}", flush=True)
                        status = "Web lỗi"
                    return row_number, status

            results = await asyncio.gather(*(process(item) for item in batch))
            data = [{"range": f"'{sheet_name}'!E{row}:E{row}", "values": [[status]]} for row, status in results]
            service.spreadsheets().values().batchUpdate(
                spreadsheetId=sid, body={"valueInputOption": "RAW", "data": data}
            ).execute()
            job["processed"] += len(results)
            job["last_batch"] = {"first_row": results[0][0], "last_row": results[-1][0], "count": len(results)}
            print(f"[sheet] job={job_id} wrote rows {results[0][0]}-{results[-1][0]} processed={job['processed']}/{job['total']}", flush=True)
        job["status"] = "done"
    except Exception as exc:
        job.update(status="error", error=str(exc))
        print(f"[sheet] job={job_id} failed: {exc}", flush=True)


def create_job(spreadsheet_url: str, sheet_name: str, batch_size: int) -> str:
    job_id = uuid.uuid4().hex
    _jobs[job_id] = {"job_id": job_id, "status": "queued", "total": 0, "processed": 0, "last_batch": None, "error": None}
    asyncio.create_task(run_sheet_job(job_id, spreadsheet_url, sheet_name, batch_size))
    return job_id


def get_job(job_id: str) -> dict[str, Any] | None:
    return _jobs.get(job_id)
