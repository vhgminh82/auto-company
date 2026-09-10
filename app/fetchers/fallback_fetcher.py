from app.fetchers.browser_fetcher import BrowserFetcher
from app.fetchers.http_fetcher import HttpFetcher
from app.fetchers.types import FetchResult


class FallbackFetcher:
    def __init__(self):
        self.http_fetcher = HttpFetcher()
        self.browser_fetcher = BrowserFetcher()

    async def fetch(self, url: str) -> FetchResult | None:
        # Strategy: fast path HTTP first, then browser rendering for JS-heavy/blocked pages.
        result = await self.http_fetcher.fetch(url)
        if result is not None:
            return result
        return await self.browser_fetcher.fetch(url)
