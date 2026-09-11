from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from cryptography.fernet import InvalidToken

from app.database import get_db
from app.emkt_service import collect_recipients, encrypt_secret, send_test_email, start_campaign, stop_campaign, test_account
from app.models.emkt import EmktCampaign, EmktCampaignRun, EmktRecipient, SesAccount


router = APIRouter(prefix="/api/emkt", tags=["emkt"])


class AccountRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    smtp_host: str = Field(default="email-smtp.us-east-1.amazonaws.com", min_length=3, max_length=255)
    smtp_port: int = Field(default=465, ge=1, le=65535)
    smtp_security: str = Field(default="ssl", pattern="^(ssl|starttls|none)$")
    smtp_username: str = Field(default="", max_length=512)
    smtp_password: str = Field(default="", max_length=1024)
    from_email: str = Field(min_length=3, max_length=255)
    from_name: str = Field(default="", max_length=255)
    configuration_set: str = Field(default="", max_length=255)
    region: str = Field(default="us-west-2", min_length=1, max_length=64)
    access_key_id: str = Field(default="", max_length=512)
    secret_access_key: str = Field(default="", max_length=1024)


class CampaignRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    account_id: int
    subject: str = Field(min_length=1, max_length=500)
    html_body: str = Field(default="", max_length=1_000_000)
    text_body: str = Field(default="", max_length=1_000_000)
    country_filter: str = Field(default="", max_length=128)
    industry_filter: str = Field(default="", max_length=128)
    query_filter: str = Field(default="", max_length=255)
    list_ids: list[int] = Field(default_factory=list, max_length=500)
    recipient_limit: int = Field(default=500, ge=1, le=50_000)
    scheduled_at: str | None = None


def _scheduled_value(value: str | None):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(400, "Thời gian gửi không hợp lệ.") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
    return parsed.astimezone(timezone.utc)


def _apply_campaign(item: EmktCampaign, request: CampaignRequest) -> None:
    values = request.model_dump()
    values["list_ids"] = json.dumps(sorted(set(request.list_ids)))
    values.pop("list_ids", None)
    for key, value in request.model_dump().items():
        if key != "list_ids":
            setattr(item, key, value)
    item.list_ids = json.dumps(sorted(set(request.list_ids)))


class StartRequest(BaseModel):
    confirm: bool = False


class TestEmailRequest(BaseModel):
    to_email: str = Field(min_length=3, max_length=255)
    subject: str = Field(default="Email kiểm tra SMTP AWS SES", max_length=500)
    body: str = Field(default="Đây là email kiểm tra kết nối SMTP AWS SES.", max_length=10000)


def account_out(item: SesAccount) -> dict:
    from app.emkt_service import decrypt_secret
    try:
        smtp_username = decrypt_secret(item.smtp_username)
    except InvalidToken:
        # Credentials created with a previous encryption key cannot be recovered.
        # Keep the account list usable so the admin can replace them.
        smtp_username = ""
    try:
        access_key_id = decrypt_secret(item.access_key_id)
    except InvalidToken:
        access_key_id = ""
    return {
        "id": item.id, "name": item.name, "smtp_host": item.smtp_host, "smtp_port": item.smtp_port,
        "smtp_security": item.smtp_security, "smtp_username": smtp_username,
        "region": item.region, "access_key_id": access_key_id,
        "from_email": item.from_email, "from_name": item.from_name,
        "configuration_set": item.configuration_set,
        "enabled": bool(item.enabled), "has_credentials": bool(item.smtp_username and item.smtp_password),
    }


def campaign_out(item: EmktCampaign, db: Session | None = None) -> dict:
    try:
        list_ids = [int(value) for value in json.loads(item.list_ids or "[]")]
    except (TypeError, ValueError, json.JSONDecodeError):
        list_ids = []
    account = db.get(SesAccount, item.account_id) if db else None
    return {
        "id": item.id, "name": item.name, "account_id": item.account_id,
        "account_name": account.name if account else "Chưa xác định",
        "subject": item.subject,
        "html_body": item.html_body, "text_body": item.text_body, "country_filter": item.country_filter,
        "industry_filter": item.industry_filter, "query_filter": item.query_filter,
        "list_ids": list_ids,
        "scheduled_at": item.scheduled_at,
        "recipient_limit": item.recipient_limit, "status": item.status, "total": item.total,
        "sent": item.sent, "failed": item.failed, "pending": max(0, item.total - item.sent - item.failed),
        "created_at": item.created_at,
        "started_at": item.started_at, "completed_at": item.completed_at,
    }


def run_out(item: EmktCampaignRun) -> dict:
    return {"id": item.id, "started_at": item.started_at, "completed_at": item.completed_at, "status": item.status, "total": item.total, "sent": item.sent, "failed": item.failed, "pending": max(0, item.total - item.sent - item.failed)}


@router.get("/accounts")
def list_accounts(db: Session = Depends(get_db)):
    return [account_out(item) for item in db.query(SesAccount).order_by(SesAccount.id).all()]


@router.post("/accounts")
def create_account(request: AccountRequest, db: Session = Depends(get_db)):
    if not request.access_key_id.strip() or not request.secret_access_key:
        if not request.smtp_username.strip() or not request.smtp_password:
            raise HTTPException(422, "Cần nhập IAM Access Key ID và Secret Access Key để dùng SES API.")
    name = request.name.strip()
    item = db.query(SesAccount).filter(SesAccount.name == name).first()
    if not item:
        item = SesAccount(name=name, region=request.region.strip(), enabled=1)
        db.add(item)
    item.region = request.region.strip()
    item.access_key_id = encrypt_secret(request.access_key_id.strip()) if request.access_key_id.strip() else ""
    item.secret_access_key = encrypt_secret(request.secret_access_key) if request.secret_access_key else ""
    item.smtp_host = request.smtp_host.strip()
    item.smtp_port = request.smtp_port
    item.smtp_security = request.smtp_security
    item.smtp_username = encrypt_secret(request.smtp_username.strip())
    item.smtp_password = encrypt_secret(request.smtp_password)
    item.from_email = request.from_email.strip()
    item.from_name = request.from_name.strip()
    item.configuration_set = request.configuration_set.strip()
    item.enabled = 1
    try:
        db.commit(); db.refresh(item)
    except Exception as exc:
        db.rollback()
        raise HTTPException(400, f"Không lưu được tài khoản: {exc}") from exc
    return account_out(item)


@router.delete("/accounts/{account_id}")
def delete_account(account_id: int, db: Session = Depends(get_db)):
    if db.query(EmktCampaign).filter(EmktCampaign.account_id == account_id).first():
        raise HTTPException(400, "Tài khoản đã được dùng trong chiến dịch, không thể xóa.")
    item = db.get(SesAccount, account_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy tài khoản.")
    db.delete(item); db.commit()
    return {"deleted": account_id}

@router.put("/accounts/{account_id}")
def update_account(account_id: int, request: AccountRequest, db: Session = Depends(get_db)):
    item = db.get(SesAccount, account_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy tài khoản SES.")
    item.name = request.name.strip()
    item.region = request.region.strip()
    if request.access_key_id.strip():
        item.access_key_id = encrypt_secret(request.access_key_id.strip())
    if request.secret_access_key:
        item.secret_access_key = encrypt_secret(request.secret_access_key)
    item.smtp_host = request.smtp_host.strip()
    item.smtp_port = request.smtp_port
    item.smtp_security = request.smtp_security
    if request.smtp_username.strip():
        item.smtp_username = encrypt_secret(request.smtp_username.strip())
    if request.smtp_password:
        item.smtp_password = encrypt_secret(request.smtp_password)
    item.from_email = request.from_email.strip()
    item.from_name = request.from_name.strip()
    item.configuration_set = request.configuration_set.strip()
    try:
        db.commit(); db.refresh(item)
    except Exception as exc:
        db.rollback()
        raise HTTPException(400, f"Không cập nhật được tài khoản: {exc}") from exc
    return account_out(item)


@router.post("/accounts/{account_id}/test")
def check_account(account_id: int, db: Session = Depends(get_db)):
    item = db.get(SesAccount, account_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy tài khoản.")
    try:
        return test_account(item)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/accounts/{account_id}/send-test")
def send_test(account_id: int, request: TestEmailRequest, db: Session = Depends(get_db)):
    item = db.get(SesAccount, account_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy tài khoản SES.")
    try:
        message_id = send_test_email(item, request.to_email.strip(), request.subject, request.body)
        return {"sent": True, "message_id": message_id, "to_email": request.to_email.strip()}
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/campaigns")
def list_campaigns(db: Session = Depends(get_db)):
    return [campaign_out(item, db) for item in db.query(EmktCampaign).order_by(EmktCampaign.id.desc()).all()]


@router.get("/stats")
def emkt_stats(period: str = "all", start: str | None = None, end: str | None = None, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    if period == "day":
        since = now.replace(hour=0, minute=0, second=0, microsecond=0)
        until = now
    elif period == "week":
        since = (now - __import__("datetime").timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        until = now
    elif period == "month":
        since = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        until = now
    elif period == "year":
        since = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        until = now
    elif period == "custom":
        since = _scheduled_value(start) if start else None
        until = _scheduled_value(end) if end else now
        if since and end and len(end) == 10:
            until = datetime.fromisoformat(end).replace(hour=23, minute=59, second=59, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh")).astimezone(timezone.utc)
    else:
        since, until = None, now

    def in_range(value):
        if not value:
            return False
        value = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
        return (since is None or value >= since) and value <= until

    campaigns = db.query(EmktCampaign).all()
    recipients = db.query(EmktRecipient).all()
    selected = [row for row in recipients if in_range(row.sent_at or row.delivered_at or row.bounced_at or row.complained_at or row.opened_at or row.clicked_at)] if period != "all" else recipients
    campaign_ids = {row.campaign_id for row in selected}
    campaign_rows = []
    for campaign in campaigns:
        rows = [row for row in selected if row.campaign_id == campaign.id]
        if not rows and period != "all":
            continue
        campaign_rows.append({"id": campaign.id, "name": campaign.name, "sent": sum(row.status == "sent" for row in rows), "failed": sum(row.status == "failed" for row in rows), "delivered": sum(bool(row.delivered_at) for row in rows), "bounced": sum(bool(row.bounced_at) for row in rows), "complained": sum(bool(row.complained_at) for row in rows), "opened": sum(bool(row.opened_at) for row in rows), "clicked": sum(bool(row.clicked_at) for row in rows), "total": len(rows)})
    total = len(selected)
    sent = sum(row.status == "sent" for row in selected)
    result = {"period": period, "from": since, "to": until, "campaigns": len(campaign_rows), "total": total, "sent": sent, "failed": sum(row.status == "failed" for row in selected), "pending": sum(row.status == "pending" for row in selected), "delivered": sum(bool(row.delivered_at) for row in selected), "bounced": sum(bool(row.bounced_at) for row in selected), "complained": sum(bool(row.complained_at) for row in selected), "opened": sum(bool(row.opened_at) for row in selected), "clicked": sum(bool(row.clicked_at) for row in selected), "campaign_rows": campaign_rows}
    result["delivery_rate"] = round(result["delivered"] / sent * 100, 1) if sent else 0
    result["open_rate"] = round(result["opened"] / sent * 100, 1) if sent else 0
    result["click_rate"] = round(result["clicked"] / sent * 100, 1) if sent else 0
    result["bounce_rate"] = round(result["bounced"] / sent * 100, 1) if sent else 0
    return result


@router.post("/campaigns")
def create_campaign(request: CampaignRequest, db: Session = Depends(get_db)):
    if not request.html_body.strip() and not request.text_body.strip():
        raise HTTPException(400, "Cần nội dung HTML hoặc văn bản.")
    if not db.get(SesAccount, request.account_id):
        raise HTTPException(404, "Không tìm thấy tài khoản SES.")
    values = request.model_dump()
    values["scheduled_at"] = _scheduled_value(request.scheduled_at)
    values["list_ids"] = json.dumps(sorted(set(request.list_ids)))
    item = EmktCampaign(**values, status="scheduled" if values["scheduled_at"] else "draft")
    db.add(item); db.commit(); db.refresh(item)
    return campaign_out(item, db)


@router.put("/campaigns/{campaign_id}")
def update_campaign(campaign_id: int, request: CampaignRequest, db: Session = Depends(get_db)):
    item = db.get(EmktCampaign, campaign_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy chiến dịch.")
    if item.status in {"sending", "queued"}:
        raise HTTPException(400, "Không thể sửa campaign đang chạy.")
    if not request.html_body.strip() and not request.text_body.strip():
        raise HTTPException(400, "Cần nội dung HTML hoặc văn bản.")
    if not db.get(SesAccount, request.account_id):
        raise HTTPException(404, "Không tìm thấy tài khoản SES.")
    _apply_campaign(item, request)
    item.scheduled_at = _scheduled_value(request.scheduled_at)
    item.status = "scheduled" if item.scheduled_at else "draft"; item.total = 0; item.sent = 0; item.failed = 0
    db.commit(); db.refresh(item)
    return campaign_out(item, db)


@router.get("/campaigns/{campaign_id}")
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    item = db.get(EmktCampaign, campaign_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy chiến dịch.")
    result = campaign_out(item, db)
    result["recent_errors"] = [
        {"email": row.email, "error": row.error}
        for row in db.query(EmktRecipient).filter(EmktRecipient.campaign_id == campaign_id, EmktRecipient.status == "failed").order_by(EmktRecipient.id.desc()).limit(10)
    ]
    return result


@router.delete("/campaigns/{campaign_id}")
def delete_campaign(campaign_id: int, db: Session = Depends(get_db)):
    item = db.get(EmktCampaign, campaign_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy chiến dịch.")
    if item.status in {"sending", "queued"}:
        raise HTTPException(400, "Không thể xóa campaign đang chạy.")
    db.query(EmktRecipient).filter(EmktRecipient.campaign_id == campaign_id).delete(synchronize_session=False)
    db.delete(item)
    db.commit()
    return {"deleted": campaign_id}


@router.get("/campaigns/{campaign_id}/history")
def campaign_history(campaign_id: int, db: Session = Depends(get_db)):
    if not db.get(EmktCampaign, campaign_id):
        raise HTTPException(404, "Không tìm thấy chiến dịch.")
    return [run_out(item) for item in db.query(EmktCampaignRun).filter(EmktCampaignRun.campaign_id == campaign_id).order_by(EmktCampaignRun.id.desc()).all()]


@router.get("/campaigns/{campaign_id}/recipients-preview")
def preview_recipients(campaign_id: int, db: Session = Depends(get_db)):
    item = db.get(EmktCampaign, campaign_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy chiến dịch.")
    all_rows = collect_recipients(db, item)
    return {"total": len(all_rows), "sample": all_rows[:20]}


@router.post("/campaigns/{campaign_id}/start")
def run_campaign(campaign_id: int, request: StartRequest, db: Session = Depends(get_db)):
    if not request.confirm:
        raise HTTPException(400, "Cần xác nhận quyền gửi email cho danh sách này.")
    campaign = db.get(EmktCampaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Không tìm thấy chiến dịch.")
    if campaign.status in {"sending", "queued", "stopping"}:
        return {"started": False, **campaign_out(campaign, db)}
    db.query(EmktRecipient).filter(EmktRecipient.campaign_id == campaign_id).delete(synchronize_session=False)
    recipients = collect_recipients(db, campaign)
    if not recipients:
        raise HTTPException(400, "Bộ lọc không có email hợp lệ.")
    db.bulk_insert_mappings(EmktRecipient, [{"campaign_id": campaign.id, **row, "status": "pending"} for row in recipients])
    run = EmktCampaignRun(campaign_id=campaign.id, status="queued", total=len(recipients))
    db.add(run)
    campaign.total = len(recipients); campaign.sent = 0; campaign.failed = 0; campaign.status = "queued"
    db.commit()
    started = start_campaign(campaign_id, run.id)
    return {"started": started, **campaign_out(campaign, db)}


@router.post("/campaigns/{campaign_id}/stop")
def halt_campaign(campaign_id: int, db: Session = Depends(get_db)):
    stopped = stop_campaign(campaign_id)
    campaign = db.get(EmktCampaign, campaign_id)
    if campaign and stopped:
        campaign.status = "stopping"; db.commit()
    return {"stopped": stopped}


def _scheduled_campaign_worker() -> None:
    from app.database import SessionLocal
    while True:
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            campaigns = db.query(EmktCampaign).filter(
                EmktCampaign.status == "scheduled",
                EmktCampaign.scheduled_at <= now,
            ).order_by(EmktCampaign.id).all()
            for campaign in campaigns:
                try:
                    recipients = collect_recipients(db, campaign)
                    if not recipients:
                        campaign.status = "failed"
                        campaign.completed_at = datetime.now(timezone.utc)
                        db.commit()
                        continue
                    db.bulk_insert_mappings(EmktRecipient, [{"campaign_id": campaign.id, **row, "status": "pending"} for row in recipients])
                    run = EmktCampaignRun(campaign_id=campaign.id, status="queued", total=len(recipients))
                    db.add(run)
                    campaign.total = len(recipients); campaign.sent = 0; campaign.failed = 0; campaign.status = "queued"
                    db.commit()
                    start_campaign(campaign.id, run.id)
                except Exception:
                    db.rollback()
                    campaign = db.get(EmktCampaign, campaign.id)
                    if campaign:
                        campaign.status = "failed"; campaign.completed_at = datetime.now(timezone.utc); db.commit()
        finally:
            db.close()
        time.sleep(5)


threading.Thread(target=_scheduled_campaign_worker, name="emkt-scheduler", daemon=True).start()
