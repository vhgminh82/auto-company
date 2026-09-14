import asyncio

from app.fetchers.types import FetchResult


# Serialize Playwright work across all fetcher instances in the API process.
_PLAYWRIGHT_LOCK = asyncio.Lock()


class BrowserFetcher:
    def __init__(self, timeout_ms: int = 25000):
        self.timeout_ms = timeout_ms

    async def fetch(self, url: str) -> FetchResult | None:
        try:
            from playwright.async_api import async_playwright
        except Exception:
            return None

        async with _PLAYWRIGHT_LOCK:
            browser = None
            context = None
            try:
                async with async_playwright() as pw:
                    browser = await pw.chromium.launch(headless=True)
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
            except Exception:
                return None
            finally:
                if context is not None:
                    try:
                        await context.close()
                    except Exception:
                        pass
                if browser is not None:
                    try:
                        await browser.close()
                    except Exception:
                        pass
