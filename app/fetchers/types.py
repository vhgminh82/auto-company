from dataclasses import dataclass


@dataclass(frozen=True)
class FetchResult:
    final_url: str
    status_code: int
    html: str
    fetcher: str
