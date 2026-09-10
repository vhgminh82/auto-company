from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import psutil
from fastapi import APIRouter, HTTPException


router = APIRouter(prefix="/api/contact-enrichment", tags=["contact-enrichment"])
ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "craw_data" / "craw_company_contacts.py"
DATABASE = ROOT / "companies.db"
LOG_FILE = ROOT / "craw_data" / "company_contacts.log"
PROGRESS_FILE = ROOT / "craw_data" / "company_contacts_progress.txt"
PID_FILE = ROOT / "craw_data" / "company_contacts.pid"
_process: subprocess.Popen | None = None


def _saved_pid() -> int | None:
    try:
        return int(PID_FILE.read_text(encoding="ascii").strip())
    except (OSError, ValueError):
        return None


def _pid_running(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        process = psutil.Process(pid)
        return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
    except (psutil.NoSuchProcess, psutil.AccessDenied, OSError, SystemError):
        return False


def _remaining() -> int:
    try:
        with sqlite3.connect(DATABASE, timeout=10) as connection:
            return int(connection.execute(
                "SELECT count(*) FROM companies WHERE trim(website) != '' AND trim(coalesce(email, '')) = ''"
            ).fetchone()[0])
    except (OSError, sqlite3.Error):
        return 0


def _progress() -> dict:
    if not PROGRESS_FILE.exists():
        return {"current": 0, "total": 0, "remaining": _remaining(), "found": 0}
    try:
        parts = PROGRESS_FILE.read_text(encoding="utf-8").split("|", 4)
        state, current, total, found = parts[:4]
        return {"state": state.lower(), "current": int(current), "total": int(total), "remaining": _remaining(), "found": int(found), "latest": parts[4] if len(parts) > 4 else ""}
    except (OSError, ValueError):
        return {"current": 0, "total": 0, "remaining": _remaining(), "found": 0}


@router.post("/start")
def start_enrichment():
    global _process
    if not SCRIPT.is_file() or not DATABASE.is_file():
        raise HTTPException(404, "Thiếu script hoặc companies.db.")
    running_pid = _process.pid if _process and _process.poll() is None else _saved_pid()
    if _pid_running(running_pid):
        return {"started": False, "status": "running", **_progress()}
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_FILE.unlink(missing_ok=True)
    log = LOG_FILE.open("a", encoding="utf-8")
    try:
        _process = subprocess.Popen(
            [sys.executable, "-u", str(SCRIPT), "db", "--database", str(DATABASE), "--progress", str(PROGRESS_FILE), "--workers", "1", "--timeout", "5", "--delay", "0.1"],
            cwd=ROOT / "craw_data",
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        PID_FILE.write_text(str(_process.pid), encoding="ascii")
    finally:
        log.close()
    return {"started": True, "status": "running", "current": 0, "total": 0, "remaining": _remaining(), "found": 0}


@router.get("/status")
def enrichment_status():
    progress = _progress()
    pid = _process.pid if _process and _process.poll() is None else _saved_pid()
    if _pid_running(pid):
        return {"status": "running", **progress}
    PID_FILE.unlink(missing_ok=True)
    if progress.get("state") == "done":
        return {"status": "completed", **progress}
    if _process:
        return {"status": "completed" if _process.returncode == 0 else "failed", **progress}
    return {"status": "idle", **progress}


@router.post("/stop")
def stop_enrichment():
    global _process
    pid = _process.pid if _process and _process.poll() is None else _saved_pid()
    if _pid_running(pid):
        try:
            root = psutil.Process(pid)
            processes = root.children(recursive=True) + [root]
            for process in reversed(processes):
                try:
                    process.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            _, alive = psutil.wait_procs(processes, timeout=3)
            for process in alive:
                try:
                    process.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    _process = None
    PID_FILE.unlink(missing_ok=True)
    return {"stopped": True}
