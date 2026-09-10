from dataclasses import dataclass


@dataclass(frozen=True)
class CrawlContext:
    query: str
    country: str
    region: str
    industry: str
    max_companies: int
