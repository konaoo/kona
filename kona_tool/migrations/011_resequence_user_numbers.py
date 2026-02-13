import os
import sqlite3
from pathlib import Path

DATABASE_PATH = Path(
    os.getenv(
        "KONA_DATABASE_PATH",
        str(Path(__file__).resolve().parent.parent / "portfolio.db"),
    )
)

START_USER_NUMBER = 10000


def _table_exists(cursor, table: str) -> bool:
    cursor.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table,),
    )
    return cursor.fetchone() is not None


def migrate() -> None:
    print(f"Migrating database: {DATABASE_PATH}")
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        if not _table_exists(cursor, "users"):
            raise RuntimeError("users table not found")

        cursor.execute(
            """
            SELECT id
            FROM users
            ORDER BY COALESCE(created_at, ''), id
            """
        )
        rows = cursor.fetchall()
        if not rows:
            print("No users found, nothing to resequence")
            conn.commit()
            return

        updates = 0
        for idx, row in enumerate(rows):
            new_no = START_USER_NUMBER + idx
            cursor.execute(
                "UPDATE users SET user_number = ? WHERE id = ?",
                (new_no, row["id"]),
            )
            updates += 1

        conn.commit()
        print(
            f"Migration 011 completed successfully: resequenced {updates} users "
            f"from {START_USER_NUMBER} to {START_USER_NUMBER + updates - 1}"
        )
    except Exception as exc:
        conn.rollback()
        print(f"Migration 011 failed: {exc}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
