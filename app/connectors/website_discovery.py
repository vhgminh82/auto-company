import base64
import re
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import httpx
from bs4 import BeautifulSoup

from app.connectors.base import BaseConnector
from app.fetchers.fallback_fetcher import FallbackFetcher
from app.pipeline.types import CrawlContext

EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_PATTERN = re.compile(r"\+?[0-9][0-9\-\s().]{7,}[0-9]")

SOCIAL_KEYS = {
    "facebook": ["facebook.com"],
    "youtube": ["youtube.com", "youtu.be"],
    "x": ["x.com", "twitter.com"],
    "linkedin": ["linkedin.com"],
    "truth": ["truthsocial.com"],
}


def _normalize_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return f"https://{url}"


def _extract_text_and_links(html: str):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = " ".join(soup.stripped_strings)
    links = [a.get("href", "") for a in soup.select("a[href]")]
    meta_desc = ""
    meta_tag = soup.find("meta", attrs={"name": "description"})
    if meta_tag:
        meta_desc = meta_tag.get("content", "")
    return text, links, meta_desc


def _extract_socials(links: list[str]) -> dict[str, str]:
    result = {"facebook": "", "youtube": "", "x": "", "linkedin": "", "truth": ""}
    for link in links:
        link_lower = link.lower()
        for key, domains in SOCIAL_KEYS.items():
            if result[key]:
                continue
            if any(domain in link_lower for domain in domains):
                result[key] = link
    return result


def _decode_bing_target(raw_url: str) -> str:
    if not raw_url:
        return ""
    parsed = urlparse(raw_url)
    if "bing.com" not in parsed.netloc:
        return raw_url

    query = parse_qs(parsed.query)
    if "u" not in query or not query["u"]:
        return raw_url

    encoded = query["u"][0]
    if encoded.startswith("a1"):
        encoded = encoded[2:]

    try:
        padding = "=" * (-len(encoded) % 4)
        decoded = base64.urlsafe_b64decode((encoded + padding).encode("utf-8")).decode("utf-8", errors="ignore")
        if decoded.startswith("http://") or decoded.startswith("https://"):
            return decoded
    except Exception:
        return raw_url

    return raw_url


async def _search_websites(query: str, max_results: int = 30) -> list[str]:
    url = f"https://www.bing.com/search?q={quote_plus(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True, headers=headers) as client:
        resp = await client.get(url)
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    candidates: list[str] = []
    for anchor in soup.select("li.b_algo h2 a[href]"):
        href = unquote(anchor.get("href", "")).strip()
        href = _decode_bing_target(href)
        if not href or "bing.com/" in href:
            continue
        if href not in candidates:
            candidates.append(href)
        if len(candidates) >= max_results:
            break
    return candidates


async def _extract_company_from_website(
    website_url: str,
    context: CrawlContext,
    fetcher: FallbackFetcher,
) -> dict[str, str] | None:
    result = await fetcher.fetch(_normalize_url(website_url))
    if result is None:
        return None

    text, links, meta_desc = _extract_text_and_links(result.html)
    emails = EMAIL_PATTERN.findall(text)
    phones = PHONE_PATTERN.findall(text)
    socials = _extract_socials(links)

    title = ""
    soup = BeautifulSoup(result.html, "html.parser")
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    if not title:
        return None

    return {
        "name": title,
        "address": "",
        "city": "",
        "state": "",
        "website": result.final_url,
        "email": emails[0] if emails else "",
        "phone": phones[0] if phones else "",
        "short_description": meta_desc or text[:400],
        "facebook": socials["facebook"],
        "youtube": socials["youtube"],
        "x": socials["x"],
        "linkedin": socials["linkedin"],
        "truth": socials["truth"],
        "country": context.country,
        "region": context.region,
        "industry": context.industry,
        "source_url": website_url,
    }


class WebsiteDiscoveryConnector(BaseConnector):
    name = "website_discovery"

    def __init__(self):
        self.fetcher = FallbackFetcher()

    async def collect(self, context: CrawlContext) -> list[dict[str, str]]:
        composed = " ".join(
            [part for part in [context.query, context.country, context.region, context.industry, "company"] if part]
        ).strip()
        websites = await _search_websites(composed, max_results=context.max_companies * 2)

        companies: list[dict[str, str]] = []
        seen_sites: set[str] = set()
        for site in websites:
            if site in seen_sites:
                continue
            seen_sites.add(site)
            row = await _extract_company_from_website(site, context=context, fetcher=self.fetcher)
            if not row:
                continue
            companies.append(row)
            if len(companies) >= context.max_companies:
                break
        return companies
