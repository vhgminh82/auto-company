from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CountryKeyword(Base):
    __tablename__ = "country_keywords"
    __table_args__ = (UniqueConstraint("position", name="uq_country_keyword_position"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    # Nhóm cột Từ khóa (1..16) mà keyword này thuộc về.
    group_position: Mapped[int] = mapped_column(Integer, nullable=False, default=1, index=True)
    keyword: Mapped[str] = mapped_column(String(255), default="")
    active: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
