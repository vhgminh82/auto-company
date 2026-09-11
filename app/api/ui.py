from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from io import BytesIO
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile
import threading
from urllib.request import Request as URLRequest, urlopen

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def index_page():
    return FileResponse("app/static/index.html")

import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GITHUB_REMOTE = "https://github.com/vhgminh82/auto-company.git"
GITHUB_BRANCH = "master"
GITHUB_API = "https://api.github.com/repos/vhgminh82/auto-company/commits/master"
GITHUB_ARCHIVE = "https://github.com/vhgminh82/auto-company/archive/refs/heads/master.tar.gz"
VERSION_FILE = PROJECT_ROOT / ".deploy_version"


def _git(*args: str) -> tuple[int, str]:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)
    return result.returncode, (result.stdout + result.stderr).strip()


def _github_head() -> str:
    request = URLRequest(GITHUB_API, headers={"User-Agent": "crawl-company-updater", "Accept": "application/vnd.github+json"})
    with urlopen(request, timeout=30) as response:
        return str(json.load(response)["sha"])


def _local_version() -> str:
    try:
        return VERSION_FILE.read_text(encoding="ascii").strip()
    except OSError:
        return ""


def _restart_process() -> None:
    os.execv(sys.executable, [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9997"])


def _download_update(commit: str) -> None:
    request = URLRequest(GITHUB_ARCHIVE, headers={"User-Agent": "crawl-company-updater"})
    with urlopen(request, timeout=120) as response:
        archive = response.read()
    with tempfile.TemporaryDirectory(prefix="crawl-company-update-") as temp_dir:
        with tarfile.open(fileobj=BytesIO(archive), mode="r:gz") as tar:
            tar.extractall(temp_dir, filter="data")
        roots = [item for item in Path(temp_dir).iterdir() if item.is_dir()]
        if len(roots) != 1:
            raise RuntimeError("GitHub archive có cấu trúc không hợp lệ.")
        source = roots[0]
        for item in source.iterdir():
            if item.name in {".git", ".env", ".deploy_version", "results", "__pycache__"}:
                continue
            destination = PROJECT_ROOT / item.name
            if item.is_dir():
                shutil.copytree(item, destination, dirs_exist_ok=True)
            else:
                shutil.copy2(item, destination)
    VERSION_FILE.write_text(commit, encoding="ascii")


@router.get("/api/system/update/check")
def check_update(request: Request):
    if not request.session.get("user", {}).get("is_admin"):
        raise HTTPException(403, "Chỉ admin được phép kiểm tra cập nhật.")
    code, output = _git("remote", "get-url", "origin")
    if code or output != GITHUB_REMOTE:
        try:
            remote = _github_head()
        except Exception as exc:
            return {"ok": False, "message": f"Không kiểm tra được GitHub: {exc}"}
        local = _local_version()
        return {"ok": True, "updated": local != remote, "local": local[:12] or "unknown", "remote": remote[:12], "source": "github-archive"}
    code, output = _git("fetch", "origin", GITHUB_BRANCH)
    if code:
        return {"ok": False, "message": output or "Không thể kiểm tra GitHub."}
    _, local = _git("rev-parse", "HEAD")
    _, remote = _git("rev-parse", f"origin/{GITHUB_BRANCH}")
    return {"ok": True, "updated": local != remote, "local": local[:12], "remote": remote[:12]}


@router.post("/api/system/update")
def update_from_github(request: Request):
    if not request.session.get("user", {}).get("is_admin"):
        raise HTTPException(403, "Chỉ admin được phép cập nhật hệ thống.")
    check = check_update(request)
    if not check.get("ok"):
        return check
    if not check.get("updated"):
        return {"ok": True, "updated": False, "message": "App đã là phiên bản mới nhất."}
    if check.get("source") == "github-archive":
        try:
            _download_update(check["remote"] if len(check["remote"]) == 40 else _github_head())
        except Exception as exc:
            return {"ok": False, "message": f"Tải bản cập nhật thất bại: {exc}"}
        threading.Timer(1.0, _restart_process).start()
        return {"ok": True, "updated": True, "restart_required": True, "message": "Đã cập nhật và đang khởi động lại app."}
    _, dirty = _git("status", "--porcelain")
    if dirty:
        return {"ok": False, "message": "Có thay đổi local chưa commit; không tự ghi đè."}
    code, output = _git("pull", "--ff-only", "origin", GITHUB_BRANCH)
    if code:
        return {"ok": False, "message": output or "Pull thất bại."}
    return {"ok": True, "updated": True, "restart_required": True, "message": "Đã cập nhật mã nguồn. Cần khởi động lại app.", "output": output}
