import sqlite3
import os
from datetime import datetime

DB_PATH = os.environ.get("DB_PATH", "/data/finance.db")


class Database:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self._init_db()

    def _conn(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    amount REAL NOT NULL,
                    type TEXT NOT NULL,
                    cat TEXT NOT NULL,
                    date TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now','localtime'))
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_date ON entries(user_id, date)")
            conn.commit()

    def add_entry(self, user_id: str, name: str, amount: float,
                  type_: str, cat: str, date: str):
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO entries (user_id, name, amount, type, cat, date) VALUES (?,?,?,?,?,?)",
                (user_id, name, amount, type_, cat, date)
            )
            conn.commit()

    def get_entries(self, user_id: str, year: int, month: int) -> list[dict]:
        prefix = f"{year}-{str(month).zfill(2)}"
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM entries WHERE user_id=? AND date LIKE ? ORDER BY date, id",
                (user_id, f"{prefix}%")
            ).fetchall()
        return [dict(r) for r in rows]

    def delete_entry_by_name(self, user_id: str, name: str, year: int, month: int) -> bool:
        prefix = f"{year}-{str(month).zfill(2)}"
        with self._conn() as conn:
            cur = conn.execute(
                "DELETE FROM entries WHERE user_id=? AND name LIKE ? AND date LIKE ? LIMIT 1",
                (user_id, f"%{name}%", f"{prefix}%")
            )
            conn.commit()
            return cur.rowcount > 0
