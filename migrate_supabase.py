import csv, io, json, sqlite3, sys, traceback
from pathlib import Path
import psycopg2
from app.database import Base
import app.models.company, app.models.country_keyword, app.models.country_source, app.models.crawl_visited, app.models.emkt

ROOT = Path(__file__).resolve().parent
URL = next(line.split("=", 1)[1].strip().strip('"').strip("'") for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines() if line.startswith("SUPABASE_DATABASE_URL="))
src = sqlite3.connect(ROOT / "companies.db")
src.row_factory = sqlite3.Row
pg = psycopg2.connect(URL)
cur = pg.cursor()
cur.execute("SET statement_timeout = 0")

try:
    for table in Base.metadata.sorted_tables:
        src_cols = {r[1] for r in src.execute(f'PRAGMA table_info("{table.name}")').fetchall()}
        if not src_cols:
            continue
        cols = [c.name for c in table.columns if c.name in src_cols]
        select_cols = ",".join('"' + c + '"' for c in cols)
        print(f"{table.name}: reading source...", flush=True)
        rows = src.execute(f'SELECT {select_cols} FROM "{table.name}"').fetchall()
        print(f"{table.name}: loaded {len(rows)}", flush=True)
        if not rows:
            print(f"{table.name}: 0", flush=True)
            continue
        quoted = ",".join('"' + c + '"' for c in cols)
        tmp = "tmp_migrate_" + table.name
        total = 0
        for off in range(0, len(rows), 500):
            batch = rows[off:off + 500]
            buf = io.StringIO()
            writer = csv.writer(buf, lineterminator="\n")
            for row in batch:
                vals = []
                for c in cols:
                    value = row[c]
                    if value is None:
                        vals.append("__NULL__")
                    elif isinstance(value, (dict, list)):
                        vals.append(json.dumps(value, ensure_ascii=False))
                    else:
                        vals.append(str(value))
                writer.writerow(vals)
            buf.seek(0)
            cur.execute(f'DROP TABLE IF EXISTS "{tmp}"')
            cur.execute(f'CREATE TEMP TABLE "{tmp}" (LIKE "{table.name}" INCLUDING DEFAULTS) ON COMMIT DROP')
            cur.copy_expert(f"""COPY "{tmp}" ({quoted}) FROM STDIN WITH (FORMAT CSV, NULL '__NULL__')""", buf)
            cur.execute(f'INSERT INTO "{table.name}" ({quoted}) SELECT {quoted} FROM "{tmp}" ON CONFLICT DO NOTHING')
            pg.commit()
            total += len(batch)
            if table.name == "companies" and total % 5000 == 0:
                print(f"{table.name}: {total}/{len(rows)}", flush=True)
        if "id" in table.c:
            cur.execute(f"""SELECT setval(pg_get_serial_sequence('{table.name}','id'), COALESCE((SELECT MAX(id) FROM "{table.name}"), 1), true)""")
        pg.commit()
        print(f"{table.name}: {total}/{len(rows)}", flush=True)
    print("ALL_DONE", flush=True)
except Exception:
    pg.rollback()
    traceback.print_exc()
    sys.exit(1)
finally:
    cur.close()
    pg.close()
    src.close()




