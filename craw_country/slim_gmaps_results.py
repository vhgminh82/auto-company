"""Convert raw Google Maps scraper CSVs to the company-sheet schema."""
import argparse
import csv
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

FIELDS = ["Tên", "địa chỉ", "quốc gia", "website", "lĩnh vực", "Phone", "email"]
SKIP_HOSTS = ("facebook.com", "instagram.com", "linkedin.com", "yelp.com", "yellowpages.com")


def root_url(value):
    value = (value or "").strip()
    if not value:
        return ""
    if not re.match(r"^https?://", value, re.I):
        value = "https://" + value
    host = (urlsplit(value).hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return f"https://{host}/" if host else ""


def country_from_row(row):
    value = (row.get("country") or "").strip()
    raw = (row.get("complete_address") or "").strip()
    try:
        parsed = json.loads(raw)
        value = str(parsed.get("country") or value).strip()
    except (json.JSONDecodeError, TypeError):
        pass
    return {"US": "Hoa Kỳ", "USA": "Hoa Kỳ", "United States": "Hoa Kỳ", "CA": "Canada"}.get(value, value)


def convert(input_root, output_root):
    output_root.mkdir(parents=True, exist_ok=True)
    seen = set()
    source_count = 0
    output_count = 0
    for source in sorted(input_root.rglob("query_*.csv")):
        source_count += 1
        relative = source.relative_to(input_root)
        target = output_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        rows = []
        with source.open(encoding="utf-8-sig", newline="", errors="replace") as handle:
            for raw in csv.DictReader(handle):
                website = root_url(raw.get("website"))
                if not website or any(host in website for host in SKIP_HOSTS):
                    continue
                title = (raw.get("title") or "").strip()
                address = (raw.get("address") or "").strip()
                key = website or (title.casefold(), address.casefold())
                if key in seen:
                    continue
                seen.add(key)
                rows.append({
                    "Tên": title,
                    "địa chỉ": address,
                    "quốc gia": country_from_row(raw),
                    "website": website,
                    "lĩnh vực": (raw.get("category") or "").strip(),
                    "Phone": (raw.get("phone") or "").strip(),
                    "email": (raw.get("emails") or "").strip(),
                })
        with target.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        output_count += len(rows)
    print(json.dumps({"raw_csv": source_count, "company_rows": output_count, "output": str(output_root)}, ensure_ascii=False))


parser = argparse.ArgumentParser()
parser.add_argument("--input", default="results")
parser.add_argument("--output", default="results_company")
args = parser.parse_args()
convert(Path(args.input), Path(args.output))
