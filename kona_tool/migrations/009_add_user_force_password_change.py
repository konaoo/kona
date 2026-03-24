import os
import sqlite3
from pathlib import Path

DATABASE_PATH = Path(
    os.getenv(
        "KONA_DATABASE_PATH",
        str(Path(__file__).resolve().parent.parent / "portfolio.db"),
    )
)


def _column_exists(cursor, table: str, column: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table})")
    return column in {row[1] for row in cursor.fetchall()}


def migrate() -> None:
    print(f"Migrating database: {DATABASE_PATH}")
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='users' LIMIT 1"
        )
        if cursor.fetchone() is None:
            raise RuntimeError("users table not found")

        if not _column_exists(cursor, "users", "must_change_password"):
            cursor.execute(
                "ALTER TABLE users ADD COLUMN must_change_password INTEGER NOT NULL DEFAULT 0"
            )
        if not _column_exists(cursor, "users", "password_reset_at"):
            cursor.execute("ALTER TABLE users ADD COLUMN password_reset_at TIMESTAMP")
        if not _column_exists(cursor, "users", "password_reset_by"):
            cursor.execute("ALTER TABLE users ADD COLUMN password_reset_by TEXT")

        cursor.execute(
            "UPDATE users SET must_change_password = 0 WHERE must_change_password IS NULL"
        )
        conn.commit()
        print("Migration 009 completed successfully")
    except Exception as exc:
        conn.rollback()
        print(f"Migration 009 failed: {exc}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
