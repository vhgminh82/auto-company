from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CountrySource(Base):
    __tablename__ = "country_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    place_name: Mapped[str] = mapped_column(String(255), default="")
    country: Mapped[str] = mapped_column(String(128), default="", index=True)
    state: Mapped[str] = mapped_column(String(128), default="")
    city: Mapped[str] = mapped_column(String(128), default="")
    region: Mapped[str] = mapped_column(String(128), default="")
    keyword_1: Mapped[str] = mapped_column(String(255), default="")
    keyword_2: Mapped[str] = mapped_column(String(255), default="")
    keyword_3: Mapped[str] = mapped_column(String(255), default="")
    keyword_4: Mapped[str] = mapped_column(String(255), default="")
    keyword_5: Mapped[str] = mapped_column(String(255), default="")
    keyword_6: Mapped[str] = mapped_column(String(255), default="")
    keyword_7: Mapped[str] = mapped_column(String(255), default="")
    keyword_8: Mapped[str] = mapped_column(String(255), default="")
    keyword_9: Mapped[str] = mapped_column(String(255), default="")
    keyword_10: Mapped[str] = mapped_column(String(255), default="")
    keyword_11: Mapped[str] = mapped_column(String(255), default="")
    keyword_12: Mapped[str] = mapped_column(String(255), default="")
    keyword_13: Mapped[str] = mapped_column(String(255), default="")
    keyword_14: Mapped[str] = mapped_column(String(255), default="")
    keyword_15: Mapped[str] = mapped_column(String(255), default="")
    keyword_16: Mapped[str] = mapped_column(String(255), default="")
