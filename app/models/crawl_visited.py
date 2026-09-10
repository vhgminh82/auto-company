from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class CrawlVisited(Base):
    __tablename__ = "crawl_visited"
    __table_args__ = (UniqueConstraint("normalized_url", name="uq_crawl_visited_normalized_url"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    normalized_url: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    source_url: Mapped[str] = mapped_column(String(512), default="")
    status: Mapped[str] = mapped_column(String(32), default="ok")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
