import os
import sqlite3
from pathlib import Path

DATABASE_PATH = Path(
    os.getenv(
        "KONA_DATABASE_PATH",
        str(Path(__file__).resolve().parent.parent / "portfolio.db"),
    )
)


def migrate():
    print(f"Migrating database: {DATABASE_PATH}")
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    def table_exists(name: str) -> bool:
        cursor.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
            (name,),
        )
        return cursor.fetchone() is not None

    try:
        if not table_exists("users"):
            cursor.execute(
                """
                CREATE TABLE users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT,
                    legacy_needs_password_setup INTEGER NOT NULL DEFAULT 0,
                    password_updated_at TIMESTAMP,
                    nickname TEXT,
                    avatar TEXT,
                    register_method TEXT,
                    phone TEXT,
                    user_number INTEGER,
                    is_admin INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT datetime('now','localtime'),
                    last_login TIMESTAMP
                )
                """
            )
        else:
            cursor.execute("PRAGMA table_info(users)")
            cols = [row[1] for row in cursor.fetchall()]
            needs_rebuild = "email" in cols or "username" not in cols or "password_hash" not in cols
            if needs_rebuild:
                cursor.execute("ALTER TABLE users RENAME TO users_old_008")
                cursor.execute(
                    """
                    CREATE TABLE users (
                        id TEXT PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT,
                        legacy_needs_password_setup INTEGER NOT NULL DEFAULT 0,
                        password_updated_at TIMESTAMP,
                        nickname TEXT,
                        avatar TEXT,
                        register_method TEXT,
                        phone TEXT,
                        user_number INTEGER,
                        is_admin INTEGER NOT NULL DEFAULT 0,
                        status TEXT NOT NULL DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT datetime('now','localtime'),
                        last_login TIMESTAMP
                    )
                    """
                )
                cursor.execute(
                    """
                    SELECT id,
                           COALESCE(NULLIF(TRIM(LOWER(REPLACE(REPLACE(REPLACE(
                               CASE WHEN email IS NOT NULL THEN email ELSE id END,
                               '@', '_'
                           ), '.', '_'), '-', '_'))), ''), id) AS raw_username,
                           nickname,
                           avatar,
                           register_method,
                           phone,
                           user_number,
                           is_admin,
                           status,
                           created_at,
                           last_login
                    FROM users_old_008
                    """
                )
                rows = cursor.fetchall()
                used = set()
                for i, row in enumerate(rows, start=1):
                    user_id = str(row["id"])
                    raw = str(row["raw_username"] or user_id).lower()
                    raw = "".join(ch if (ch.isalnum() or ch == "_") else "_" for ch in raw)
                    raw = raw.strip("_")
                    if not raw:
                        raw = "user"
                    if not raw[0].isalpha():
                        raw = f"u_{raw}"
                    if len(raw) < 4:
                        raw = (raw + "user")[:4]
                    base = raw[:24]
                    candidate = base
                    idx = 1
                    while candidate in used:
                        suffix = f"_{idx}"
                        candidate = f"{base[:24-len(suffix)]}{suffix}"
                        idx += 1
                    used.add(candidate)

                    cursor.execute(
                        """
                        INSERT INTO users (
                            id, username, password_hash, legacy_needs_password_setup,
                            password_updated_at, nickname, avatar, register_method,
                            phone, user_number, is_admin, status, created_at, last_login
                        ) VALUES (?, ?, NULL, 1, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            user_id,
                            candidate,
                            row["nickname"],
                            row["avatar"],
                            row["register_method"] or "legacy_email_otp",
                            row["phone"],
                            row["user_number"] or (10000 + i),
                            int(row["is_admin"] or 0),
                            row["status"] or "active",
                            row["created_at"],
                            row["last_login"],
                        ),
                    )
                cursor.execute("DROP TABLE IF EXISTS users_old_008")

        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username_unique ON users(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_status ON users(status)")

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS invite_codes (
                code TEXT PRIMARY KEY,
                batch_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_by TEXT,
                created_at TIMESTAMP DEFAULT datetime('now','localtime'),
                used_by_user_id TEXT,
                used_at TIMESTAMP,
                note TEXT
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_invite_codes_status ON invite_codes(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_invite_codes_batch_id ON invite_codes(batch_id)")

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_refresh_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                token_hash TEXT UNIQUE NOT NULL,
                device_id TEXT,
                issued_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                revoked_at TIMESTAMP,
                last_used_at TIMESTAMP
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_auth_refresh_tokens_user_id ON auth_refresh_tokens(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_auth_refresh_tokens_expires_at ON auth_refresh_tokens(expires_at)")

        cursor.execute("DROP TABLE IF EXISTS email_verification_codes")

        conn.commit()
        print("Migration completed successfully!")
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
