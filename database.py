# -*- coding: utf-8 -*-
from pathlib import Path
import sqlite3
from data import data

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "rewards.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section TEXT NOT NULL,
            reward_type TEXT NOT NULL,
            job TEXT NOT NULL,
            amount TEXT NOT NULL,
            currency TEXT NOT NULL DEFAULT 'جنيه',
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute("SELECT COUNT(*) AS c FROM rewards")
    count = cur.fetchone()["c"]
    if count == 0:
        rows = []
        for item in data:
            rows.append(
                (
                    str(item.get("القسم", "")),
                    str(item.get("نوع_المكافأة", "")),
                    str(item.get("وظيفة", "")),
                    str(item.get("الفئة_بالجنيه", "")),
                    str(item.get("العملة", "جنيه")),
                    str(item.get("ملاحظات", "")),
                )
            )
        cur.executemany(
            """
            INSERT INTO rewards
            (section, reward_type, job, amount, currency, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
    conn.commit()
    conn.close()
    return DB_PATH


def _row_to_dict(row):
    return {
        "id": row["id"],
        "القسم": row["section"],
        "نوع_المكافأة": row["reward_type"],
        "وظيفة": row["job"],
        "الفئة_بالجنيه": row["amount"],
        "العملة": row["currency"],
        "ملاحظات": row["notes"],
    }


def get_all_rewards():
    init_db()
    conn = get_connection()
    rows = conn.execute("SELECT * FROM rewards ORDER BY id").fetchall()
    conn.close()
    return [_row_to_dict(row) for row in rows]


def search_rewards(query="", reward_type=""):
    init_db()
    query = (query or "").strip()
    reward_type = (reward_type or "").strip()
    conn = get_connection()
    sql = "SELECT * FROM rewards WHERE 1=1"
    params = []
    if query:
        sql += " AND (job LIKE ? OR reward_type LIKE ? OR section LIKE ? OR amount LIKE ? OR notes LIKE ?)"
        like = f"%{query}%"
        params.extend([like, like, like, like, like])
    if reward_type:
        sql += " AND reward_type = ?"
        params.append(reward_type)
    sql += " ORDER BY id"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [_row_to_dict(row) for row in rows]


def get_reward_types():
    init_db()
    conn = get_connection()
    rows = conn.execute("SELECT DISTINCT reward_type FROM rewards ORDER BY reward_type").fetchall()
    conn.close()
    return [row[0] for row in rows]


def get_reward_by_id(record_id):
    init_db()
    conn = get_connection()
    row = conn.execute("SELECT * FROM rewards WHERE id = ?", (record_id,)).fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


def add_reward(section, reward_type, job, amount, currency="جنيه", notes=""):
    init_db()
    section = (section or "").strip()
    reward_type = (reward_type or "").strip()
    job = (job or "").strip()
    amount = str(amount or "").strip()
    currency = (currency or "جنيه").strip()
    notes = (notes or "").strip()
    if not section or not reward_type or not job or not amount:
        raise ValueError("يجب إدخال القسم ونوع المكافأة والوظيفة وقيمة المكافأة.")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO rewards (section, reward_type, job, amount, currency, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (section, reward_type, job, amount, currency, notes),
    )
    record_id = cur.lastrowid
    conn.commit()
    conn.close()
    return record_id


def delete_reward(record_id):
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM rewards WHERE id = ?", (record_id,))
    deleted = cur.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def get_statistics():
    init_db()
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM rewards").fetchone()[0]
    jobs = conn.execute("SELECT COUNT(DISTINCT job) FROM rewards").fetchone()[0]
    types = conn.execute("SELECT COUNT(DISTINCT reward_type) FROM rewards").fetchone()[0]
    sections = conn.execute("SELECT COUNT(DISTINCT section) FROM rewards").fetchone()[0]
    conn.close()
    return {
        "إجمالي السجلات": total,
        "عدد الوظائف/البنود": jobs,
        "عدد أنواع المكافآت": types,
        "عدد الأقسام": sections,
  }
