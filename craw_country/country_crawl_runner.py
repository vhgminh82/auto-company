"""Linux-compatible country crawl runner using the app's Python connectors."""
from __future__ import annotations

import argparse
import asyncio
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.database import SessionLocal
from app.pipeline.orchestrator import CrawlOrchestrator
from app.pipeline.types import CrawlContext
from app.repositories.company_repo import insert_many_ignore_duplicates


def write_progress(path: Path, state: str, current: int, total: int, query: str = "", found: int = 0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{state}|{current}|{total}|{query}|{found}", encoding="utf-8")


def build_pending(craw_dir: Path, completed: Path, pending: Path) -> None:
    subprocess.run(
        [sys.executable, str(craw_dir / "build_pending_queries.py"), "--database", "SUPABASE", "--completed", str(completed), "--output", str(pending)],
        cwd=craw_dir,
        check=True,
    )


def mark_completed(craw_dir: Path, query: str) -> None:
    subprocess.run(
        [sys.executable, str(craw_dir / "mark_query_completed.py"), "--database", "SUPABASE", "--query", query],
        cwd=craw_dir,
        check=True,
        stdout=subprocess.DEVNULL,
    )


async def crawl_query(orchestrator: CrawlOrchestrator, query: str) -> list[dict[str, str]]:
    return await orchestrator.run(CrawlContext(query=query, country="", region="", industry="", max_companies=5000))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--progress", required=True)
    args = parser.parse_args()
    craw_dir = Path(__file__).resolve().parent
    results = craw_dir / "results"
    completed = craw_dir / "completed_queries.txt"
    pending = results / "pending_queries.txt"
    progress = Path(args.progress)
    try:
        completed.touch(exist_ok=True)
        build_pending(craw_dir, completed, pending)
        queries = [line.strip() for line in pending.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
        write_progress(progress, "RUNNING", 0, len(queries), "", 0)
        orchestrator = CrawlOrchestrator()
        found = 0
        for index, query in enumerate(queries, 1):
            try:
                rows = asyncio.run(crawl_query(orchestrator, query))
                db = SessionLocal()
                try:
                    inserted = insert_many_ignore_duplicates(db, rows)
                finally:
                    db.close()
                mark_completed(craw_dir, query)
                found += inserted
            except Exception as exc:
                print(f"[country-crawl] query failed: {query}: {exc}", flush=True)
            write_progress(progress, "RUNNING", index, len(queries), query, found)
        write_progress(progress, "DONE", len(queries), len(queries), "", found)
        return 0
    except KeyboardInterrupt:
        write_progress(progress, "STOPPED", 0, 0, "", 0)
        return 130
    except Exception as exc:
        write_progress(progress, "FAILED", 0, 0, str(exc), 0)
        print(f"[country-crawl] failed: {exc}", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
