import os
import sqlite3
from pathlib import Path

DATABASE_PATH = Path(
    os.getenv(
        "KONA_DATABASE_PATH",
        str(Path(__file__).resolve().parent.parent / "portfolio.db"),
    )
)


DEFAULT_POLICIES = [
    ("upstream.price", "upstream", 1, None, "Price upstream switch"),
    ("upstream.rate", "upstream", 1, None, "Rate upstream switch"),
    ("upstream.news", "upstream", 1, None, "News upstream switch"),
    ("api.auth", "api_group", 1, 120, "Auth API group policy"),
    ("api.portfolio", "api_group", 1, 240, "Portfolio API group policy"),
    ("api.news", "api_group", 1, 120, "News API group policy"),
]


def migrate() -> None:
    print(f"Migrating database: {DATABASE_PATH}")
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_api_policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scope_key TEXT UNIQUE NOT NULL,
                scope_type TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                limit_per_min INTEGER,
                note TEXT,
                updated_by TEXT,
                updated_at TIMESTAMP DEFAULT datetime('now','localtime')
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_admin_api_policies_scope_type ON admin_api_policies(scope_type)"
        )

        for scope_key, scope_type, enabled, limit_per_min, note in DEFAULT_POLICIES:
            cursor.execute(
                """
                INSERT INTO admin_api_policies
                (scope_key, scope_type, enabled, limit_per_min, note, updated_by)
                VALUES (?, ?, ?, ?, ?, 'migration_010')
                ON CONFLICT(scope_key) DO UPDATE SET
                    scope_type = excluded.scope_type,
                    note = COALESCE(admin_api_policies.note, excluded.note)
                """,
                (scope_key, scope_type, enabled, limit_per_min, note),
            )

        conn.commit()
        print("Migration 010 completed successfully")
    except Exception as exc:
        conn.rollback()
        print(f"Migration 010 failed: {exc}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
