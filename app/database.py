import os
from contextvars import ContextVar
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker, with_loader_criteria
from fastapi import Request

current_owner: ContextVar[str] = ContextVar("current_owner", default="")

def _load_dotenv() -> None:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip(chr(34)).strip(chr(39)))

_load_dotenv()
DATABASE_URL = os.getenv("SUPABASE_DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("SUPABASE_DATABASE_URL chưa được cấu hình; app chỉ hỗ trợ Supabase.")
IS_SQLITE = DATABASE_URL.startswith("sqlite")

engine_kwargs = {"pool_pre_ping": True, "pool_recycle": 1800}
if IS_SQLITE:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def ensure_schema():
    from sqlalchemy import inspect, text
    existing = {column["name"] for column in inspect(engine).get_columns("companies")}
    additions = {
        "contact": "VARCHAR(64) NOT NULL DEFAULT ''",
        "facebook_alt": "VARCHAR(512) NOT NULL DEFAULT ''",
        "industry_raw": "VARCHAR(255) NOT NULL DEFAULT ''",
        "email_2": "VARCHAR(255) NOT NULL DEFAULT ''",
        "list": "TEXT NOT NULL DEFAULT ''",
    }
    with engine.begin() as connection:
        for name, definition in additions.items():
            if name not in existing:
                connection.execute(text(f"ALTER TABLE companies ADD COLUMN {name} {definition}"))

    scenario_columns = {column["name"] for column in inspect(engine).get_columns("contact_scenarios")}
    with engine.begin() as connection:
        if "description" not in scenario_columns:
            connection.execute(text("ALTER TABLE contact_scenarios ADD COLUMN description TEXT NOT NULL DEFAULT ''"))
        if "reference_website" not in scenario_columns:
            connection.execute(text("ALTER TABLE contact_scenarios ADD COLUMN reference_website VARCHAR(2000) NOT NULL DEFAULT ''"))

    ai_columns = {column["name"] for column in inspect(engine).get_columns("ai_settings")}
    with engine.begin() as connection:
        if "custom_prompt" not in ai_columns:
            connection.execute(text("ALTER TABLE ai_settings ADD COLUMN custom_prompt TEXT NOT NULL DEFAULT ''"))

    check_constraints = {item.get("name") for item in inspect(engine).get_check_constraints("companies")}
    with engine.begin() as connection:
        if "companies_website_required" not in check_constraints:
            connection.execute(
                text(
                    "ALTER TABLE companies ADD CONSTRAINT companies_website_required "
                    "CHECK (website IS NOT NULL AND length(trim(website)) > 0)"
                )
            )

    keyword_columns = {column["name"] for column in inspect(engine).get_columns("country_keywords")}
    with engine.begin() as connection:
        if "group_position" not in keyword_columns:
            connection.execute(text("ALTER TABLE country_keywords ADD COLUMN group_position INTEGER NOT NULL DEFAULT 1"))
            connection.execute(text("UPDATE country_keywords SET group_position = position WHERE position BETWEEN 1 AND 16"))
        if "active" not in keyword_columns:
            connection.execute(text("ALTER TABLE country_keywords ADD COLUMN active INTEGER NOT NULL DEFAULT 0"))
            connection.execute(text("UPDATE country_keywords SET active = 1 WHERE position BETWEEN 1 AND 16"))

    account_columns = {column["name"] for column in inspect(engine).get_columns("ses_accounts")}
    account_additions = {
        "smtp_host": "VARCHAR(255) NOT NULL DEFAULT ''",
        "smtp_port": "INTEGER NOT NULL DEFAULT 465",
        "smtp_security": "VARCHAR(16) NOT NULL DEFAULT 'ssl'",
        "smtp_username": "VARCHAR(512) NOT NULL DEFAULT ''",
        "smtp_password": "VARCHAR(1024) NOT NULL DEFAULT ''",
    }
    with engine.begin() as connection:
        for name, definition in account_additions.items():
            if name not in account_columns:
                connection.execute(text(f"ALTER TABLE ses_accounts ADD COLUMN {name} {definition}"))

    list_columns = {column["name"] for column in inspect(engine).get_columns("emkt_lists")}
    with engine.begin() as connection:
        if "blacklist" not in list_columns:
            connection.execute(text("ALTER TABLE emkt_lists ADD COLUMN blacklist INTEGER NOT NULL DEFAULT 0"))
        if "manual_emails" not in list_columns:
            connection.execute(text("ALTER TABLE emkt_lists ADD COLUMN manual_emails TEXT NOT NULL DEFAULT ''"))
        if "blacklist_emails" not in list_columns:
            connection.execute(text("ALTER TABLE emkt_lists ADD COLUMN blacklist_emails TEXT NOT NULL DEFAULT ''"))

    member_columns = {column["name"] for column in inspect(engine).get_columns("emkt_list_members")}
    with engine.begin() as connection:
        if "blacklisted" not in member_columns:
            connection.execute(text("ALTER TABLE emkt_list_members ADD COLUMN blacklisted INTEGER NOT NULL DEFAULT 0"))

    campaign_columns = {column["name"] for column in inspect(engine).get_columns("emkt_campaigns")}
    with engine.begin() as connection:
        if "list_ids" not in campaign_columns:
            connection.execute(text("ALTER TABLE emkt_campaigns ADD COLUMN list_ids TEXT NOT NULL DEFAULT '[]'"))
        if "scheduled_at" not in campaign_columns:
            connection.execute(text("ALTER TABLE emkt_campaigns ADD COLUMN scheduled_at DATETIME"))

    recipient_columns = {column["name"] for column in inspect(engine).get_columns("emkt_recipients")}
    recipient_additions = {
        "delivered_at": "DATETIME", "bounced_at": "DATETIME", "complained_at": "DATETIME",
        "opened_at": "DATETIME", "clicked_at": "DATETIME", "open_count": "INTEGER NOT NULL DEFAULT 0",
        "click_count": "INTEGER NOT NULL DEFAULT 0",
    }
    with engine.begin() as connection:
        for name, definition in recipient_additions.items():
            if name not in recipient_columns:
                connection.execute(text(f"ALTER TABLE emkt_recipients ADD COLUMN {name} {definition}"))

    for table in ("ses_accounts", "emkt_lists", "emkt_campaigns", "emkt_campaign_runs", "contact_scenarios", "contact_runs", "contact_lists"):
        columns = {column["name"] for column in inspect(engine).get_columns(table)}
        if "owner_email" not in columns:
            with engine.begin() as connection:
                connection.execute(text(f"ALTER TABLE {table} ADD COLUMN owner_email VARCHAR(320) NOT NULL DEFAULT ''"))


class Base(DeclarativeBase):
    pass


def get_db(request: Request):
    db = SessionLocal()
    db.info["owner_email"] = (request.session.get("user", {}).get("email", "").lower() if request else "")
    try:
        yield db
    finally:
        db.close()


@event.listens_for(Session, "do_orm_execute")
def _scope_user_data(execute_state):
    if not execute_state.is_select or execute_state.execution_options.get("skip_owner_scope"):
        return
    owner = execute_state.session.info.get("owner_email", "")
    if not owner:
        return
    from app.models.emkt import SesAccount, EmktList, EmktCampaign, EmktCampaignRun, ContactScenario, ContactRun, ContactList
    for model in (SesAccount, EmktList, EmktCampaign, EmktCampaignRun, ContactScenario, ContactRun, ContactList):
        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(
                model,
                lambda cls: (cls.owner_email == owner)
                | cls.owner_email.like(owner + ",%")
                | cls.owner_email.like("%," + owner + ",%")
                | cls.owner_email.like("%," + owner),
                include_aliases=True,
            )
        )


@event.listens_for(Session, "before_flush")
def _stamp_owner(session, flush_context, instances):
    owner = session.info.get("owner_email", "")
    if not owner:
        return
    for item in session.new:
        if hasattr(item, "owner_email") and not getattr(item, "owner_email", ""):
            item.owner_email = owner





