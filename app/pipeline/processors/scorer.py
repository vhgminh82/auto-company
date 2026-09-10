def score_record(record: dict[str, str]) -> float:
    fields = [
        "name", "address", "city", "state", "website", "email", "phone", "short_description", "facebook",
        "youtube", "x", "linkedin", "truth",
    ]
    filled = sum(1 for field in fields if (record.get(field, "") or "").strip())
    base_score = filled / len(fields)

    reliability_bonus = 0.0
    if record.get("_domain_norm", ""):
        reliability_bonus += 0.1
    if record.get("email", ""):
        reliability_bonus += 0.05
    if record.get("phone", ""):
        reliability_bonus += 0.05

    return min(base_score + reliability_bonus, 1.0)


def attach_score(record: dict[str, str]) -> dict[str, str]:
    enriched = dict(record)
    enriched["quality_score"] = f"{score_record(record):.3f}"
    return enriched
