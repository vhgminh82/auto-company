from app.fetchers.types import FetchResult
from app.playwright_guard import limited_playwright


class BrowserFetcher:
    def __init__(self, timeout_ms: int = 25000):
        self.timeout_ms = timeout_ms

    async def fetch(self, url: str) -> FetchResult | None:
        try:
            async with limited_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                context = None
                try:
                    context = await browser.new_context()
                    page = await context.new_page()
                    response = await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                    await page.wait_for_timeout(1200)
                    html = await page.content()
                    final_url = page.url
                    status_code = response.status if response else 200
                    if status_code >= 400 or not html:
                        return None
                    return FetchResult(
                        final_url=final_url,
                        status_code=status_code,
                        html=html,
                        fetcher="browser",
                    )
                finally:
                    if context is not None:
                        try:
                            await context.close()
                        except Exception:
                            pass
                    try:
                        await browser.close()
                    except Exception:
                        pass
        except Exception:
            return None
