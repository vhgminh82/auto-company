"""Collect public contact emails and Facebook links from company websites.

CSV mode is the safe default. Sheet mode requires a Google service-account JSON
with access to the spreadsheet and the gspread package.
"""
import argparse, csv, json, re, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.legacy_db import connect_supabase
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
SOCIAL_RE = re.compile(r"https?://(?:www\.)?facebook\.com/[^\"'\s<>]+", re.I)
LINKEDIN_RE = re.compile(r"https?://(?:[a-z]{2,3}\.)?linkedin\.com/(?:company|in|school|show|posts)/[^\"'\s<>?#]+", re.I)
CONTACT_WORDS = ("contact", "about", "company", "enquiry", "inquiry", "location")
UA = "VCMoldContactResearch/1.0 (public business contact lookup)"
MAX_HTML_BYTES = 300_000

def clean_url(value):
    value = (value or "").strip()
    if not value: return ""
    if not re.match(r"^https?://", value, re.I): value = "https://" + value
    p = urlsplit(value)
    if not p.hostname: return ""
    host = p.hostname.lower()
    if host.startswith("www."): host = host[4:]
    return "https://" + host + "/"

def clean_email(value):
    value = value.replace("mailto:", "").strip().lower()
    value = value.replace("[at]", "@").replace(" (at) ", "@").replace("[dot]", ".")
    return value if EMAIL_RE.fullmatch(value) else ""

def email_list(*values):
    seen = set(); emails = []
    for value in values:
        for item in EMAIL_RE.findall(value or ""):
            email = clean_email(item)
            if email and email not in seen:
                seen.add(email); emails.append(email)
    return emails[:2]

def fetch(url, session, timeout):
    try:
        r = session.get(url, timeout=timeout, headers={"User-Agent": UA}, allow_redirects=True)
        if r.ok and "text/html" in r.headers.get("content-type", "").lower():
            return r.content[:MAX_HTML_BYTES].decode(r.encoding or "utf-8", errors="ignore"), r.url
    except requests.RequestException:
        pass
    return "", url

def enrich(url, timeout=15, delay=0.25):
    root = clean_url(url)
    if not root: return {"emails": "", "facebook": "", "linkedin": "", "status": "invalid_url"}
    s = requests.Session(); pages = [root]
    html, final = fetch(root, s, timeout)
    if not html: return {"emails": "", "facebook": "", "linkedin": "", "status": "unreachable"}
    soup = BeautifulSoup(html, "html.parser")
    site_host = (urlsplit(final).hostname or "").lower()
    if site_host.startswith("www."): site_host = site_host[4:]
    links = []
    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        if not href: continue
        if href.lower().startswith("mailto:"):
            links.append(href)
        elif urlsplit(href).hostname and "facebook.com" in urlsplit(href).hostname.lower():
            links.append(href)
        elif urlsplit(href).hostname and "linkedin.com" in urlsplit(href).hostname.lower():
            links.append(href)
        elif any(word in (a.get_text(" ") + " " + href).lower() for word in CONTACT_WORDS):
            links.append(urljoin(final, href))
    for link in links:
        if link.startswith("mailto:") or "facebook.com" in link.lower() or "linkedin.com" in link.lower(): continue
        if len(pages) >= 4: break
        if urlsplit(link).hostname == urlsplit(final).hostname and link not in pages: pages.append(link)
    emails, facebook, linkedin = set(), set(), set()
    for index, page in enumerate(pages):
        if index: time.sleep(delay)
        text = BeautifulSoup(html if index == 0 else fetch(page, s, timeout)[0], "html.parser")
        raw = str(text)
        for item in EMAIL_RE.findall(raw):
            e = clean_email(item)
            email_host = e.rsplit("@", 1)[-1] if "@" in e else ""
            same_site = email_host == site_host or email_host.endswith("." + site_host) or site_host.endswith("." + email_host)
            if e and same_site and not e.endswith((".png", ".jpg", ".jpeg", ".gif")): emails.add(e)
        for item in SOCIAL_RE.findall(raw):
            item = item.rstrip(".,);]").replace("%20", "").rstrip("/")
            if "/sharer" not in item and "/plugins/" not in item: facebook.add(item)
        for item in LINKEDIN_RE.findall(raw):
            item = item.rstrip(".,);]").split("?")[0].rstrip("/")
            if not any(x in item.lower() for x in ("/share", "/feed", "/login", "/jobs", "/learning")):
                linkedin.add(item)
    return {"emails": "; ".join(sorted(emails)[:5]), "facebook": "; ".join(sorted(facebook)[:3]), "linkedin": "; ".join(sorted(linkedin)[:3]), "status": "ok"}

def enrich_isolated(url, timeout=15, delay=0.25):
    """Run one crawl in a killable child process so malformed pages cannot hang the batch."""
    proc = None
    try:
        proc = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "single", url, "--timeout", str(timeout), "--delay", str(delay)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        stdout, _ = proc.communicate(timeout=30)
        if proc.returncode == 0 and stdout.strip():
            return json.loads(stdout.strip().splitlines()[-1])
    except subprocess.TimeoutExpired:
        if proc and proc.poll() is None:
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"emails": "", "facebook": "", "linkedin": "", "status": "timeout"}
    except (OSError, ValueError, json.JSONDecodeError):
        pass
    return {"emails": "", "facebook": "", "linkedin": "", "status": "timeout"}

def process_csv(args):
    with open(args.input, encoding="utf-8-sig", newline="") as f: rows = list(csv.DictReader(f))
    name_key = "title" if rows and "title" in rows[0] else "Tên"
    website_key = "website" if rows and "website" in rows[0] else "Website"
    email_key = "email" if rows and "email" in rows[0] else "Email"
    if "Facebook" not in rows[0] if rows else True:
        for row in rows: row.setdefault("Facebook", "")
    if "LinkedIn" not in rows[0] if rows else True:
        for row in rows: row.setdefault("LinkedIn", "")
    work = [(i, r) for i, r in enumerate(rows) if clean_url(r.get(website_key, ""))]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(enrich, r.get(website_key, ""), args.timeout, args.delay): i for i, r in work}
        for n, future in enumerate(as_completed(futures), 1):
            i = futures[future]
            try: result = future.result()
            except Exception as exc: result = {"emails":"", "facebook":"", "linkedin":"", "status":"error"}; print(f"row {i+2}: {exc}", file=sys.stderr)
            if not rows[i].get(email_key): rows[i][email_key] = result["emails"] or "chưa có"
            if not rows[i].get("Facebook"): rows[i]["Facebook"] = result["facebook"] or "chưa có"
            if not rows[i].get("LinkedIn"): rows[i]["LinkedIn"] = result["linkedin"] or "chưa có"
            print(f"[{n}/{len(work)}] {rows[i].get(name_key,'')} | {result['status']} | email={result['emails'] or '-'} | facebook={result['facebook'] or '-'} | linkedin={result['linkedin'] or '-'}", flush=True)
    fields = list(rows[0].keys()) if rows else ["Tên","địa chỉ","quốc gia","website","lĩnh vực","Phone","email","Facebook"]
    if "Facebook" not in fields: fields.append("Facebook")
    if "LinkedIn" not in fields: fields.append("LinkedIn")
    with open(args.output, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)

def _column_letter(index):
    """Convert a zero-based column index to a Sheets A1 column label."""
    label = ""
    index += 1
    while index:
        index, remainder = divmod(index - 1, 26)
        label = chr(65 + remainder) + label
    return label

def process_sheet(args):
    try: import gspread
    except ImportError: raise SystemExit("Sheet mode cần cài: pip install gspread google-auth")
    gc = gspread.service_account(filename=args.credentials)
    ws = gc.open_by_key(args.spreadsheet_id).worksheet(args.sheet)
    values = ws.get_all_values()
    if not values: raise SystemExit("Tab company đang trống")
    header = values[0]
    header_lookup = {str(name).strip().lower(): index for index, name in enumerate(header)}
    for name in ("email", "facebook", "linkedin"):
        if name not in header_lookup:
            header.append(name); ws.update_cell(1, len(header), name)
            header_lookup[name] = len(header) - 1
    website_col = header_lookup.get("website")
    email_col = header_lookup["email"]
    fb_col = header_lookup["facebook"]
    li_col = header_lookup["linkedin"]
    if website_col is None: raise SystemExit("Không tìm thấy cột website trong tab company")
    tasks = [(i, row) for i, row in enumerate(values[1:], 2)
             if len(row)>website_col and clean_url(row[website_col])
             and (len(row) <= email_col or not row[email_col].strip())]
    pending_updates=[]
    total_updates=0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures={pool.submit(enrich,row[website_col],args.timeout,args.delay):(i,row) for i,row in tasks}
        for n,f in enumerate(as_completed(futures),1):
            i,row=futures[f]
            try:
                result=f.result()
            except Exception as exc:
                result={"emails":"","facebook":"","linkedin":"","status":"error"}
                print(f"row {i}: {exc}", file=sys.stderr, flush=True)
            current_email=row[email_col] if len(row)>email_col else ""
            if not current_email.strip(): pending_updates.append({"range":f"{_column_letter(email_col)}{i}","values":[[result["emails"] or "chưa có"]]})
            current_fb=row[fb_col] if len(row)>fb_col else ""
            if not current_fb.strip() and result["facebook"]: pending_updates.append({"range":f"{_column_letter(fb_col)}{i}","values":[[result["facebook"]]]})
            current_li=row[li_col] if len(row)>li_col else ""
            if not current_li.strip() and result["linkedin"]: pending_updates.append({"range":f"{_column_letter(li_col)}{i}","values":[[result["linkedin"]]]})
            print(f"[{n}/{len(tasks)}] row {i} | {result['status']} | email={result['emails'] or '-'} | facebook={result['facebook'] or '-'} | linkedin={result['linkedin'] or '-'}", flush=True)
            if n % 100 == 0:
                if pending_updates:
                    ws.batch_update(pending_updates)
                    total_updates += len(pending_updates)
                    print(f"  >>> Đã cập nhật {len(pending_updates)} ô sau {n} kết quả.", flush=True)
                    pending_updates=[]
    if pending_updates:
        ws.batch_update(pending_updates)
        total_updates += len(pending_updates)
        print(f"  >>> Đã cập nhật {len(pending_updates)} ô ở lô cuối.", flush=True)
    print(f"Đã cập nhật {total_updates} ô trong tab {args.sheet}; đã xử lý {len(tasks)} website.")

def process_db(args):
    """Enrich SQLite company records directly; existing non-empty values are kept."""
    # Autocommit prevents a large UI read from blocking the crawler at batch commit.
    connection = connect_supabase(args.database)
    connection.row_factory = dict
    try:
        rows = connection.execute(
            """SELECT id, name, website, email, email_2, facebook, linkedin
               FROM companies
               WHERE trim(website) != ''
                 AND trim(coalesce(email, '')) = ''
               LIMIT 500"""
        ).fetchall()
        tasks = [row for row in rows if clean_url(row["website"])]
        if not tasks:
            return 0
        updated = found_fields = 0
        latest = ""
        progress_path = Path(args.progress) if args.progress else None
        def progress(state, current):
            if progress_path:
                progress_path.write_text(f"{state}|{current}|{len(tasks)}|{found_fields}|{latest}", encoding="utf-8")
        progress("RUNNING", 0)
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(enrich_isolated, row["website"], args.timeout, args.delay): row for row in tasks}
            for n, future in enumerate(as_completed(futures), 1):
                row = futures[future]
                try:
                    result = future.result()
                except Exception as exc:
                    result = {"emails": "", "facebook": "", "linkedin": "", "status": "error"}
                    print(f"id {row['id']}: {exc}", file=sys.stderr, flush=True)
                fields = []
                values = []
                emails = email_list(row["email"], row["email_2"], result["emails"])
                current_emails = email_list(row["email"], row["email_2"])
                if emails and row["email"] != emails[0]:
                    fields.append("email = ?"); values.append(emails[0])
                if len(emails) > 1 and row["email_2"] != emails[1]:
                    fields.append("email_2 = ?"); values.append(emails[1])
                if not emails and not row["email"].strip():
                    fields.append("email = ?"); values.append("chưa có")
                found_fields += max(0, len(emails) - len(current_emails))
                for field, result_key in (("facebook", "facebook"), ("linkedin", "linkedin")):
                    if not row[field].strip() and result[result_key]:
                        fields.append(f"{field} = ?")
                        values.append(result[result_key])
                        found_fields += 1
                if fields:
                    values.append(row["id"])
                    connection.execute(f"UPDATE companies SET {', '.join(fields)} WHERE id = ?", values)
                    updated += 1
                    latest = row["name"]
                progress("RUNNING", n)
        progress("DONE", len(tasks))
        return len(tasks)
    finally:
        connection.close()

if __name__ == "__main__":
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="mode")
    c=sub.add_parser("csv"); c.add_argument("--input",required=True); c.add_argument("--output",required=True)
    s=sub.add_parser("sheet"); s.add_argument("--credentials",required=True); s.add_argument("--spreadsheet-id",required=True); s.add_argument("--sheet",default="company")
    d=sub.add_parser("db"); d.add_argument("--database",required=True); d.add_argument("--progress")
    s=sub.add_parser("single"); s.add_argument("url")
    for p in (c,s,d): p.add_argument("--workers",type=int,default=8); p.add_argument("--timeout",type=int,default=15); p.add_argument("--delay",type=float,default=.25)
    args=ap.parse_args()
    if not args.mode: ap.error("choose csv or sheet mode")
    if args.mode == "single": print(json.dumps(enrich(args.url, args.timeout, args.delay), ensure_ascii=False))
    elif args.mode == "csv": process_csv(args)
    elif args.mode == "sheet": process_sheet(args)
    else:
        while process_db(args):
            pass




