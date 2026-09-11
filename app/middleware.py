from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, RedirectResponse

class LoginRequiredMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path.startswith("/auth/") or request.url.path == "/login" or request.url.path.startswith("/static/"):
            return await call_next(request)
        if not request.session.get("user"):
            if request.url.path.startswith("/api/"):
                return JSONResponse({"detail": "Bạn cần đăng nhập."}, status_code=401)
            return RedirectResponse("/login", status_code=303)
        return await call_next(request)