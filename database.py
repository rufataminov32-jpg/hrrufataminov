"""
database.py — SQLite orqali xodimlar va hisobotlarni boshqarish.
"""

import sqlite3
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str = "reports.db"):
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ─── Init ────────────────────────────────────────────────────────────────
    def init(self):
        """Jadval mavjud bo'lmasa yaratadi."""
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS employees (
                    user_id          INTEGER PRIMARY KEY,
                    full_name        TEXT    NOT NULL,
                    username         TEXT    DEFAULT '',
                    last_report_date TEXT    DEFAULT ''
                )
            """)
            conn.commit()
        logger.info("Ma'lumotlar bazasi tayyor.")

    # ─── CRUD ────────────────────────────────────────────────────────────────
    def add_employee(self, user_id: int, full_name: str, username: str = ""):
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO employees (user_id, full_name, username)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    full_name = excluded.full_name,
                    username  = excluded.username
                """,
                (user_id, full_name, username),
            )
            conn.commit()

    def remove_employee(self, user_id: int):
        with self._conn() as conn:
            conn.execute("DELETE FROM employees WHERE user_id = ?", (user_id,))
            conn.commit()

    def is_employee(self, user_id: int) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM employees WHERE user_id = ?", (user_id,)
            ).fetchone()
        return row is not None

    def get_employee_name(self, user_id: int) -> str:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT full_name FROM employees WHERE user_id = ?", (user_id,)
            ).fetchone()
        return row["full_name"] if row else str(user_id)

    def get_all_employees(self) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT user_id, full_name, username, last_report_date FROM employees ORDER BY full_name"
            ).fetchall()
        return [dict(r) for r in rows]

    # ─── Hisobot yangilash ───────────────────────────────────────────────────
    def update_report(self, user_id: int, report_date: str):
        with self._conn() as conn:
            conn.execute(
                "UPDATE employees SET last_report_date = ? WHERE user_id = ?",
                (report_date, user_id),
            )
            conn.commit()

    def get_last_report_date(self, user_id: int) -> Optional[str]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT last_report_date FROM employees WHERE user_id = ?", (user_id,)
            ).fetchone()
        return row["last_report_date"] if row else None
