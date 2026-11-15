import sqlite3
from datetime import date

DB_NAME = "expenses.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                date TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)


def add_expense(amount, category, description, exp_date=None):
    exp_date = exp_date or date.today().isoformat()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO expenses (amount, category, description, date) VALUES (?, ?, ?, ?)",
            (amount, category, description, exp_date),
        )


def get_all_expenses():
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, amount, category, description, date FROM expenses ORDER BY date ASC, id ASC"
        ).fetchall()


def delete_expense(expense_id):
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        return cur.rowcount > 0


def total_by_category():
    with get_connection() as conn:
        return conn.execute(
            "SELECT category, SUM(amount) FROM expenses "
            "GROUP BY category COLLATE NOCASE ORDER BY SUM(amount) DESC"
        ).fetchall()


def monthly_total(month):  # month format: "2026-11"
    with get_connection() as conn:
        result = conn.execute(
            "SELECT SUM(amount) FROM expenses WHERE date LIKE ?", (month + "%",)
        ).fetchone()
        return result[0] or 0


def monthly_totals():
    with get_connection() as conn:
        return conn.execute(
            "SELECT substr(date, 1, 7), SUM(amount) FROM expenses GROUP BY 1 ORDER BY 1"
        ).fetchall()


def top_expenses(limit=5, month=None):  # month=None gives all-time
    query = "SELECT amount, category, description, date FROM expenses"
    params = []
    if month:
        query += " WHERE date LIKE ?"
        params.append(month + "%")
    query += " ORDER BY amount DESC LIMIT ?"
    params.append(limit)
    with get_connection() as conn:
        return conn.execute(query, params).fetchall()


def set_budget(amount):
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES ('monthly_budget', ?)",
            (str(amount),),
        )


def get_budget():
    with get_connection() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = 'monthly_budget'"
        ).fetchone()
        return float(row[0]) if row else None
