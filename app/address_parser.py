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
COUNTRIES = {
    "united states": "United States", "usa": "United States", "us": "United States",
    "vietnam": "Vietnam", "viet nam": "Vietnam", "vn": "Vietnam",
    "canada": "Canada", "united kingdom": "United Kingdom", "uk": "United Kingdom",
    "australia": "Australia", "germany": "Germany", "france": "France",
    "japan": "Japan", "singapore": "Singapore", "thailand": "Thailand",
    "south korea": "South Korea", "korea": "South Korea", "india": "India",
}


def parse_address(address: str, country: str = "") -> tuple[str, str, str]:
    text = " ".join(str(address or "").split())
    if not text:
        return "", "", ""
    parts = [part.strip() for part in text.split(",") if part.strip()]
    detected_country = ""
    if parts:
        tail = parts[-1].casefold().rstrip(".")
        detected_country = COUNTRIES.get(tail, "")
        if detected_country:
            parts.pop()
    detected_country = detected_country or COUNTRIES.get(str(country or "").strip().casefold(), str(country or "").strip())
    body = ", ".join(parts)
    match = US_CITY_STATE.search(body + ("," if body else ""))
    if match:
        return detected_country or "United States", match.group(1).strip(), US_STATES[match.group(2).upper()]
    if len(parts) >= 2:
        state = re.sub(r"\s+\d{4,6}(?:-\d{4})?$", "", parts[-1]).strip()
        city = parts[-2]
        # For Vietnam, a district is not a state; retain the province/city as city.
        if detected_country == "Vietnam" and len(parts) >= 3:
            city, state = parts[-1], ""
        return detected_country, city, state
    return detected_country, (parts[0] if parts else ""), ""


def split_address(address: str, country: str = "") -> tuple[str, str]:
    _, city, state = parse_address(address, country)
    return city, state
