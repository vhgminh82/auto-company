from __future__ import annotations

import re
import unicodedata


def _key(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or "").casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


# These are the only values allowed in Company.industry.  More specific groups
# come first so that, for example, a plastic moulding company is not classified
# as a generic mould maker.
INDUSTRY_RULES = (
    ("Ép nhựa", ("plastic", "polymer", "injection molding", "injection moulding", "thermoplastic", "rubber products", "plastic resin")),
    ("Khuôn", ("mold maker", "mould", "tool die", "tooling", "khuon")),
    ("Cơ khí chính xác", ("machine shop", "machining", "cnc", "metal fabricator", "metalworking", "laser cutting", "foundry", "welder", "precision")),
    ("Gỗ", ("wood", "lumber", "millwork", "cabinet", "furniture", "carpentry", "timber", "go")),
    ("Thực phẩm", ("food", "grocery", "bakery", "beverage", "restaurant", "catering", "meat", "seafood", "thuc pham")),
    ("May mặc", ("textile", "apparel", "clothing", "garment", "fashion", "sewing", "fabric", "tailor", "may mac")),
    ("Ô tô & phụ tùng", ("automotive", "auto parts", "vehicle", "truck", "car manufacturer", "o to", "phu tung")),
    ("Bao bì & in ấn", ("packaging", "printing", "label", "bao bi", "in an")),
    ("Điện tử & công nghệ", ("electronic", "electrical", "automation", "computer", "software", "telecom", "dien tu", "cong nghe")),
    ("Hóa chất & nhựa", ("chemical", "chemistry", "polyethylene", "polythene", "hoa chat")),
    ("Xây dựng & vật liệu", ("construction", "contractor", "building", "roof", "flooring", "plumbing", "hvac", "architect", "xay dung", "vat lieu")),
    ("Logistics & phân phối", ("logistics", "transport", "distribution", "warehouse", "freight", "shipping", "trucking", "phan phoi")),
    ("Y tế & chăm sóc sức khỏe", ("medical", "health", "dental", "pharmacy", "clinic", "hospital", "y te")),
    ("Máy móc & thiết bị", ("machinery", "machine", "equipment", "may moc", "thiet bi")),
    ("Nông nghiệp", ("agriculture", "agricultural", "farm", "nong nghiep")),
    ("Năng lượng", ("energy", "solar", "wind power", "nang luong")),
    ("Giày dép & da", ("shoe", "footwear", "leather", "giay", "da")),
    ("Nội thất & gia dụng", ("home", "household", "interior", "noi that", "gia dung")),
    ("Kim loại & gia công", ("metal", "steel", "aluminium", "aluminum", "welding", "kim loai", "gia cong")),
    ("Thương mại & bán lẻ", ("retail", "store", "wholesale", "shop", "dealer", "supplier", "trading", "thuong mai", "ban le")),
    ("Tư vấn & kỹ thuật", ("consult", "engineering", "engineer", "technical", "tu van", "ky thuat")),
    ("Sản xuất công nghiệp", ("manufacturing", "manufacturer", "industrial", "production", "san xuat")),
    ("Dịch vụ", ("service", "office", "repair", "cleaning", "inspector", "dich vu")),
)


def main_industry(value: str) -> str:
    raw = str(value or "").strip()
    key = _key(raw)
    if not key or key in {"chua co", "unknown", "n a", "na", "null", "none"}:
        return "chưa có"
    for canonical, _aliases in INDUSTRY_RULES:
        if key == _key(canonical):
            return canonical
    for canonical, aliases in INDUSTRY_RULES:
        if any(alias in key for alias in aliases):
            return canonical
    if key in {"khac", "other", "others", "miscellaneous"}:
        return "Khác"
    return "Khác"
