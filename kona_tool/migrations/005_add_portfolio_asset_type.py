import sqlite3
import sys
from pathlib import Path

# Add parent dir to path
sys.path.append(str(Path(__file__).parent.parent))
from config import DATABASE_PATH
from core.asset_type import infer_asset_type


def migrate():
    print(f"Migrating database: {DATABASE_PATH}")
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA table_info(portfolio)")
        cols = [row[1] for row in cursor.fetchall()]
        if 'asset_type' not in cols:
            cursor.execute("ALTER TABLE portfolio ADD COLUMN asset_type TEXT DEFAULT 'a'")
            print("Added asset_type column to portfolio")

        # Backfill
        cursor.execute("SELECT code, name FROM portfolio WHERE asset_type IS NULL OR asset_type = ''")
        rows = cursor.fetchall()
        for code, name in rows:
            asset_type = infer_asset_type(code, name)
            cursor.execute(
                "UPDATE portfolio SET asset_type = ? WHERE code = ?",
                (asset_type, code)
            )
        if rows:
            print(f"Backfilled asset_type for {len(rows)} records")

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
