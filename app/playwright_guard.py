import asyncio
from contextlib import asynccontextmanager

from playwright.async_api import async_playwright


_PLAYWRIGHT_LOCK = asyncio.Lock()


@asynccontextmanager
async def limited_playwright():
    """Allow only one Playwright session in the API process at a time."""
    async with _PLAYWRIGHT_LOCK:
        async with async_playwright() as playwright:
            yield playwright
