from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.emkt import EmktRecipient


router = APIRouter(prefix="/api/emkt", tags=["emkt-tracking"])
PIXEL = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"


def _now():
    return datetime.now(timezone.utc)


@router.get("/track/open/{recipient_id}.gif")
def track_open(recipient_id: int, db: Session = Depends(get_db)):
    recipient = db.get(EmktRecipient, recipient_id)
    if recipient:
        recipient.open_count = (recipient.open_count or 0) + 1
        recipient.opened_at = recipient.opened_at or _now()
        db.commit()
    return Response(content=PIXEL, media_type="image/gif", headers={"Cache-Control": "no-store, no-cache, must-revalidate"})


@router.get("/track/click/{recipient_id}")
def track_click(recipient_id: int, url: str, db: Session = Depends(get_db)):
    recipient = db.get(EmktRecipient, recipient_id)
    if recipient:
        recipient.click_count = (recipient.click_count or 0) + 1
        recipient.clicked_at = recipient.clicked_at or _now()
        db.commit()
    return RedirectResponse(url=url, status_code=307)


@router.post("/events/ses")
async def ses_event(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    # SNS wraps SES events in Message; direct EventBridge/HTTP sends the event itself.
    if payload.get("Type") == "SubscriptionConfirmation":
        return {"accepted": True, "subscription_confirmation": True}
    raw = payload.get("Message", payload)
    if isinstance(raw, str):
        raw = json.loads(raw)
    raw = raw.get("detail", raw) if isinstance(raw, dict) else {}
    event_type = str(raw.get("eventType") or raw.get("notificationType") or "").lower()
    message_id = str((raw.get("mail") or {}).get("messageId") or "")
    recipient = db.query(EmktRecipient).filter(EmktRecipient.message_id == message_id).first() if message_id else None
    if not recipient:
        return {"accepted": True, "matched": False}
    now = _now()
    if event_type == "delivery":
        recipient.delivered_at = recipient.delivered_at or now
    elif event_type == "bounce":
        recipient.bounced_at = recipient.bounced_at or now
    elif event_type == "complaint":
        recipient.complained_at = recipient.complained_at or now
    elif event_type == "open":
        recipient.open_count = (recipient.open_count or 0) + 1; recipient.opened_at = recipient.opened_at or now
    elif event_type == "click":
        recipient.click_count = (recipient.click_count or 0) + 1; recipient.clicked_at = recipient.clicked_at or now
    db.commit()
    return {"accepted": True, "matched": True, "event": event_type}
