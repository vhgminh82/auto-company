"""Incrementally append Google Maps places to the company sheet in batches."""
import argparse, csv, json, re
from pathlib import Path
from urllib.parse import urlsplit

FIELDS = ["Tên", "địa chỉ", "quốc gia", "website", "lĩnh vực", "Phone", "email", "facebook", "linkedin"]

def root_url(value):
    value = (value or "").strip()
    if not value: return ""
    if not re.match(r"^https?://", value, re.I): value = "https://" + value
    host = (urlsplit(value).hostname or "").lower()
    if host.startswith("www."): host = host[4:]
    return f"https://{host}/" if host else ""

def country_from_row(row):
    value = (row.get("country") or "").strip()
    try: value = str(json.loads(row.get("complete_address") or "{}").get("country") or value).strip()
    except (json.JSONDecodeError, TypeError): pass
    return {"US":"Hoa Kỳ", "USA":"Hoa Kỳ", "United States":"Hoa Kỳ", "CA":"Canada"}.get(value, value)

def key_for(row):
    website = root_url(row.get("website"))
    return "url:" + website if website else "name:" + (row.get("title") or row.get("Tên") or "").strip().casefold() + "|" + (row.get("address") or row.get("địa chỉ") or "").strip().casefold()

def load_state(path):
    if path.exists():
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
            for key, default in (("processed_files", []), ("pending", []), ("uploaded_keys", [])): state.setdefault(key, default)
            return state
        except (json.JSONDecodeError, OSError): pass
    return {"processed_files": [], "pending": [], "uploaded_keys": []}

def save_state(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

def read_candidates(files):
    out, keys = [], set()
    for source in files:
        with source.open(encoding="utf-8-sig", newline="", errors="replace") as handle:
            for raw in csv.DictReader(handle):
                website = root_url(raw.get("website"))
                if not website: continue
                row = {"Tên":(raw.get("title") or "").strip(), "địa chỉ":(raw.get("address") or "").strip(), "quốc gia":country_from_row(raw), "website":website, "lĩnh vực":(raw.get("category") or "").strip(), "Phone":(raw.get("phone") or "").strip(), "email":(raw.get("emails") or raw.get("email") or "").strip(), "facebook":"", "linkedin":""}
                key = key_for(row)
                if key not in keys: keys.add(key); out.append({"key":key, "row":row})
    return out

def main(args):
    state_path, state = Path(args.state), load_state(Path(args.state))
    processed, uploaded = set(state["processed_files"]), set(state["uploaded_keys"])
    pending = {item["key"]: item for item in state["pending"]}
    files = sorted(Path(args.input_root).rglob("query_*.csv"))
    new_files = [p for p in files if str(p.resolve()) not in processed]
    for item in read_candidates(new_files):
        if item["key"] not in uploaded and item["key"] not in pending: pending[item["key"]] = item
    processed.update(str(p.resolve()) for p in new_files)
    uploaded_now = 0
    if len(pending) >= args.batch_size or args.flush:
        import gspread
        ws = gspread.service_account(filename=args.credentials).open_by_key(args.spreadsheet_id).worksheet(args.sheet)
        existing, existing_keys = ws.get_all_values(), set()
        if existing:
            header = {str(v).strip().casefold(): i for i, v in enumerate(existing[0])}
            for row in existing[1:]:
                website = row[header.get("website", 3)] if len(row) > header.get("website", 3) else ""
                title = row[header.get("tên", 0)] if len(row) > header.get("tên", 0) else ""
                address = row[header.get("địa chỉ", 1)] if len(row) > header.get("địa chỉ", 1) else ""
                existing_keys.add("url:" + root_url(website) if root_url(website) else "name:" + title.strip().casefold() + "|" + address.strip().casefold())
        for key in list(pending):
            if key in existing_keys: del pending[key]
        batch = list(pending.values()) if args.flush else list(pending.values())[:args.batch_size]
        if batch:
            ws.append_rows([[item["row"][field] for field in FIELDS] for item in batch], value_input_option="USER_ENTERED", insert_data_option="INSERT_ROWS", table_range="A1")
            for item in batch: pending.pop(item["key"], None); uploaded.add(item["key"])
            uploaded_now = len(batch)
    state.update(processed_files=sorted(processed), pending=list(pending.values()), uploaded_keys=sorted(uploaded))
    save_state(state_path, state)
    print(json.dumps({"new_files":len(new_files), "uploaded":uploaded_now, "pending":len(pending), "state":str(state_path)}, ensure_ascii=False))

parser = argparse.ArgumentParser()
parser.add_argument("--input-root", required=True); parser.add_argument("--state", required=True); parser.add_argument("--credentials", required=True); parser.add_argument("--spreadsheet-id", required=True); parser.add_argument("--sheet", default="company"); parser.add_argument("--batch-size", type=int, default=100); parser.add_argument("--flush", action="store_true")
main(parser.parse_args())
