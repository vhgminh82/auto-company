from urllib.parse import urlparse

BLOCKED_URL_TERMS = (
    "google", "amazon", "survey", "yahoo", "baidu", "wiki", "wikidata", "search", "copyright.com",
)
BLOCKED_SOURCE_TERMS = ("wikipedia", "wikidata", "copyright.com")


def is_blocked_url(url: str) -> bool:
    value = (url or "").lower()
    return any(term in value for term in BLOCKED_URL_TERMS)


def is_blocked_source_url(url: str) -> bool:
    value = (url or "").lower()
    return any(term in value for term in BLOCKED_SOURCE_TERMS)


def normalize_url_for_index(url: str) -> str:
    if not url:
        return ""
    value = url.strip()
    parsed = urlparse(value if value.lower().startswith(("http://", "https://")) else f"https://{value}")
    host = (parsed.hostname or "").lower().strip()
    if host.startswith("www."):
        host = host[4:]
    return f"https://{host}/" if host else ""
