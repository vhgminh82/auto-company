from __future__ import annotations

import json
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai_service import OpenRouterError, chat_completion, configured_models
from app.database import get_db
from app.models.company import Company
from app.models.emkt import SesAccount
from app.models.ai import AISetting

router = APIRouter(prefix="/api/ai", tags=["ai"])


class CompanyAnalysisRequest(BaseModel):
    company_id: int
    language: str = Field(default="vi", min_length=2, max_length=10)


DEFAULT_MODELS = configured_models()


class AISettingsRequest(BaseModel):
    primary_model: str = Field(default="", max_length=255)
    fallback_model_1: str = Field(default="", max_length=255)
    fallback_model_2: str = Field(default="", max_length=255)


class AITestRequest(BaseModel):
    model: str = Field(min_length=1, max_length=255)


class ContactGenerateRequest(BaseModel):
    description: str = Field(min_length=1, max_length=10000)
    reference_website: str = Field(default="", max_length=2000)
    language: str = Field(default="vi", min_length=2, max_length=10)


class CampaignGenerateRequest(ContactGenerateRequest):
    account_ids: list[int] = Field(default_factory=list, max_length=100)


def _admin(request: Request) -> None:
    if not request.session.get("user", {}).get("is_admin"):
        raise HTTPException(403, "Chỉ admin được sử dụng AI.")


def _settings(db: Session) -> AISetting:
    item = db.get(AISetting, 1)
    if not item:
        item = AISetting(id=1)
        db.add(item)
        db.commit()
        db.refresh(item)
    return item


def _models(db: Session) -> list[str]:
    item = _settings(db)
    defaults = configured_models()
    return list(dict.fromkeys([
        (item.primary_model or defaults[0]).strip(),
        (item.fallback_model_1 or defaults[1]).strip(),
        (item.fallback_model_2 or defaults[2]).strip(),
    ]))


async def _json_completion(messages: list[dict[str, str]], models: list[str]) -> dict:
    errors = []
    for model in models:
        try:
            raw = await chat_completion(messages, model=model)
            cleaned = raw.strip().removeprefix("```json").removesuffix("```").strip()
            return json.loads(cleaned)
        except (OpenRouterError, json.JSONDecodeError, TypeError, ValueError) as exc:
            errors.append(f"{model}: {exc}")
    raise OpenRouterError("Không tạo được dữ liệu AI: " + " | ".join(errors))


@router.get("/settings")
def get_ai_settings(request: Request, db: Session = Depends(get_db)):
    _admin(request)
    item = _settings(db)
    defaults = configured_models()
    return {
        "primary_model": item.primary_model,
        "fallback_model_1": item.fallback_model_1,
        "fallback_model_2": item.fallback_model_2,
        "defaults": {"primary_model": defaults[0], "fallback_model_1": defaults[1], "fallback_model_2": defaults[2]},
        "configured_models": _models(db),
        "has_api_key": bool(os.getenv("OPENROUTER_API_KEY", "").strip()),
    }


@router.put("/settings")
def save_ai_settings(payload: AISettingsRequest, request: Request, db: Session = Depends(get_db)):
    _admin(request)
    item = _settings(db)
    item.primary_model = payload.primary_model.strip()
    item.fallback_model_1 = payload.fallback_model_1.strip()
    item.fallback_model_2 = payload.fallback_model_2.strip()
    db.commit()
    return get_ai_settings(request, db)


@router.post("/test")
async def test_ai_model(payload: AITestRequest, request: Request):
    _admin(request)
    try:
        result = await chat_completion(
            [{"role": "user", "content": "Reply with exactly OK."}], model=payload.model.strip()
        )
    except OpenRouterError as exc:
        raise HTTPException(503, str(exc)) from exc
    return {"model": payload.model.strip(), "ok": True, "response": result}


@router.post("/contact-generate")
async def generate_contact(payload: ContactGenerateRequest, request: Request, db: Session = Depends(get_db)):
    _admin(request)
    prompt = f"""Tạo dữ liệu điền form liên hệ từ mô tả và website tham chiếu.
Chỉ trả về JSON object với các key: name, company, email, phone, subject, website, address, message, custom_fields.
Giá trị không suy ra được để chuỗi rỗng; custom_fields là object. Không bịa email, số điện thoại hay địa chỉ.
Ngôn ngữ: {payload.language}.
Mô tả: {payload.description}
Website tham chiếu: {payload.reference_website or 'không có'}"""
    try:
        result = await _json_completion([{"role": "system", "content": "Bạn là trợ lý tạo nội dung contact B2B."}, {"role": "user", "content": prompt}], _models(db))
    except OpenRouterError as exc:
        raise HTTPException(503, str(exc)) from exc
    return {"fields": result}


@router.post("/campaign-generate")
async def generate_campaign(payload: CampaignGenerateRequest, request: Request, db: Session = Depends(get_db)):
    _admin(request)
    accounts = db.query(SesAccount).filter(SesAccount.enabled == 1).order_by(SesAccount.id).all()
    accounts = [account for account in accounts if not payload.account_ids or account.id in payload.account_ids]
    account_data = [{"id": account.id, "name": account.name, "from_email": account.from_email} for account in accounts]
    prompt = f"""Tạo campaign email B2B từ mô tả và website tham chiếu.
Chỉ trả về JSON object với key account_id, subject, html_body, text_body.
account_id phải là một id trong danh sách tài khoản; nếu danh sách rỗng trả về null.
Dùng placeholder {{company_name}} và {{website}} khi phù hợp. Không bịa thông tin doanh nghiệp.
Ngôn ngữ: {payload.language}.
Mô tả: {payload.description}
Website tham chiếu: {payload.reference_website or 'không có'}
Tài khoản hợp lệ: {json.dumps(account_data, ensure_ascii=False)}"""
    try:
        result = await _json_completion([{"role": "system", "content": "Bạn là chuyên viên viết email marketing B2B."}, {"role": "user", "content": prompt}], _models(db))
    except OpenRouterError as exc:
        raise HTTPException(503, str(exc)) from exc
    valid_ids = {account["id"] for account in account_data}
    if result.get("account_id") not in valid_ids:
        result["account_id"] = None
    return {"campaign": result}


@router.post("/company-analysis")
async def company_analysis(
    payload: CompanyAnalysisRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    if not request.session.get("user", {}).get("is_admin"):
        raise HTTPException(403, "Chỉ admin được sử dụng AI.")

    company = db.get(Company, payload.company_id)
    if not company:
        raise HTTPException(404, "Không tìm thấy doanh nghiệp.")

    company_data = "\n".join(
        [
            f"Tên: {company.name}",
            f"Ngành: {company.industry}",
            f"Mô tả: {company.short_description}",
            f"Địa chỉ: {company.address}, {company.city}, {company.state}, {company.country}",
            f"Website: {company.website}",
        ]
    )
    prompt = (
        "Phân tích doanh nghiệp dưới đây cho nhân viên kinh doanh. "
        "Trả về ngắn gọn theo các mục: tóm tắt, sản phẩm/dịch vụ có thể suy ra, "
        "khách hàng mục tiêu, 3 góc tiếp cận bán hàng và mức độ tin cậy của suy luận. "
        f"Viết bằng ngôn ngữ mã '{payload.language}'. Chỉ dùng dữ liệu được cung cấp "
        "và ghi rõ phần nào là suy luận.\n\n"
        + company_data
    )

    try:
        analysis = await chat_completion(
            [
                {
                    "role": "system",
                    "content": "Bạn là chuyên viên phân tích B2B, trung thực và không bịa dữ liệu.",
                },
                {"role": "user", "content": prompt},
            ]
        )
    except OpenRouterError as exc:
        raise HTTPException(503, str(exc)) from exc

    return {"company_id": company.id, "model": "openrouter", "analysis": analysis}