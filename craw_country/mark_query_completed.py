"""Mark the country-source keyword/location cell represented by a completed query."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.legacy_db import connect_supabase


def normalize(value: str) -> str:
    value = re.sub(r"\([^)]*\)", "", (value or "").lower())
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def location(row: dict) -> str:
    raw_city = (row["city"] or "").strip().casefold()
    city, state = normalize(row["city"] or ""), normalize(row["state"] or "")
    raw_country = (row["country"] or "").strip().casefold()
    country = "usa" if raw_country in {"hoa kỳ", "hoa ky", "united states", "usa"} else normalize(row["country"] or "")
    state_part = "" if state == country else state
    place = state_part if raw_city.startswith(("toàn ", "toan ")) else f"{city} {state_part}".strip()
    return f"{place} {country}".strip()


parser = argparse.ArgumentParser()
parser.add_argument("--database", required=True)
parser.add_argument("--query", required=True)
args = parser.parse_args()

target = normalize(args.query)
connection = connect_supabase(args.database)
connection.row_factory = dict
marked = 0
try:
    keywords = connection.execute(
        "SELECT group_position, keyword FROM country_keywords WHERE active = 1 AND trim(keyword) != ''"
    ).fetchall()
    sources = connection.execute("SELECT * FROM country_sources").fetchall()
    for source in sources:
        place = location(source)
        for keyword in keywords:
            group = int(keyword["group_position"])
            if normalize(f'{keyword["keyword"]} {place}') == target:
                connection.execute(f"UPDATE country_sources SET keyword_{group} = 'V' WHERE id = ?", (source["id"],))
                marked += 1
    connection.commit()
finally:
    connection.close()
print(marked)



