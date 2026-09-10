from io import BytesIO

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.constants import COMPANY_EXPORT_COLUMNS
from app.database import get_db
from app.repositories.company_repo import insert_many_ignore_duplicates, list_for_export

router = APIRouter(prefix="/api", tags=["io"])


@router.post("/import")
async def import_companies(file: UploadFile = File(...), db: Session = Depends(get_db)):
    filename = file.filename.lower()
    content = await file.read()

    if filename.endswith(".csv"):
        df = pd.read_csv(BytesIO(content))
    elif filename.endswith(".xlsx"):
        df = pd.read_excel(BytesIO(content))
    else:
        raise HTTPException(status_code=400, detail="Only CSV/XLSX are supported")

    required_cols = [
        "name", "address", "city", "state", "website", "email", "phone", "short_description",
        "facebook", "youtube", "x", "linkedin", "truth",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing columns: {', '.join(missing)}")

    records = [
        {col: str(row.get(col, "") if pd.notna(row.get(col, "")) else "") for col in COMPANY_EXPORT_COLUMNS}
        for _, row in df.iterrows()
    ]
    inserted = insert_many_ignore_duplicates(db, records)
    return {"rows": len(df), "inserted": inserted}


@router.get("/export/csv")
def export_csv(db: Session = Depends(get_db)):
    rows = list_for_export(db)
    df = pd.DataFrame(rows)
    return StreamingResponse(
        iter([df.to_csv(index=False).encode("utf-8")]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=companies.csv"},
    )


@router.get("/export/xlsx")
def export_xlsx(db: Session = Depends(get_db)):
    rows = list_for_export(db)
    df = pd.DataFrame(rows)
    bio = BytesIO()
    df.to_excel(bio, index=False, engine="openpyxl")
    bio.seek(0)
    return StreamingResponse(
        bio,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=companies.xlsx"},
    )
