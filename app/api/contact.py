from __future__ import annotations

import re
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.contact_forms import detect_captcha_from_page, inspect_url

router = APIRouter(prefix="/api/contact", tags=["contact"])


class InspectRequest(BaseModel):
    url: str = Field(min_length=3, max_length=2048)


class SubmitRequest(BaseModel):
    page_url: str
    action: str
    fields: dict[str, str]
    form_index: int = 0
    confirm: bool = False


COOKIE_WORDS = re.compile(r"accept|agree|allow|got it|ok|dismiss|consent|đồng ý|chấp nhận|cho phép|aceptar|accepter|akzeptieren", re.I)
COOKIE_AREA_WORDS = re.compile(r"cookie|consent|privacy|gdpr", re.I)
LEGAL_WORDS = re.compile(r"agree|consent|terms|privacy|policy|đồng ý|điều khoản|chính sách", re.I)


async def _dismiss_cookie_banners(page) -> list[str]:
    dismissed = []
    candidates = page.locator("button, a, input[type=button], input[type=submit]")
    for index in range(min(await candidates.count(), 80)):
        candidate = candidates.nth(index)
        try:
            text = ((await candidate.inner_text()) or (await candidate.get_attribute("value")) or "").strip()
            aria = (await candidate.get_attribute("aria-label") or "").strip()
            identifier = " ".join([(await candidate.get_attribute("id") or ""), (await candidate.get_attribute("class") or "")])
            context = f"{text} {aria} {identifier}"
            if text and COOKIE_WORDS.search(text) and COOKIE_AREA_WORDS.search(context):
                await candidate.click(timeout=1500)
                dismissed.append(text[:80])
                break
        except Exception:
            continue
    return dismissed


async def _required_fields_missing(target, supplied: dict[str, str]) -> list[str]:
    missing = []
    controls = target.locator("input, textarea, select")
    for index in range(await controls.count()):
        control = controls.nth(index)
        try:
            if not await control.is_visible() or not await control.is_required():
                continue
            name = await control.get_attribute("name") or await control.get_attribute("id") or f"field_{index + 1}"
            field_type = (await control.get_attribute("type") or "text").lower()
            if field_type in {"checkbox", "radio"}:
                if not await control.is_checked():
                    label = (await control.get_attribute("aria-label") or name).strip()
                    missing.append(f"{name} (checkbox bắt buộc: {label})")
                continue
            if name not in supplied or not str(supplied.get(name, "")).strip():
                label = (await control.get_attribute("aria-label") or await control.get_attribute("placeholder") or name).strip()
                missing.append(f"{name} ({label})")
        except Exception:
            continue
    return missing


@router.post("/inspect")
async def inspect_contact(request: InspectRequest):
    return await inspect_url(request.url)


@router.post("/submit")
async def submit_contact(request: SubmitRequest):
    print(f"[contact] submit requested page={request.page_url} form_index={request.form_index}", flush=True)
    if not request.confirm:
        raise HTTPException(400, "Bước xác nhận: chưa xác nhận gửi.")
    parsed_page = urlparse(request.page_url)
    parsed_action = urlparse(request.action)
    if parsed_page.scheme not in {"http", "https"} or parsed_action.scheme not in {"http", "https"}:
        raise HTTPException(400, "Bước kiểm tra URL: URL không hợp lệ.")
    if (parsed_page.hostname or "").lower().lstrip("www.") != (parsed_action.hostname or "").lower().lstrip("www."):
        raise HTTPException(400, "Bước bảo mật: form gửi tới domain khác domain của trang.")
    try:
        from playwright.async_api import async_playwright
    except Exception as exc:
        raise HTTPException(503, f"Bước khởi tạo trình duyệt: {exc}") from exc

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            try:
                await page.goto(request.page_url, wait_until="domcontentloaded", timeout=30000)
                dismissed = await _dismiss_cookie_banners(page)
                if dismissed:
                    print(f"[contact] cookie banner dismissed: {dismissed}", flush=True)
            except Exception as exc:
                raise HTTPException(504, f"Bước mở trang: {str(exc)[:260]}") from exc

            forms = page.locator("form")
            if request.form_index < 0 or request.form_index >= await forms.count():
                raise HTTPException(404, f"Bước tìm form: không tìm thấy form số {request.form_index + 1}.")
            target = forms.nth(request.form_index)
            try:
                if detect_captcha_from_page(await target.inner_html()):
                    raise HTTPException(409, "Bước kiểm tra form: phát hiện CAPTCHA.")
            except HTTPException:
                raise
            except Exception as exc:
                raise HTTPException(422, f"Bước đọc form: {str(exc)[:260]}") from exc

            missing = await _required_fields_missing(target, request.fields)
            if missing:
                raise HTTPException(422, "Bước kiểm tra trường bắt buộc: thiếu " + "; ".join(missing[:12]))

            try:
                for name, value in request.fields.items():
                    locator = target.locator(f"[name={name!r}]")
                    if not await locator.count():
                        print(f"[contact] optional field not found, skipped: {name}", flush=True)
                        continue
                    element = locator.first
                    field_type = (await element.get_attribute("type") or "").lower()
                    if field_type in {"checkbox", "radio"}:
                        if str(value).strip().lower() in {"1", "true", "yes", "on", "x"}:
                            await element.check()
                    elif (await element.evaluate("el => el.tagName.toLowerCase()")) == "select":
                        await element.select_option(str(value))
                    else:
                        await element.fill(str(value))
            except Exception as exc:
                raise HTTPException(422, f"Bước điền form: {str(exc)[:260]}") from exc

            submitter = target.locator("button[type=submit], button:not([type]), input[type=submit]")
            if await submitter.count() == 0:
                raise HTTPException(422, "Bước gửi form: không tìm thấy nút gửi.")
            try:
                await submitter.first.click(timeout=10000)
                await page.wait_for_timeout(1200)
            except Exception as exc:
                raise HTTPException(422, f"Bước click nút gửi: {str(exc)[:260]}") from exc
            return {"ok": True, "message": "Đã gửi form.", "final_url": page.url, "cookie_dismissed": dismissed}
        finally:
            await browser.close()
