import json
import os
import sqlite3
from pathlib import Path

ROOT = Path(os.environ.get("SPHEREX_DATA_DIR", Path(__file__).resolve().parents[1] / "data"))
ROOT.mkdir(parents=True, exist_ok=True)

def connect():
    db = sqlite3.connect(ROOT / "workspace.sqlite", timeout=30)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("CREATE TABLE IF NOT EXISTS records (kind TEXT, id TEXT, body TEXT, PRIMARY KEY(kind,id))")
    return db

def put(kind, id, body):
    with connect() as db:
        db.execute("INSERT OR REPLACE INTO records VALUES (?,?,?)", (kind, id, json.dumps(body, allow_nan=False)))

def get(kind, id):
    with connect() as db:
        row = db.execute("SELECT body FROM records WHERE kind=? AND id=?", (kind, id)).fetchone()
    return json.loads(row[0]) if row else None
