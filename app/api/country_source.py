from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.country_source import sync_completed_queries, sync_country_sheet
from app.database import get_db
from app.models.country_source import CountrySource
from app.models.country_keyword import CountryKeyword

router = APIRouter(prefix="/api/country-source", tags=["country-source"])


class CountrySourceSyncRequest(BaseModel):
    spreadsheet_url: str = Field(min_length=20, max_length=2048)
    sheet_name: str = Field(default="Quốc gia", min_length=1, max_length=200)


class KeywordsUpdateRequest(BaseModel):
    keywords: list[str] = Field(default_factory=list, max_length=16)


class KeywordCreateRequest(BaseModel):
    keyword: str = Field(min_length=1, max_length=255)
    group_position: int = Field(ge=1, le=16)


class KeywordActiveRequest(BaseModel):
    active: bool = True


@router.post("/sync")
def sync_source(request: CountrySourceSyncRequest):
    try:
        return sync_country_sheet(request.spreadsheet_url, request.sheet_name)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/sync-completed")
def sync_completed():
    try:
        return sync_completed_queries()
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("")
def list_source(limit: int = Query(default=1000, ge=1, le=25000), db: Session = Depends(get_db)):
    return db.query(CountrySource).order_by(CountrySource.id).limit(limit).all()


@router.get("/keywords")
def list_keywords(db: Session = Depends(get_db)):
    return db.query(CountryKeyword).order_by(CountryKeyword.position).all()


@router.get("/stats")
def source_stats(db: Session = Depends(get_db)):
    rows = db.query(CountrySource).all()
    active_groups = {
        item.group_position
        for item in db.query(CountryKeyword).filter(CountryKeyword.active == 1, CountryKeyword.keyword != "").all()
    }
    pending_by_location = [
        sum(
            1
            for group in active_groups
            if (getattr(row, f"keyword_{group}", "") or "").strip().upper() != "V"
        )
        for row in rows
    ]
    return {
        "total_locations": len(rows),
        "pending_locations": sum(1 for count in pending_by_location if count),
        "pending_combinations": sum(pending_by_location),
    }


@router.post("/keywords")
def create_keyword(request: KeywordCreateRequest, db: Session = Depends(get_db)):
    keyword = request.keyword.strip()
    if not keyword:
        raise HTTPException(400, "Từ khóa không được để trống.")
    latest = db.query(CountryKeyword).order_by(CountryKeyword.position.desc()).first()
    item = CountryKeyword(
        position=(latest.position + 1 if latest else 1),
        group_position=request.group_position,
        keyword=keyword,
        active=0,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/keywords/{position}/active")
def activate_keyword(position: int, request: KeywordActiveRequest, db: Session = Depends(get_db)):
    item = db.query(CountryKeyword).filter(CountryKeyword.position == position).first()
    if not item:
        raise HTTPException(404, "Không tìm thấy từ khóa.")
    if request.active:
        db.query(CountryKeyword).filter(
            CountryKeyword.group_position == item.group_position
        ).update({CountryKeyword.active: 0}, synchronize_session=False)
        item.active = 1
    else:
        item.active = 0
    db.commit()
    db.refresh(item)
    return item


@router.delete("/keywords/{position}")
def delete_keyword(position: int, db: Session = Depends(get_db)):
    # Vị trí 1..16 là keyword gốc, được đồng bộ từ tiêu đề Google Sheet.
    if position <= 16:
        raise HTTPException(400, "Không thể xóa từ khóa gốc lấy từ Google Sheet.")
    item = db.query(CountryKeyword).filter(CountryKeyword.position == position).first()
    if not item:
        raise HTTPException(404, "Không tìm thấy từ khóa.")
    db.delete(item)
    db.commit()
    return {"deleted": position}


@router.patch("/{source_id}/keywords")
def update_keywords(source_id: int, request: KeywordsUpdateRequest, db: Session = Depends(get_db)):
    source = db.get(CountrySource, source_id)
    if not source:
        raise HTTPException(404, "Không tìm thấy dòng dữ liệu quốc gia.")
    keywords = [str(value).strip()[:255] for value in request.keywords if str(value).strip()][:16]
    for index in range(1, 17):
        setattr(source, f"keyword_{index}", keywords[index - 1] if index <= len(keywords) else "")
    db.commit()
    db.refresh(source)
    return source
