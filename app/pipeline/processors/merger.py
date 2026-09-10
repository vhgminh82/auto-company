PREFERRED_FIELDS = [
    "website", "email", "phone", "short_description", "facebook", "youtube", "x", "linkedin", "truth",
]


def _completeness_score(record: dict[str, str]) -> int:
    score = 0
    for key in [
        "name", "address", "city", "state", "website", "email", "phone", "short_description", "facebook",
        "youtube", "x", "linkedin", "truth",
    ]:
        if (record.get(key, "") or "").strip():
            score += 1
    return score


def merge_group(records: list[dict[str, str]]) -> dict[str, str]:
    winner = max(records, key=_completeness_score)
    merged = dict(winner)

    for record in records:
        for key in PREFERRED_FIELDS:
            if not (merged.get(key, "") or "").strip() and (record.get(key, "") or "").strip():
                merged[key] = record[key]

    return merged
