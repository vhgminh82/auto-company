from sqlalchemy.orm import Session

from app.models.company import Company


def delete_all_companies(db: Session) -> int:
    deleted = db.query(Company).delete()
    db.commit()
    return deleted
