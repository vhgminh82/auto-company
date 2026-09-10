from app.connectors.registry import get_default_connectors
from app.pipeline.processors.deduper import dedupe_records
from app.pipeline.processors.merger import merge_group
from app.pipeline.processors.normalizer import normalize_record
from app.pipeline.processors.scorer import attach_score
from app.pipeline.types import CrawlContext


class CrawlOrchestrator:
    def __init__(self):
        self._connectors = get_default_connectors()

    async def run_with_progress(self, context: CrawlContext):
        collected: list[dict[str, str]] = []

        for connector in self._connectors:
            rows = await connector.collect(context)
            collected.extend(rows)
            yield {
                "stage": "connector",
                "connector": connector.name,
                "collected": len(collected),
                "last_batch": len(rows),
            }

        normalized = [normalize_record(record) for record in collected if (record.get("name", "") or "").strip()]
        yield {"stage": "normalize", "collected": len(collected), "normalized": len(normalized)}

        grouped = dedupe_records(normalized)
        merged = [merge_group(group) for group in grouped]
        scored = [attach_score(record) for record in merged]
        final_rows = scored[: context.max_companies]

        yield {
            "stage": "postprocess",
            "grouped": len(grouped),
            "merged": len(merged),
            "final": len(final_rows),
        }
        yield {"stage": "final_rows", "rows": final_rows}

    async def run(self, context: CrawlContext) -> list[dict[str, str]]:
        final_rows: list[dict[str, str]] = []
        async for event in self.run_with_progress(context):
            if event.get("stage") == "final_rows":
                final_rows = event.get("rows", [])
        return final_rows
