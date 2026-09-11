import os
import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import AppUser

ADMIN_EMAILS = {"vhglinh@gmail.com", "icdirector@cnctech.vn"}

def _is_admin(request: Request) -> bool:
    return bool(request.session.get("user", {}).get("is_admin"))

router = APIRouter()
GOOGLE_AUTHORIZE = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN = "https://oauth2.googleapis.com/token"
MICROSOFT_AUTHORIZE = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
MICROSOFT_TOKEN = "https://login.microsoftonline.com/common/oauth2/v2.0/token"

def _base_url(request: Request) -> str:
    return os.getenv("AUTH_BASE_URL", str(request.base_url).rstrip("/"))

def _providers():
    return {
        "google": {"label": "Google / Gmail", "client_id": os.getenv("GOOGLE_CLIENT_ID", ""), "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""), "authorize": GOOGLE_AUTHORIZE, "token": GOOGLE_TOKEN, "scope": "openid email profile"},
        "microsoft": {"label": "Microsoft 365", "client_id": os.getenv("MICROSOFT_CLIENT_ID", ""), "client_secret": os.getenv("MICROSOFT_CLIENT_SECRET", ""), "authorize": MICROSOFT_AUTHORIZE, "token": MICROSOFT_TOKEN, "scope": "openid profile email User.Read"},
    }

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if request.session.get("user"):
        return RedirectResponse("/", status_code=303)
    buttons = []
    message = {"pending_approval": "Tài khoản đã ghi nhận và đang chờ admin duyệt.", "rejected": "Tài khoản chưa được admin cho phép.", "oauth_failed": "Đăng nhập OAuth thất bại."}.get(request.query_params.get("error", ""), "")
    if message:
        buttons.append(f'<p class="login-error">{message}</p>')
    for key, provider in _providers().items():
        if provider["client_id"] and provider["client_secret"]:
            buttons.append(f'<a class="login-button {key}" href="/auth/{key}/start">Đăng nhập với {provider["label"]}</a>')
    if not buttons:
        buttons.append('<p class="login-error">Chưa cấu hình OAuth. Hãy khai báo GOOGLE_CLIENT_ID/SECRET hoặc MICROSOFT_CLIENT_ID/SECRET.</p>')
    return HTMLResponse(f'''<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Đăng nhập</title><style>body{{font-family:system-ui,sans-serif;background:#f4f6f8;display:grid;place-items:center;min-height:100vh;margin:0}}main{{background:#fff;padding:32px;max-width:420px;width:calc(100% - 48px);border-radius:14px;box-shadow:0 8px 30px #0001;text-align:center}}h1{{font-size:24px}}.login-button{{display:block;padding:12px 16px;margin:12px 0;border-radius:8px;color:#fff;text-decoration:none;font-weight:600}}.google{{background:#4285f4}}.microsoft{{background:#2563eb}}.login-error{{color:#b42318;text-align:left;background:#fef3f2;padding:12px;border-radius:8px}}</style></head><body><main><h1>Company Crawl Platform</h1><p>Đăng nhập để tiếp tục</p>{''.join(buttons)}</main></body></html>''')

@router.get("/auth/{provider}/start")
def auth_start(provider: str, request: Request):
    config = _providers().get(provider)
    if not config or not config["client_id"] or not config["client_secret"]:
        return RedirectResponse("/login?error=provider_not_configured", status_code=303)
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state
    params = {"client_id": config["client_id"], "response_type": "code", "redirect_uri": f"{_base_url(request)}/auth/{provider}/callback", "scope": config["scope"], "state": state}
    if provider == "google":
        params.update({"access_type": "online", "prompt": "select_account"})
    return RedirectResponse(f'{config["authorize"]}?{urlencode(params)}', status_code=307)

@router.get("/auth/{provider}/callback")
async def auth_callback(provider: str, request: Request, code: str = "", state: str = "", error: str = ""):
    config = _providers().get(provider)
    expected = request.session.pop("oauth_state", "")
    if error or not config or not expected or not secrets.compare_digest(state, expected) or not code:
        return RedirectResponse("/login?error=oauth_failed", status_code=303)
    redirect_uri = f"{_base_url(request)}/auth/{provider}/callback"
    async with httpx.AsyncClient(timeout=15) as client:
        token_response = await client.post(config["token"], data={"client_id": config["client_id"], "client_secret": config["client_secret"], "code": code, "grant_type": "authorization_code", "redirect_uri": redirect_uri})
        if token_response.status_code >= 400:
            return RedirectResponse("/login?error=token_failed", status_code=303)
        token = token_response.json().get("access_token")
        if not token:
            return RedirectResponse("/login?error=missing_token", status_code=303)
        profile_url = "https://openidconnect.googleapis.com/v1/userinfo" if provider == "google" else "https://graph.microsoft.com/oidc/userinfo"
        profile_response = await client.get(profile_url, headers={"Authorization": f"Bearer {token}"})
        if profile_response.status_code >= 400:
            return RedirectResponse("/login?error=profile_failed", status_code=303)
    profile = profile_response.json()
    email = (profile.get("email", "") or "").strip().lower()
    if not email:
        return RedirectResponse("/login?error=missing_email", status_code=303)
    with next(get_db(request)) as db:
        user = db.query(AppUser).filter(AppUser.email == email).first()
        is_admin = email in ADMIN_EMAILS
        if not user:
            user = AppUser(email=email, name=profile.get("name", ""), provider=provider, subject=profile.get("sub", ""), status="approved" if is_admin else "pending", is_admin=1 if is_admin else 0)
            db.add(user)
        else:
            user.name = profile.get("name", "") or user.name
            user.provider, user.subject = provider, profile.get("sub", "")
            if is_admin:
                user.status, user.is_admin = "approved", 1
        db.commit()
        if user.status != "approved":
            return RedirectResponse("/login?error=pending_approval", status_code=303)
        admin = bool(user.is_admin)
    request.session["user"] = {"provider": provider, "subject": profile.get("sub", ""), "email": email, "name": profile.get("name", ""), "is_admin": admin}
    return RedirectResponse("/", status_code=303)

@router.get("/api/auth/me")
def current_user(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(401, "Chưa đăng nhập.")
    return user

@router.get("/api/auth/users")
def list_users(request: Request, db: Session = Depends(get_db)):
    if not _is_admin(request):
        raise HTTPException(403, "Chỉ admin được phép.")
    return [{"id": x.id, "email": x.email, "name": x.name, "status": x.status, "is_admin": bool(x.is_admin), "created_at": x.created_at} for x in db.query(AppUser).order_by(AppUser.id.desc()).all()]

@router.patch("/api/auth/users/{user_id}")
def approve_user(user_id: int, request: Request, status: str, db: Session = Depends(get_db)):
    if not _is_admin(request):
        raise HTTPException(403, "Chỉ admin được phép.")
    if status not in {"approved", "rejected", "pending"}:
        raise HTTPException(400, "Trạng thái không hợp lệ.")
    user = db.get(AppUser, user_id)
    if not user:
        raise HTTPException(404, "Không tìm thấy user.")
    if user.email in ADMIN_EMAILS and status != "approved":
        raise HTTPException(400, "Không thể khóa admin mặc định.")
    user.status = status
    db.commit()
    return {"ok": True, "status": status}

@router.post("/auth/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
