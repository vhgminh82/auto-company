from app.connectors.base import BaseConnector
from app.core.bing_search import bing_search
from app.pipeline.types import CrawlContext


class YellowPagesConnector(BaseConnector):
    name = "yellowpages"

    async def collect(self, context: CrawlContext) -> list[dict[str, str]]:
        q_parts = [context.query, context.industry, context.region, context.country]
        base_q = " ".join([x for x in q_parts if x]).strip() or "business directory"

        queries = [
            f"site:yellowpages.com {base_q}",
            f"site:mapquest.com business {base_q}",
        ]

        rows: list[dict[str, str]] = []
        seen: set[str] = set()
        for q in queries:
            for hit in bing_search(q, max_results=context.max_companies * 2):
                url = hit.get("url", "")
                if not url or url in seen:
                    continue
                seen.add(url)
                rows.append(
                    {
                        "name": hit.get("title", "") or "Unknown company",
                        "address": "",
                        "city": "",
                        "state": context.region,
                        "website": "",
                        "email": "",
                        "phone": "",
                        "short_description": hit.get("snippet", ""),
                        "facebook": "",
                        "youtube": "",
                        "x": "",
                        "linkedin": "",
                        "truth": "",
                        "country": context.country,
                        "region": context.region,
                        "industry": context.industry,
                        "source_url": url,
                    }
                )
                if len(rows) >= context.max_companies:
                    return rows
        return rows
