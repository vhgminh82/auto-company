from abc import ABC, abstractmethod

from app.pipeline.types import CrawlContext


class BaseConnector(ABC):
    name: str = "base"

    @abstractmethod
    async def collect(self, context: CrawlContext) -> list[dict[str, str]]:
        raise NotImplementedError
