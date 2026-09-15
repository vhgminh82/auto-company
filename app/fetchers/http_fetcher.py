import httpx
from bs4 import BeautifulSoup

from app.fetchers.types import FetchResult


class HttpFetcher:
    def __init__(self, timeout_seconds: float = 20.0):
        self.timeout_seconds = timeout_seconds

    async def fetch(self, url: str) -> FetchResult | None:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=True) as client:
                response = await client.get(url)
                if response.status_code >= 400 or not response.content:
                    return None
                # Let the HTML parser honor charset declarations instead of
                # trusting a server header that may decode CJK pages incorrectly.
                html = BeautifulSoup(response.content, "html.parser").decode()
                return FetchResult(
                    final_url=str(response.url),
                    status_code=response.status_code,
                    html=html,
                    fetcher="http",
                )
        except Exception:
            return None
