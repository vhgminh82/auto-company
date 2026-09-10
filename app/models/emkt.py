from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy import JSON

from app.database import Base


class SesAccount(Base):
    __tablename__ = "ses_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    region: Mapped[str] = mapped_column(String(64), nullable=False, default="us-east-1")
    access_key_id: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    secret_access_key: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    session_token: Mapped[str] = mapped_column(Text, nullable=False, default="")
    profile_name: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    from_email: Mapped[str] = mapped_column(String(255), nullable=False)
    from_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    configuration_set: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    smtp_host: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    smtp_port: Mapped[int] = mapped_column(Integer, nullable=False, default=465)
    smtp_security: Mapped[str] = mapped_column(String(16), nullable=False, default="ssl")
    smtp_username: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    smtp_password: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    enabled: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class EmktList(Base):
    __tablename__ = "emkt_lists"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    country_filter: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    industry_filter: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    query_filter: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    blacklist: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    manual_emails: Mapped[str] = mapped_column(Text, nullable=False, default="")
    blacklist_emails: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class EmktListMember(Base):
    __tablename__ = "emkt_list_members"
    __table_args__ = (UniqueConstraint("list_id", "company_id", name="uq_emkt_list_company"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    list_id: Mapped[int] = mapped_column(ForeignKey("emkt_lists.id"), nullable=False, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    custom_email: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    blacklisted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class EmktCampaign(Base):
    __tablename__ = "emkt_campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("ses_accounts.id"), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    html_body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    text_body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    country_filter: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    industry_filter: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    query_filter: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    list_ids: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    recipient_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=500)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", index=True)
    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scheduled_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)


class EmktCampaignRun(Base):
    __tablename__ = "emkt_campaign_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("emkt_campaigns.id"), nullable=False, index=True)
    started_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class EmktRecipient(Base):
    __tablename__ = "emkt_recipients"
    __table_args__ = (UniqueConstraint("campaign_id", "email", name="uq_emkt_campaign_email"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("emkt_campaigns.id"), nullable=False, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    website: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    message_id: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    error: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sent_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    bounced_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    complained_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    opened_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    clicked_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    open_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    click_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class ContactScenario(Base):
    __tablename__ = "contact_scenarios"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    fields: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ContactRun(Base):
    __tablename__ = "contact_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scenario_id: Mapped[int] = mapped_column(ForeignKey("contact_scenarios.id"), nullable=False, index=True)
    list_ids: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    started_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    captcha: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class ContactList(Base):
    __tablename__ = "contact_lists"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    country_filter: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    industry_filter: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ContactListMember(Base):
    __tablename__ = "contact_list_members"
    __table_args__ = (UniqueConstraint("list_id", "company_id", name="uq_contact_list_company"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    list_id: Mapped[int] = mapped_column(ForeignKey("contact_lists.id"), nullable=False, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
