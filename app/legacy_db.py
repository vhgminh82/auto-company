from __future__ import annotations
import os
from pathlib import Path
from typing import Any
import psycopg2
from psycopg2.extras import RealDictCursor

def _url() -> str:
    configured = os.getenv("SUPABASE_DATABASE_URL", "").strip()
    if configured:
        return configured
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        raise RuntimeError("SUPABASE_DATABASE_URL chưa được cấu hình")
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("SUPABASE_DATABASE_URL="):
            value=line.split("=",1)[1].strip().strip('"').strip("'")
            if value: return value
    raise RuntimeError("SUPABASE_DATABASE_URL chưa được cấu hình")

class Result:
    def __init__(self, cursor): self.cursor=cursor
    def fetchall(self): return self.cursor.fetchall()
    def fetchone(self): return self.cursor.fetchone()
    def __iter__(self): return iter(self.cursor.fetchall())
    def __getitem__(self, key): return self.cursor[key]

class Connection:
    def __init__(self):
        self.raw=psycopg2.connect(_url())
        self.raw.autocommit=False
    @property
    def row_factory(self): return RealDictCursor
    @row_factory.setter
    def row_factory(self, value): pass
    def execute(self, sql: str, params: Any = None):
        sql=sql.replace("last_insert_rowid()", "currval(pg_get_serial_sequence('companies','id'))")
        if sql.lstrip().upper().startswith("PRAGMA "):
            return Result(self.raw.cursor(cursor_factory=RealDictCursor))
        cur=self.raw.cursor(cursor_factory=RealDictCursor)
        cur.execute(sql.replace("?", "%s"), params or ())
        return Result(cur)
    def commit(self): self.raw.commit()
    def rollback(self): self.raw.rollback()
    def close(self): self.raw.close()

def connect_supabase(*args, **kwargs) -> Connection:
    return Connection()
