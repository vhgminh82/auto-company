from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def index_page():
    return FileResponse("app/static/index.html")

import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GITHUB_REMOTE = "https://github.com/vhgminh82/auto-company.git"
GITHUB_BRANCH = "master"


def _git(*args: str) -> tuple[int, str]:
    result = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    return result.returncode, (result.stdout + result.stderr).strip()


@router.get("/api/system/update/check")
def check_update():
    code, output = _git("remote", "get-url", "origin")
    if code or output != GITHUB_REMOTE:
        return {"ok": False, "message": "Remote GitHub không đúng repository đã cấu hình."}
    code, output = _git("fetch", "origin", GITHUB_BRANCH)
    if code:
        return {"ok": False, "message": output or "Không thể kiểm tra GitHub."}
    _, local = _git("rev-parse", "HEAD")
    _, remote = _git("rev-parse", f"origin/{GITHUB_BRANCH}")
    return {"ok": True, "updated": local != remote, "local": local[:12], "remote": remote[:12]}


@router.post("/api/system/update")
def update_from_github():
    check = check_update()
    if not check.get("ok"):
        return check
    if not check.get("updated"):
        return {"ok": True, "updated": False, "message": "App đã là phiên bản mới nhất."}
    _, dirty = _git("status", "--porcelain")
    if dirty:
        return {"ok": False, "message": "Có thay đổi local chưa commit; không tự ghi đè."}
    code, output = _git("pull", "--ff-only", "origin", GITHUB_BRANCH)
    if code:
        return {"ok": False, "message": output or "Pull thất bại."}
    return {"ok": True, "updated": True, "restart_required": True, "message": "Đã cập nhật mã nguồn. Cần khởi động lại app.", "output": output}
