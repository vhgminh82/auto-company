import base64
import re
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import httpx
from bs4 import BeautifulSoup

from app.connectors.base import BaseConnector
from app.core.url_utils import is_blocked_url, normalize_url_for_index
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

INTERMEDIARY_DOMAINS = {
    "10times.com", "alibaba.com", "amazon.com", "bing.com", "crunchbase.com", "dnb.com",
    "eventseye.com", "facebook.com", "github.com", "glassdoor.com", "google.com",
    "indeed.com", "instagram.com", "linkedin.com", "mapquest.com", "pinterest.com",
    "reddit.com", "surveymonkey.com", "tradefairdates.com", "tripadvisor.com", "trustradius.com",
    "twitter.com", "wikipedia.org", "yellowpages.com", "yelp.com", "youtube.com",
}

RELEVANCE_STOP_WORDS = {
    "a", "an", "and", "at", "company", "companies", "com", "for", "in", "of", "the", "to",
}


def _normalize_url(url: str) -> str:
    if not url:
        return ""
    value = url.strip()
    if value.lower().startswith(("http://", "https://")):
        return value
    return f"https://{value}"


def _is_intermediary_url(url: str) -> bool:
    if is_blocked_url(url):
        return True
    host = (urlparse(url).hostname or "").lower().removeprefix("www.")
    return any(host == domain or host.endswith(f".{domain}") for domain in INTERMEDIARY_DOMAINS)


def _relevance_terms(context: CrawlContext) -> set[str]:
    raw = " ".join([context.query, context.industry, context.region, context.country])
    return {term for term in re.findall(r"[a-z0-9]+", raw.lower()) if len(term) > 2 and term not in RELEVANCE_STOP_WORDS}


def _is_relevant_page(text: str, title: str, meta_desc: str, context: CrawlContext) -> bool:
    terms = _relevance_terms(context)
    if not terms:
        return True
    searchable = f"{title} {meta_desc} {text[:5000]}".lower()
    return any(term in searchable for term in terms)


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
    if _is_intermediary_url(website_url):
        return None
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

    if not title or not _is_relevant_page(text, title, meta_desc, context):
        return None

    return {
        "name": title,
        "address": "",
        "city": "",
        "state": "",
        "website": normalize_url_for_index(result.final_url or website_url),
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
            site_key = normalize_url_for_index(site)
            if not site_key or _is_intermediary_url(site_key) or site_key in seen_sites:
                continue
            seen_sites.add(site_key)
            row = await _extract_company_from_website(site, context=context, fetcher=self.fetcher)
            if not row:
                continue
            companies.append(row)
            if len(companies) >= context.max_companies:
                break
        return companies
