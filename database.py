import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "stratedge.db"


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS business_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_name TEXT NOT NULL,
                industry TEXT NOT NULL,
                target_audience TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS strategy_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER REFERENCES business_profiles(id),
                goals TEXT NOT NULL,
                budget TEXT NOT NULL,
                strategy_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)


def save_profile(business_name: str, industry: str, target_audience: str) -> int:
    with _connect() as conn:
        row = conn.execute(
            "SELECT id FROM business_profiles WHERE business_name = ? AND industry = ? AND target_audience = ?",
            (business_name, industry, target_audience),
        ).fetchone()
        if row:
            return row["id"]
        cursor = conn.execute(
            "INSERT INTO business_profiles (business_name, industry, target_audience) VALUES (?, ?, ?)",
            (business_name, industry, target_audience),
        )
        return cursor.lastrowid


def save_strategy(profile_id: int, goals: str, budget: str, strategy_text: str):
    with _connect() as conn:
        conn.execute(
            "INSERT INTO strategy_history (profile_id, goals, budget, strategy_text) VALUES (?, ?, ?, ?)",
            (profile_id, goals, budget, strategy_text),
        )


def get_all_profiles() -> list:
    """Returns one record per unique business_name (the most recent entry for each)."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT business_name, industry, target_audience
            FROM business_profiles
            GROUP BY business_name
            ORDER BY MAX(created_at) DESC
            """
        ).fetchall()
    return rows


def get_strategies_for_business(business_name: str) -> list:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT s.id, s.goals, s.budget, s.strategy_text, s.created_at,
                   p.business_name, p.industry
            FROM strategy_history s
            JOIN business_profiles p ON p.id = s.profile_id
            WHERE p.business_name = ?
            ORDER BY s.created_at DESC
            """,
            (business_name,),
        ).fetchall()
    return rows


def get_recent_strategies(limit: int = 10) -> list:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT s.id, s.goals, s.budget, s.strategy_text, s.created_at,
                   p.business_name, p.industry
            FROM strategy_history s
            JOIN business_profiles p ON p.id = s.profile_id
            ORDER BY s.created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return rows


# --- Auth ---

def create_user(name: str, email: str, password_hash: str) -> int:
    with _connect() as conn:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email.lower().strip(), password_hash),
        )
        return cursor.lastrowid


def get_user_by_email(email: str):
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE email = ?", (email.lower().strip(),)
        ).fetchone()


def get_user_by_id(user_id: int):
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()


def create_reset_token(user_id: int, token: str, expires_at: str):
    with _connect() as conn:
        conn.execute(
            "INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (?, ?, ?)",
            (user_id, token, expires_at),
        )


def get_reset_token(token: str):
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM password_reset_tokens WHERE token = ? AND used = 0",
            (token,),
        ).fetchone()


def mark_token_used(token: str):
    with _connect() as conn:
        conn.execute(
            "UPDATE password_reset_tokens SET used = 1 WHERE token = ?", (token,)
        )


def update_user_password(user_id: int, password_hash: str):
    with _connect() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id)
        )
