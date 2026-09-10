from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (
        UniqueConstraint("name", "website", name="uq_company_name_website"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    address: Mapped[str] = mapped_column(String(512), default="")
    city: Mapped[str] = mapped_column(String(128), default="", index=True)
    state: Mapped[str] = mapped_column(String(128), default="", index=True)
    website: Mapped[str] = mapped_column(String(512), default="", index=True)
    contact: Mapped[str] = mapped_column(String(64), default="", index=True)
    email: Mapped[str] = mapped_column(String(255), default="")
    email_2: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(64), default="")
    short_description: Mapped[str] = mapped_column(Text, default="")
    facebook: Mapped[str] = mapped_column(String(512), default="")
    facebook_alt: Mapped[str] = mapped_column(String(512), default="")
    youtube: Mapped[str] = mapped_column(String(512), default="")
    x: Mapped[str] = mapped_column(String(512), default="")
    linkedin: Mapped[str] = mapped_column(String(512), default="")
    truth: Mapped[str] = mapped_column(String(512), default="")
    country: Mapped[str] = mapped_column(String(128), default="", index=True)
    industry: Mapped[str] = mapped_column(String(128), default="", index=True)
    industry_raw: Mapped[str] = mapped_column(String(255), default="")
    list: Mapped[str] = mapped_column(Text, default="")
    source_url: Mapped[str] = mapped_column(String(512), default="")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
