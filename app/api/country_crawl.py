from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import psutil
from fastapi import APIRouter, HTTPException, Request


router = APIRouter(prefix="/api/country-crawl", tags=["country-crawl"])
CRAWL_DIR = Path(__file__).resolve().parents[2] / "craw_country"
BATCH_FILE = CRAWL_DIR / "1_find_country_company.bat"
PYTHON_RUNNER = CRAWL_DIR / "country_crawl_runner.py"
PROGRESS_FILE = CRAWL_DIR / "results" / "crawl_progress.txt"
PID_FILE = CRAWL_DIR / "results" / "crawl.pid"
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


def _crawler_pid_running(pid: int | None) -> bool:
    """Return true only when the PID belongs to this crawler, not a reused PID."""
    if not _pid_running(pid):
        return False
    try:
        command_line = " ".join(psutil.Process(pid).cmdline()).lower()
    except (psutil.NoSuchProcess, psutil.AccessDenied, OSError, SystemError):
        return False
    expected = (str(BATCH_FILE) if os.name == "nt" else str(PYTHON_RUNNER)).lower()
    return expected in command_line


def _progress() -> dict:
    if not PROGRESS_FILE.exists():
        return {"state": "idle", "current": 0, "total": 0, "query": ""}
    try:
        parts = PROGRESS_FILE.read_text(encoding="utf-8").split("|", 4)
        state, current, total = parts[:3]
        query = parts[3].strip() if len(parts) > 3 else ""
        found = int(parts[4]) if len(parts) > 4 and parts[4].strip().isdigit() else 0
        return {"state": state.lower(), "current": int(current), "total": int(total), "query": query, "found": found}
    except (OSError, ValueError):
        return {"state": "running", "current": 0, "total": 0, "query": "", "found": 0}


def start_crawl_job(auto: bool = False, request: Request | None = None):
    if request is not None and not request.session.get("user", {}).get("is_admin"):
        raise HTTPException(403, "Chỉ admin được tìm doanh nghiệp.")
    if os.name != "nt":
        raise HTTPException(501, "Country crawl trên server chỉ được phép chạy Google Maps; chưa bật bộ Google Maps scraper.")
    global _process
    if os.name == "nt":
        command = ["cmd.exe", "/c", str(BATCH_FILE)]
    else:
        if not PYTHON_RUNNER.is_file():
            raise HTTPException(404, "country crawl runner not found.")
        command = [sys.executable, str(PYTHON_RUNNER), "--progress", str(PROGRESS_FILE)]
    running_pid = _process.pid if _process and _process.poll() is None else _saved_pid()
    if _crawler_pid_running(running_pid):
        return {"started": False, **_progress()}
    PID_FILE.unlink(missing_ok=True)
    if auto and _progress().get("state") == "done":
        return {"started": False, **_progress()}
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_FILE.unlink(missing_ok=True)
    try:
        _process = subprocess.Popen(
            command,
            cwd=CRAWL_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except OSError as exc:
        raise HTTPException(500, f"Không thể khởi động crawler: {exc}") from exc
    PID_FILE.write_text(str(_process.pid), encoding="ascii")
    return {"started": True, "state": "running", "current": 0, "total": 0, "query": "", "found": 0}


def country_crawl_running() -> bool:
    running_pid = _process.pid if _process and _process.poll() is None else _saved_pid()
    return _crawler_pid_running(running_pid)


@router.post("/start")
def start_crawl(request: Request):
    return start_crawl_job(request=request)


@router.post("/stop")
def stop_crawl(request: Request):
    if not request.session.get("user", {}).get("is_admin"):
        raise HTTPException(403, "Chỉ admin được dừng tìm doanh nghiệp.")
    if os.name != "nt":
        raise HTTPException(501, "Country crawl trên server chỉ được phép chạy Google Maps; chưa bật bộ Google Maps scraper.")
    global _process
    current = _progress()
    pid = _process.pid if _process and _process.poll() is None else _saved_pid()
    if _crawler_pid_running(pid):
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
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_FILE.write_text(
        f"STOPPED|{current['current']}|{current['total']}|{current['query']}|{current.get('found', 0)}",
        encoding="utf-8",
    )
    return {"stopped": True, **_progress()}


@router.get("/status")
def crawl_status():
    result = _progress()
    pid = _process.pid if _process and _process.poll() is None else _saved_pid()
    result["running"] = _pid_running(pid)
    if not result["running"]:
        PID_FILE.unlink(missing_ok=True)
    return result
