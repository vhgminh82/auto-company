import httpx

from app.fetchers.types import FetchResult


class HttpFetcher:
    def __init__(self, timeout_seconds: float = 20.0):
        self.timeout_seconds = timeout_seconds

    async def fetch(self, url: str) -> FetchResult | None:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=True) as client:
                response = await client.get(url)
                if response.status_code >= 400 or not response.text:
                    return None
                return FetchResult(
                    final_url=str(response.url),
                    status_code=response.status_code,
                    html=response.text,
                    fetcher="http",
                )
        except Exception:
            return None
