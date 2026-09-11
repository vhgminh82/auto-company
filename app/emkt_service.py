from __future__ import annotations

import html
import json
import re
import smtplib
import ssl
import threading
import time
import os
from urllib.parse import quote
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import make_msgid
from pathlib import Path

from cryptography.fernet import Fernet
from sqlalchemy import or_

from app.database import SessionLocal
from app.models.company import Company
from app.models.emkt import EmktCampaign, EmktCampaignRun, EmktList, EmktListMember, EmktRecipient, SesAccount


ROOT = Path(__file__).resolve().parents[1]
KEY_FILE = ROOT / ".ses_credentials.key"
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_jobs: dict[int, tuple[threading.Thread, threading.Event]] = {}
_jobs_lock = threading.Lock()
campaign_start_lock = threading.Lock()


def _fernet() -> Fernet:
    if not KEY_FILE.exists():
        KEY_FILE.write_bytes(Fernet.generate_key())
    return Fernet(KEY_FILE.read_bytes().strip())


def encrypt_secret(value: str) -> str:
    return _fernet().encrypt(value.encode("utf-8")).decode("ascii") if value else ""


def decrypt_secret(value: str) -> str:
    return _fernet().decrypt(value.encode("ascii")).decode("utf-8") if value else ""


def valid_email(value: str) -> bool:
    value = (value or "").strip().lower()
    return value != "chưa có" and bool(EMAIL_RE.fullmatch(value))


def manual_emails(value: str) -> set[str]:
    return {email.strip().lower() for email in re.split(r"[,;\s]+", value or "") if valid_email(email.strip())}


def recipient_query(db, campaign: EmktCampaign):
    query = db.query(Company).filter(Company.website != "")
    try:
        selected_list_ids = [int(value) for value in json.loads(campaign.list_ids or "[]")]
    except (TypeError, ValueError, json.JSONDecodeError):
        selected_list_ids = []
    if selected_list_ids:
        selected_companies = db.query(EmktListMember.company_id).filter(EmktListMember.list_id.in_(selected_list_ids))
        query = query.filter(Company.id.in_(selected_companies))
    elif not (campaign.country_filter or campaign.industry_filter or campaign.query_filter):
        query = query.filter(Company.id == -1)
    if campaign.country_filter:
        query = query.filter(Company.country.ilike(f"%{campaign.country_filter}%"))
    if campaign.industry_filter:
        query = query.filter(Company.industry.ilike(f"%{campaign.industry_filter}%"))
    if campaign.query_filter:
        term = f"%{campaign.query_filter}%"
        query = query.filter(or_(Company.name.ilike(term), Company.website.ilike(term), Company.short_description.ilike(term)))
    blocked_companies = db.query(EmktListMember.company_id).join(EmktList, EmktList.id == EmktListMember.list_id).filter((EmktList.blacklist == 1) | (EmktListMember.blacklisted == 1))
    query = query.filter(~Company.id.in_(blocked_companies))
    return query.order_by(Company.id)


def blocked_emails(db) -> set[str]:
    values = set()
    for raw in db.query(EmktList.blacklist_emails).all():
        values.update(value.strip().lower() for value in re.split(r"[,;\s]+", raw[0] or "") if valid_email(value.strip()))
    return values


def collect_recipients(db, campaign: EmktCampaign, sample_limit: int | None = None) -> list[dict]:
    results, seen = [], set()
    blocked = blocked_emails(db)
    for company in recipient_query(db, campaign).yield_per(1000):
        for value in (company.email, company.email_2):
            email_value = (value or "").strip().lower()
            if not valid_email(email_value) or email_value in seen or email_value in blocked:
                continue
            seen.add(email_value)
            results.append({"company_id": company.id, "company_name": company.name, "website": company.website, "email": email_value})
            if sample_limit and len(results) >= sample_limit:
                return results
            if campaign.recipient_limit > 0 and len(results) >= campaign.recipient_limit:
                return results
    try:
        selected_list_ids = [int(value) for value in json.loads(campaign.list_ids or "[]")]
    except (TypeError, ValueError, json.JSONDecodeError):
        selected_list_ids = []
    if selected_list_ids:
        lists = db.query(EmktList).filter(EmktList.id.in_(selected_list_ids)).all()
        for item in lists:
            if item.blacklist:
                continue
            for email_value in sorted(manual_emails(item.manual_emails)):
                if email_value in seen or email_value in blocked or email_value in manual_emails(item.blacklist_emails):
                    continue
                seen.add(email_value)
                results.append({"company_id": 0, "company_name": "Email tự thêm", "website": "", "email": email_value})
                if sample_limit and len(results) >= sample_limit:
                    return results
                if campaign.recipient_limit > 0 and len(results) >= campaign.recipient_limit:
                    return results
    return results


def render_template(value: str, recipient: EmktRecipient) -> str:
    replacements = {
        "{{company_name}}": recipient.company_name,
        "{{website}}": recipient.website,
        "{{email}}": recipient.email,
    }
    for key, replacement in replacements.items():
        value = value.replace(key, replacement or "")
    return value


def add_tracking(html_body: str, recipient: EmktRecipient) -> str:
    base = os.getenv("EMKT_PUBLIC_BASE_URL", "").strip().rstrip("/")
    if not base or not html_body:
        return html_body
    pixel = f'<img src="{base}/api/emkt/track/open/{recipient.id}.gif" width="1" height="1" alt="" style="display:none!important">'
    tracked = re.sub(
        r'(?i)(href\s*=\s*["\'])(https?://[^"\']+)(["\'])',
        lambda match: f'{match.group(1)}{base}/api/emkt/track/click/{recipient.id}?url={quote(match.group(2), safe="")}{match.group(3)}',
        html_body,
    )
    return tracked + pixel


def _smtp_connection(account: SesAccount):
    host = (account.smtp_host or "").strip()
    if not host:
        raise RuntimeError("Tài khoản chưa có SMTP host.")
    username = decrypt_secret(account.smtp_username)
    password = decrypt_secret(account.smtp_password)
    if account.smtp_security == "ssl":
        connection = smtplib.SMTP_SSL(host, account.smtp_port, timeout=30, context=ssl.create_default_context())
    else:
        connection = smtplib.SMTP(host, account.smtp_port, timeout=30)
        connection.ehlo()
        if account.smtp_security == "starttls":
            connection.starttls(context=ssl.create_default_context())
            connection.ehlo()
    if username:
        connection.login(username, password)
    return connection


def test_account(account: SesAccount) -> dict:
    connection = _smtp_connection(account)
    try:
        return {"smtp_ok": True, "host": account.smtp_host, "port": account.smtp_port, "security": account.smtp_security}
    finally:
        connection.quit()


def send_test_email(account: SesAccount, to_email: str, subject: str, body: str) -> str:
    sender = f"{account.from_name} <{account.from_email}>" if account.from_name else account.from_email
    message = EmailMessage()
    message["From"], message["To"], message["Subject"] = sender, to_email, subject
    message.set_content(body)
    connection = _smtp_connection(account)
    try:
        connection.send_message(message)
        return str(message.get("Message-ID", ""))
    finally:
        connection.quit()


def _send_one(connection, account: SesAccount, campaign: EmktCampaign, recipient: EmktRecipient) -> str:
    message = EmailMessage()
    sender = f"{account.from_name} <{account.from_email}>" if account.from_name else account.from_email
    message["From"] = sender
    message["To"] = recipient.email
    message["Subject"] = render_template(campaign.subject, recipient)
    message["Message-ID"] = make_msgid()
    text_body = render_template(campaign.text_body, recipient)
    html_body = add_tracking(render_template(campaign.html_body, recipient), recipient)
    if account.configuration_set:
        message["X-SES-CONFIGURATION-SET"] = account.configuration_set.strip()
    if text_body:
        message.set_content(text_body)
    else:
        message.set_content("Vui lòng xem phiên bản HTML của email này.")
    if html_body:
        message.add_alternative(html_body, subtype="html")
    connection.send_message(message)
    return str(message.get("Message-ID", ""))


def _run_campaign(campaign_id: int, run_id: int, stop_event: threading.Event) -> None:
    db = SessionLocal()
    try:
        campaign = db.get(EmktCampaign, campaign_id)
        run = db.get(EmktCampaignRun, run_id)
        if not campaign:
            return
        account = db.get(SesAccount, campaign.account_id)
        if not account or not account.enabled:
            campaign.status = "failed"
            if run: run.status = "failed"
            db.commit()
            return
        connection = _smtp_connection(account)
        campaign.status = "sending"
        if run: run.status = "sending"
        campaign.started_at = datetime.now(timezone.utc)
        db.commit()
        recipients = db.query(EmktRecipient).filter(EmktRecipient.campaign_id == campaign_id, EmktRecipient.status == "pending").order_by(EmktRecipient.id).all()
        for recipient in recipients:
            if stop_event.is_set():
                campaign.status = "stopped"
                if run:
                    run.status = "stopped"; run.completed_at = datetime.now(timezone.utc)
                db.commit()
                return
            try:
                recipient.message_id = _send_one(connection, account, campaign, recipient)
                recipient.status = "sent"
                recipient.sent_at = datetime.now(timezone.utc)
                campaign.sent += 1
                if run: run.sent += 1
            except Exception as exc:
                recipient.status = "failed"
                recipient.error = str(exc)[:2000]
                campaign.failed += 1
                if run: run.failed += 1
            db.commit()
            time.sleep(0.12)
        campaign.status = "completed"
        if run: run.status = "completed"; run.completed_at = datetime.now(timezone.utc)
        campaign.completed_at = datetime.now(timezone.utc)
        db.commit()
    except Exception:
        db.rollback()
        campaign = db.get(EmktCampaign, campaign_id)
        if campaign:
            campaign.status = "failed"
            run = db.get(EmktCampaignRun, run_id)
            if run:
                run.status = "failed"; run.completed_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        try:
            if 'connection' in locals():
                connection.quit()
        except Exception:
            pass
        db.close()
        with _jobs_lock:
            _jobs.pop(campaign_id, None)


def start_campaign(campaign_id: int, run_id: int) -> bool:
    with _jobs_lock:
        existing = _jobs.get(campaign_id)
        if existing and existing[0].is_alive():
            return False
        stop_event = threading.Event()
        thread = threading.Thread(target=_run_campaign, args=(campaign_id, run_id, stop_event), daemon=True)
        _jobs[campaign_id] = (thread, stop_event)
        thread.start()
        return True


def stop_campaign(campaign_id: int) -> bool:
    with _jobs_lock:
        job = _jobs.get(campaign_id)
        if not job:
            return False
        job[1].set()
        return True
