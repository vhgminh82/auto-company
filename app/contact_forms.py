from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.fetchers.browser_fetcher import BrowserFetcher
from app.fetchers.http_fetcher import HttpFetcher


CONTACT_WORDS = re.compile(r"contact|contact-us|get-in-touch|lien-he|lienhe|liên hệ|contato", re.I)
CAPTCHA_WORDS = re.compile(r"captcha|recaptcha|hcaptcha|turnstile|g-recaptcha|cf-turnstile", re.I)


@dataclass
class FormInfo:
    page_url: str
    form_index: int
    action: str
    method: str
    has_captcha: bool
    fields: list[dict]


def _same_site(a: str, b: str) -> bool:
    return (urlparse(a).hostname or "").lower().lstrip("www.") == (urlparse(b).hostname or "").lower().lstrip("www.")


def _label_for(element, soup: BeautifulSoup) -> str:
    if element.get("aria-label"):
        return element["aria-label"].strip()
    if element.get("placeholder"):
        return element["placeholder"].strip()
    if element.get("id"):
        label = soup.find("label", attrs={"for": element["id"]})
        if label:
            return label.get_text(" ", strip=True)
    return element.get("name") or element.get("type") or "field"


def inspect_html(page_url: str, html: str) -> tuple[list[FormInfo], list[str]]:
    soup = BeautifulSoup(html, "html.parser")
    forms: list[FormInfo] = []
    for index, form in enumerate(soup.find_all("form")):
        form_text = str(form)
        fields = []
        for element in form.find_all(["input", "textarea", "select"]):
            field_type = element.get("type", "text").lower()
            if field_type in {"hidden", "submit", "button", "reset", "file", "checkbox", "radio"}:
                continue
            name = element.get("name") or element.get("id")
            if not name:
                continue
            field_type = "select" if element.name == "select" else ("textarea" if element.name == "textarea" else field_type)
            options = []
            if element.name == "select":
                options = [{"value": option.get("value", ""), "label": option.get_text(" ", strip=True)} for option in element.find_all("option")]
            fields.append({
                "name": name,
                "type": field_type,
                "label": _label_for(element, soup),
                "required": element.has_attr("required"),
                "options": options,
            })
        action = urljoin(page_url, form.get("action") or page_url)
        forms.append(FormInfo(page_url, index, action, (form.get("method") or "post").lower(), bool(CAPTCHA_WORDS.search(form_text)), fields))

    links = []
    for link in soup.find_all("a", href=True):
        url = urljoin(page_url, link["href"])
        text = f"{link.get_text(' ', strip=True)} {url}"
        if _same_site(page_url, url) and CONTACT_WORDS.search(text) and url not in links:
            links.append(url)
    return forms, links[:8]


async def inspect_url(url: str) -> dict:
    normalized = url if url.startswith(("http://", "https://")) else f"https://{url}"
    fetch = await HttpFetcher().fetch(normalized)
    if not fetch:
        fetch = await BrowserFetcher().fetch(normalized)
    if not fetch:
        return {"url": normalized, "forms": [], "contact_pages": [], "error": "Không tải được URL."}
    forms, links = inspect_html(fetch.final_url, fetch.html)
    page_text = BeautifulSoup(fetch.html, "html.parser").get_text(" ", strip=True)[:12000]
    checked = {fetch.final_url}
    for contact_url in links:
        if contact_url in checked:
            continue
        page = await HttpFetcher().fetch(contact_url) or await BrowserFetcher().fetch(contact_url)
        if page:
            extra, _ = inspect_html(page.final_url, page.html)
            forms.extend(extra)
            checked.add(contact_url)
    return {"url": normalized, "final_url": fetch.final_url, "forms": [asdict(f) for f in forms], "contact_pages": links, "page_text": page_text, "error": None}


def detect_captcha_from_page(html: str) -> bool:
    return bool(CAPTCHA_WORDS.search(html))
