from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = "sqlite:///./companies.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
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
        if "region" in existing:
            connection.execute(text("DROP INDEX IF EXISTS ix_companies_region"))
            connection.execute(text("ALTER TABLE companies DROP COLUMN region"))

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


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
