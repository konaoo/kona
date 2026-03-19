"""将数据库中所有 UTC 时间戳 +8 小时，转为北京时间。

背景：SQLite 的 CURRENT_TIMESTAMP 返回 UTC，而非服务器本地时间。
本次迁移将已有数据统一为北京时间，配合代码改为 datetime('now','localtime')。

注意：auth_refresh_tokens 的时间字段保持 UTC（JWT 标准要求），不做迁移。
"""

import os
import sqlite3
from pathlib import Path

DATABASE_PATH = Path(
    os.getenv(
        "KONA_DATABASE_PATH",
        str(Path(__file__).resolve().parent.parent / "portfolio.db"),
    )
)

# (表名, 时间列名) — 需要 +8 小时的字段
_TIMESTAMP_COLUMNS = [
    ("portfolio", "created_at"),
    ("portfolio", "updated_at"),
    ("transactions", "created_at"),
    ("cash_assets", "created_at"),
    ("cash_assets", "updated_at"),
    ("other_assets", "created_at"),
    ("other_assets", "updated_at"),
    ("liabilities", "created_at"),
    ("liabilities", "updated_at"),
    ("users", "created_at"),
    ("users", "password_updated_at"),
    ("users", "password_reset_at"),
    ("users", "build_start_at"),
    ("users", "last_login"),
    ("users", "last_active_at"),
    ("admin_audit_logs", "created_at"),
    ("invite_codes", "created_at"),
    ("invite_codes", "used_at"),
    ("runtime_configs", "updated_at"),
    ("daily_snapshots", "updated_at"),
    ("daily_snapshot_market_breakdowns", "updated_at"),
    ("asset_adjustments", "created_at"),
    ("admin_api_policies", "updated_at"),
    ("price_alert_reports", "updated_at"),
    ("provider_test_reports", "updated_at"),
    ("user_daily_activity", "first_seen_at"),
    ("user_daily_activity", "last_seen_at"),
]


def _table_exists(cursor, table: str) -> bool:
    cursor.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table,),
    )
    return cursor.fetchone() is not None


def _column_exists(cursor, table: str, column: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def migrate() -> None:
    print(f"Migrating database: {DATABASE_PATH}")
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        updated = 0
        for table, col in _TIMESTAMP_COLUMNS:
            if not _table_exists(cursor, table):
                print(f"  跳过 {table}.{col} — 表不存在")
                continue
            if not _column_exists(cursor, table, col):
                print(f"  跳过 {table}.{col} — 列不存在")
                continue

            sql = (
                f"UPDATE {table} "
                f"SET {col} = datetime({col}, '+8 hours') "
                f"WHERE {col} IS NOT NULL"
            )
            cursor.execute(sql)
            count = cursor.rowcount
            updated += count
            print(f"  {table}.{col}: {count} 行已更新")

        conn.commit()
        print(f"迁移完成，共更新 {updated} 行")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
