import httpx

from app.connectors.base import BaseConnector
from app.pipeline.types import CrawlContext

COUNTRY_QID = {
    "united states": "Q30",
    "usa": "Q30",
    "vietnam": "Q881",
    "canada": "Q16",
    "germany": "Q183",
    "japan": "Q17",
    "china": "Q148",
    "south korea": "Q884",
    "singapore": "Q334",
    "thailand": "Q869",
    "india": "Q668",
    "australia": "Q408",
    "france": "Q142",
    "united kingdom": "Q145",
}


def _escape(text: str) -> str:
    return (text or "").replace('"', '\\"').strip().lower()


def _build_sparql(context: CrawlContext, use_region: bool, use_industry: bool, use_query: bool) -> str:
    country_key = (context.country or "").strip().lower()
    country_qid = COUNTRY_QID.get(country_key, "Q30")

    industry = _escape(context.industry)
    region = _escape(context.region)
    query = _escape(context.query)

    filters = []
    if use_industry and industry:
        filters.append(f'FILTER(CONTAINS(LCASE(STR(?industryLabel)), "{industry}"))')
    if use_region and region:
        filters.append(f'FILTER(CONTAINS(LCASE(STR(?hqLabel)), "{region}"))')
    if use_query and query:
        filters.append(
            f'FILTER(CONTAINS(LCASE(STR(?companyLabel)), "{query}") || CONTAINS(LCASE(STR(?industryLabel)), "{query}"))'
        )

    filters_block = "\n  ".join(filters)

    return f'''
SELECT ?company ?companyLabel ?website ?industryLabel ?hqLabel WHERE {{
  ?company wdt:P31 wd:Q4830453;
           wdt:P17 wd:{country_qid}.
  OPTIONAL {{ ?company wdt:P856 ?website. }}
  OPTIONAL {{ ?company wdt:P452 ?industry. }}
  OPTIONAL {{ ?company wdt:P159 ?hq. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
  {filters_block}
}}
LIMIT {max(20, context.max_companies * 4)}
'''


class WikidataConnector(BaseConnector):
    name = "wikidata"

    async def _run_query(self, sparql: str) -> list[dict[str, str]]:
        endpoint = "https://query.wikidata.org/sparql"
        headers = {
            "Accept": "application/sparql-results+json",
            "User-Agent": "crawl-company/1.0 (contact:admin@example.com)",
        }

        try:
            async with httpx.AsyncClient(timeout=35.0, headers=headers) as client:
                response = await client.get(endpoint, params={"query": sparql})
                response.raise_for_status()
                payload = response.json()
        except Exception:
            return []

        rows: list[dict[str, str]] = []
        for item in payload.get("results", {}).get("bindings", []):
            company_name = item.get("companyLabel", {}).get("value", "").strip()
            if not company_name:
                continue
            rows.append(
                {
                    "name": company_name,
                    "address": "",
                    "city": "",
                    "state": item.get("hqLabel", {}).get("value", "").strip(),
                    "website": item.get("website", {}).get("value", "").strip(),
                    "email": "",
                    "phone": "",
                    "short_description": item.get("industryLabel", {}).get("value", "").strip(),
                    "facebook": "",
                    "youtube": "",
                    "x": "",
                    "linkedin": "",
                    "truth": "",
                    "country": "",
                    "region": "",
                    "industry": "",
                    "source_url": item.get("company", {}).get("value", "").strip(),
                }
            )
        return rows

    async def collect(self, context: CrawlContext) -> list[dict[str, str]]:
        strategies = [
            (True, True, True),
            (False, True, True),
            (True, False, True),
            (False, False, True),
            (False, False, False),
        ]

        merged: list[dict[str, str]] = []
        seen: set[str] = set()

        for use_region, use_industry, use_query in strategies:
            sparql = _build_sparql(context, use_region, use_industry, use_query)
            rows = await self._run_query(sparql)
            for row in rows:
                identity = f"{row.get('name', '').strip().lower()}|{row.get('website', '').strip().lower()}"
                if identity in seen:
                    continue
                seen.add(identity)
                row["country"] = context.country
                row["region"] = context.region
                row["industry"] = context.industry or row.get("short_description", "")
                merged.append(row)
                if len(merged) >= context.max_companies:
                    return merged

        return merged
