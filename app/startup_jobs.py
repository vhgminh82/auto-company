from __future__ import annotations

import asyncio
import logging

from app.api.contact_enrichment import start_enrichment_job
from app.api.country_crawl import country_crawl_running, start_crawl_job

logger = logging.getLogger(__name__)


async def auto_start_jobs() -> None:
    """Run country discovery first, then the single capped enrichment job."""
    try:
        country = await asyncio.to_thread(start_crawl_job, auto=True)
        logger.info("[startup-jobs] country crawl: %s", country)
        while country_crawl_running():
            await asyncio.sleep(30)
        enrichment = await asyncio.to_thread(start_enrichment_job)
        logger.info("[startup-jobs] enrichment: %s", enrichment)
    except Exception:
        logger.exception("[startup-jobs] failed to start background jobs")
