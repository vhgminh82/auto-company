from __future__ import annotations


def main_industry(value: str) -> str:
    text = str(value or "").casefold()
    if not text:
        return "Khác"
    # Priority matters: plastic molding is distinct from mold/tool manufacturing.
    if any(word in text for word in ("plastic", "polymer", "injection molding", "thermoplastic", "rubber products", "resin")):
        return "Ép nhựa"
    if any(word in text for word in ("mold maker", "mould", "tool & die", "tool and die", "tooling")):
        return "Khuôn"
    if any(word in text for word in ("machine shop", "machining", "cnc", "metal fabricator", "metalworking", "laser cutting", "foundry", "welder", "precision")):
        return "Cơ khí chính xác"
    if any(word in text for word in ("wood", "lumber", "millwork", "cabinet", "furniture", "carpentry", "timber")):
        return "Gỗ"
    if any(word in text for word in ("food", "grocery", "bakery", "beverage", "restaurant", "catering", "meat", "seafood")):
        return "Thực phẩm"
    if any(word in text for word in ("textile", "apparel", "clothing", "garment", "fashion", "sewing", "fabric", "tailor")):
        return "May mặc"
    if any(word in text for word in ("automotive", "auto ", "car ", "vehicle", "truck")):
        return "Ô tô & phụ tùng"
    if any(word in text for word in ("packaging", "printing", "label")):
        return "Bao bì & in ấn"
    if any(word in text for word in ("electronic", "electrical", "automation", "computer", "software", "telecom")):
        return "Điện tử & công nghệ"
    if any(word in text for word in ("construction", "contractor", "building", "roof", "flooring", "plumbing", "hvac", "architect")):
        return "Xây dựng & vật liệu"
    if any(word in text for word in ("logistics", "transport", "distribution", "warehouse", "freight", "shipping", "trucking")):
        return "Logistics & phân phối"
    if any(word in text for word in ("medical", "health", "dental", "pharmacy", "clinic", "hospital")):
        return "Y tế & chăm sóc sức khỏe"
    if any(word in text for word in ("manufacturer", "industrial", "machinery", "equipment", "engineering", "manufacturer")):
        return "Sản xuất công nghiệp"
    if any(word in text for word in ("retail", "store", "wholesale", "shop", "dealer", "supplier")):
        return "Thương mại & bán lẻ"
    if any(word in text for word in ("consult", "service", "office", "repair", "cleaning", "inspector")):
        return "Dịch vụ"
    return "Khác"
