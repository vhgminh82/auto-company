def is_duplicate(a: dict[str, str], b: dict[str, str]) -> bool:
    domain_a = a.get("_domain_norm", "")
    domain_b = b.get("_domain_norm", "")
    if domain_a and domain_b and domain_a == domain_b:
        return True

    email_a = a.get("email", "")
    email_b = b.get("email", "")
    if email_a and email_b and email_a == email_b:
        return True

    name_a = a.get("_name_norm", "")
    name_b = b.get("_name_norm", "")
    city_a = (a.get("city", "") or "").lower()
    city_b = (b.get("city", "") or "").lower()
    state_a = (a.get("state", "") or "").lower()
    state_b = (b.get("state", "") or "").lower()

    if name_a and name_b and name_a == name_b and (city_a == city_b or state_a == state_b):
        return True

    return False


def dedupe_records(records: list[dict[str, str]]) -> list[list[dict[str, str]]]:
    groups: list[list[dict[str, str]]] = []

    for record in records:
        matched = False
        for group in groups:
            if any(is_duplicate(record, existing) for existing in group):
                group.append(record)
                matched = True
                break
        if not matched:
            groups.append([record])

    return groups
