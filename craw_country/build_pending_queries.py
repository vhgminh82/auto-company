"""Build queries only for active keyword/location groups that are not marked V."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.legacy_db import connect_supabase
from pathlib import Path


def lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def normalize(value: str) -> str:
    value = re.sub(r"\([^)]*\)", "", (value or "").lower())
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def location(row: dict) -> str:
    raw_city = (row["city"] or "").strip().casefold()
    city = normalize(row["city"] or "")
    state = normalize(row["state"] or "")
    raw_country = (row["country"] or "").strip().casefold()
    country = normalize(row["country"] or "")
    state_part = "" if state == country else state
    place = state_part if raw_city.startswith(("toàn ", "toan ")) else f"{city} {state_part}".strip()
    if raw_country in {"hoa kỳ", "hoa ky", "united states", "usa"}:
        country = "usa"
    return f"{place} {country}".strip()


parser = argparse.ArgumentParser()
parser.add_argument("--database", required=True)
parser.add_argument("--completed", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()

completed_path = Path(args.completed)
completed = {normalize(query) for query in lines(completed_path)} if completed_path.is_file() else set()
connection = connect_supabase(args.database)
connection.row_factory = dict
try:
    keyword_rows = connection.execute(
        "SELECT position, group_position, keyword, active FROM country_keywords "
        "WHERE trim(keyword) != '' ORDER BY group_position, active DESC, position"
    ).fetchall()
    active_by_group: dict[int, dict] = {}
    for keyword in keyword_rows:
        group = int(keyword["group_position"])
        if group not in active_by_group or int(keyword["active"] or 0) == 1:
            active_by_group[group] = keyword

    pending = []
    seen = set()
    sources = connection.execute("SELECT * FROM country_sources ORDER BY id").fetchall()
    for source in sources:
        place = location(source)
        if not place:
            continue
        for group, keyword in active_by_group.items():
            column = f"keyword_{group}"
            if column not in source.keys() or (source[column] or "").strip().upper() == "V":
                continue
            query = f'{(keyword["keyword"] or "").strip()} {place}'.strip()
            key = normalize(query)
            if key in completed:
                connection.execute(f"UPDATE country_sources SET {column} = 'V' WHERE id = ?", (source["id"],))
                continue
            if key and key not in seen:
                pending.append(query)
                seen.add(key)
    connection.commit()
finally:
    connection.close()

Path(args.output).write_text("\n".join(pending) + ("\n" if pending else ""), encoding="utf-8")
print(len(pending))



