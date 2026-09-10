from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import requests
from bs4 import BeautifulSoup


def _decode_bing_target(raw_url: str) -> str:
    if not raw_url:
        return ""
    parsed = urlparse(raw_url)
    if "bing.com" not in parsed.netloc:
        return raw_url
    query = parse_qs(parsed.query)
    if "u" in query and query["u"]:
        # bing often wraps target in base64-like token; if decode fails, keep raw
        return raw_url
    return raw_url


def bing_search(query: str, max_results: int = 20) -> list[dict[str, str]]:
    url = f"https://www.bing.com/search?q={quote_plus(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    results: list[dict[str, str]] = []

    for item in soup.select("li.b_algo"):
        anchor = item.select_one("h2 a[href]")
        if not anchor:
            continue
        href = unquote(anchor.get("href", "")).strip()
        title = " ".join(anchor.stripped_strings).strip()
        snippet_el = item.select_one("p")
        snippet = " ".join(snippet_el.stripped_strings).strip() if snippet_el else ""

        href = _decode_bing_target(href)
        if not href:
            continue

        results.append({"title": title, "url": href, "snippet": snippet})
        if len(results) >= max_results:
            break

    return results
