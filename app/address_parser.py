from __future__ import annotations

import re

US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia",
}
US_STATE_CODES = "|".join(US_STATES)
US_CITY_STATE = re.compile(rf"(?:^|,\s*)([^,]+),\s*({US_STATE_CODES})\s+\d{{5}}(?:-\d{{4}})?(?:,|$)", re.I)


def split_address(address: str, country: str = "") -> tuple[str, str]:
    text = " ".join(str(address or "").split())
    if not text:
        return "", ""
    match = US_CITY_STATE.search(text)
    if match:
        return match.group(1).strip(), US_STATES[match.group(2).upper()]
    parts = [part.strip() for part in text.split(",") if part.strip()]
    if parts and parts[-1].lower() in {"united states", "usa", "us", "vietnam", "vn", "canada", "germany", "japan"}:
        parts.pop()
    if len(parts) >= 2:
        state = re.sub(r"\s+\d{4,6}(?:-\d{4})?$", "", parts[-1]).strip()
        return parts[-2], state
    return "", ""
