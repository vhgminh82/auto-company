import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.pipeline.orchestrator import CrawlOrchestrator
from app.pipeline.types import CrawlContext
from app.repositories.company_repo import insert_many_ignore_duplicates
from app.repositories.visited_repo import is_visited, mark_visited
from app.schemas import CrawlRequest

router = APIRouter(prefix="/api", tags=["crawl"])
orchestrator = CrawlOrchestrator()

UNBOUNDED_MAX = 5000


def _resolve_max_companies(raw: int) -> int:
    if raw == -1:
        return UNBOUNDED_MAX
    return min(max(raw, 1), UNBOUNDED_MAX)


def _filter_by_visited(db: Session, rows: list[dict[str, str]]):
    filtered_rows: list[dict[str, str]] = []
    skipped_visited = 0

    for row in rows:
        website = (row.get("website") or "").strip()
        if not website:
            continue
        if is_visited(db, website):
            skipped_visited += 1
            continue
        filtered_rows.append(row)
        mark_visited(db, website, status="ok")

    return filtered_rows, skipped_visited


@router.post("/crawl")
async def run_crawl(payload: CrawlRequest, db: Session = Depends(get_db)):
    max_companies = _resolve_max_companies(payload.max_companies)
    context = CrawlContext(
        query=payload.query,
        country=payload.country,
        region=payload.region,
        industry=payload.industry,
        max_companies=max_companies,
    )

    rows = await orchestrator.run(context)
    filtered_rows, skipped_visited = _filter_by_visited(db, rows)
    inserted = insert_many_ignore_duplicates(db, filtered_rows)

    return {
        "fetched": len(rows),
        "skipped_visited": skipped_visited,
        "eligible": len(filtered_rows),
        "inserted": inserted,
    }


@router.post("/crawl/stream")
async def run_crawl_stream(payload: CrawlRequest, db: Session = Depends(get_db)):
    max_companies = _resolve_max_companies(payload.max_companies)
    context = CrawlContext(
        query=payload.query,
        country=payload.country,
        region=payload.region,
        industry=payload.industry,
        max_companies=max_companies,
    )

    async def event_iter():
        rows: list[dict[str, str]] = []

        async for event in orchestrator.run_with_progress(context):
            if event.get("stage") == "final_rows":
                rows = event.get("rows", [])
            else:
                yield json.dumps({"type": "progress", **event}, ensure_ascii=False) + "\n"

        filtered_rows, skipped_visited = _filter_by_visited(db, rows)
        inserted = insert_many_ignore_duplicates(db, filtered_rows)

        yield json.dumps(
            {
                "type": "done",
                "fetched": len(rows),
                "skipped_visited": skipped_visited,
                "eligible": len(filtered_rows),
                "inserted": inserted,
            },
            ensure_ascii=False,
        ) + "\n"

    return StreamingResponse(event_iter(), media_type="application/x-ndjson")
