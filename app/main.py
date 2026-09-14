from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import secrets
import hashlib
import asyncio
from starlette.middleware.sessions import SessionMiddleware

from app.api.companies import router as companies_router
from app.api.crawl import router as crawl_router
from app.api.import_export import router as io_router
from app.api.ui import router as ui_router
from app.api.contact import router as contact_router
from app.api.sheet_contact import router as sheet_contact_router
from app.api.db_contact import router as db_contact_router
from app.api.country_source import router as country_source_router
from app.api.country_crawl import router as country_crawl_router
from app.api.company_source import router as company_source_router
from app.api.contact_enrichment import router as contact_enrichment_router
from app.api.contact_campaign import router as contact_campaign_router
from app.api.sheet_sync import router as sheet_sync_router
from app.api.emkt import router as emkt_router
from app.api.emkt_lists import router as emkt_lists_router
from app.api.emkt_tracking import router as emkt_tracking_router
from app.api.ai import router as ai_router
from app.auth import router as auth_router
from app.middleware import LoginRequiredMiddleware
from app.database import Base, engine, ensure_schema
from app.models.user import AppUser
from app.database import SessionLocal

Base.metadata.create_all(bind=engine)
ensure_schema()
with SessionLocal() as _db:
    for _email in ("vhglinh@gmail.com", "icdirector@cnctech.vn"):
        _user = _db.query(AppUser).filter(AppUser.email == _email).first()
        if not _user:
            _db.add(AppUser(email=_email, status="approved", is_admin=1))
        else:
            _user.status, _user.is_admin = "approved", 1
    _db.commit()

app = FastAPI(title="Company Crawl Platform", version="2.0.0")
app.add_middleware(LoginRequiredMiddleware)
session_secret = os.getenv("AUTH_SESSION_SECRET") or hashlib.sha256((os.getenv("SUPABASE_DATABASE_URL", "") + "::crm-auth-session").encode()).hexdigest()
app.add_middleware(SessionMiddleware, secret_key=session_secret, same_site="lax")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(ui_router)
app.include_router(crawl_router)
app.include_router(companies_router)
app.include_router(io_router)
app.include_router(contact_router)
app.include_router(sheet_contact_router)
app.include_router(db_contact_router)
app.include_router(country_source_router)
app.include_router(country_crawl_router)
app.include_router(company_source_router)
app.include_router(contact_enrichment_router)
app.include_router(contact_campaign_router)
app.include_router(sheet_sync_router)
app.include_router(emkt_router)
app.include_router(emkt_lists_router)
app.include_router(emkt_tracking_router)
app.include_router(ai_router)
app.include_router(auth_router)


@app.on_event("startup")
async def start_background_jobs() -> None:
    from app.startup_jobs import auto_start_jobs
    asyncio.create_task(auto_start_jobs())
