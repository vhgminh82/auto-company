from sqlalchemy.orm import Session

from app.models.crawl_visited import CrawlVisited


def is_visited(db: Session, url: str) -> bool:
    from app.core.url_utils import normalize_url_for_index

    normalized = normalize_url_for_index(url)
    if not normalized:
        return False
    existing = db.query(CrawlVisited).filter(CrawlVisited.normalized_url == normalized).first()
    return existing is not None


def mark_visited(db: Session, url: str, status: str = "ok") -> bool:
    from sqlalchemy.exc import IntegrityError
    from app.core.url_utils import normalize_url_for_index

    normalized = normalize_url_for_index(url)
    if not normalized:
        return False

    row = CrawlVisited(normalized_url=normalized[:512], source_url=str(url)[:512], status=status[:32])
    db.add(row)
    try:
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        return False


def clear_visited(db: Session) -> int:
    deleted = db.query(CrawlVisited).delete()
    db.commit()
    return deleted
