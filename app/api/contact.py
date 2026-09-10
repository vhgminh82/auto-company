from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from urllib.parse import urlparse

from app.contact_forms import detect_captcha_from_page, inspect_url
from app.fetchers.browser_fetcher import BrowserFetcher

router = APIRouter(prefix="/api/contact", tags=["contact"])


class InspectRequest(BaseModel):
    url: str = Field(min_length=3, max_length=2048)


class SubmitRequest(BaseModel):
    page_url: str
    action: str
    fields: dict[str, str]
    form_index: int = 0
    confirm: bool = False


@router.post("/inspect")
async def inspect_contact(request: InspectRequest):
    return await inspect_url(request.url)


@router.post("/submit")
async def submit_contact(request: SubmitRequest):
    print(f"[contact] submit requested page={request.page_url} form_index={request.form_index}", flush=True)
    if not request.confirm:
        print("[contact] stopped: confirmation missing", flush=True)
        raise HTTPException(400, "Cần xác nhận trước khi gửi.")
    parsed_page = urlparse(request.page_url)
    parsed_action = urlparse(request.action)
    if parsed_page.scheme not in {"http", "https"} or parsed_action.scheme not in {"http", "https"}:
        print("[contact] stopped: invalid URL", flush=True)
        raise HTTPException(400, "URL không hợp lệ.")
    if (parsed_page.hostname or "").lower().lstrip("www.") != (parsed_action.hostname or "").lower().lstrip("www."):
        print("[contact] stopped: cross-domain action", flush=True)
        raise HTTPException(400, "Từ chối gửi tới domain khác domain của trang.")
    try:
        from playwright.async_api import async_playwright
    except Exception:
        print("[contact] stopped: Playwright unavailable", flush=True)
        raise HTTPException(503, "Chưa cài Playwright/browser.")
    async with async_playwright() as pw:
        print("[contact] launching browser", flush=True)
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            print(f"[contact] opening {request.page_url}", flush=True)
            await page.goto(request.page_url, wait_until="domcontentloaded", timeout=30000)
            forms = page.locator("form")
            if request.form_index < 0 or request.form_index >= await forms.count():
                print("[contact] stopped: form index not found", flush=True)
                raise HTTPException(404, "Không tìm thấy form.")
            target = forms.nth(request.form_index)
            if detect_captcha_from_page(await target.inner_html()):
                print("[contact] stopped: CAPTCHA detected in selected form", flush=True)
                raise HTTPException(409, "Phát hiện CAPTCHA; cần thao tác thủ công.")
            print(f"[contact] filling {len(request.fields)} fields", flush=True)
            for name, value in request.fields.items():
                locator = target.locator(f"[name={name!r}]")
                if await locator.count():
                    element = locator.first
                    tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                    if tag_name == "select":
                        await element.select_option(value)
                    else:
                        await element.fill(value)
                    print(f"[contact] filled field: {name}", flush=True)
                else:
                    print(f"[contact] field not found, skipped: {name}", flush=True)
            print("[contact] clicking submit", flush=True)
            await target.locator("button[type=submit], input[type=submit]").first.click(timeout=10000)
            await page.wait_for_timeout(1200)
            print(f"[contact] submitted; final_url={page.url}", flush=True)
            return {"ok": True, "message": "Đã gửi form.", "final_url": page.url}
        finally:
            await browser.close()
