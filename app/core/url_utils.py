from urllib.parse import urlparse


def normalize_url_for_index(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url if url.startswith(("http://", "https://")) else f"https://{url}")
    scheme = (parsed.scheme or "https").lower()
    host = (parsed.netloc or "").lower().strip()
    if host.startswith("www."):
        host = host[4:]
    path = (parsed.path or "/").rstrip("/") or "/"
    return f"{scheme}://{host}{path}"
