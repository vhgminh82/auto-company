from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class AISetting(Base):
    __tablename__ = "ai_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    primary_model: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    fallback_model_1: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    fallback_model_2: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)