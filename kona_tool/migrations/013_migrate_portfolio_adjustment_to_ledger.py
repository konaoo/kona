"""把旧 portfolio.adjustment 兼容迁到收益事件流水表。

第一阶段不清空 portfolio.adjustment，只补一份 ledger 兼容数据：
- event_type 固定为 manual_adjustment
- source 固定为 legacy_migration

这样旧页面和旧脚本还能继续跑，新读侧也能逐步切到流水聚合。
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

DATABASE_PATH = Path(
    os.getenv(
        "KONA_DATABASE_PATH",
        str(Path(__file__).resolve().parent.parent / "portfolio.db"),
    )
)


def migrate() -> None:
    print(f"迁移数据库: {DATABASE_PATH}")
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS portfolio_adjustment_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT '',
                code TEXT NOT NULL,
                event_type TEXT NOT NULL,
                amount REAL NOT NULL,
                curr TEXT NOT NULL DEFAULT 'CNY',
                note TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT 'manual',
                related_tx_id INTEGER,
                created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
                updated_at TIMESTAMP DEFAULT (datetime('now','localtime'))
            )
            """
        )

        cursor.execute(
            """
            SELECT
                COALESCE(user_id, '') AS user_id,
                code,
                COALESCE(curr, 'CNY') AS curr,
                COALESCE(adjustment, 0.0) AS adjustment
            FROM portfolio
            WHERE ABS(COALESCE(adjustment, 0.0)) > 1e-9
            """
        )
        rows = cursor.fetchall()
        inserted = 0

        for user_id, code, curr, adjustment in rows:
            cursor.execute(
                """
                SELECT 1
                FROM portfolio_adjustment_ledger
                WHERE user_id = ?
                  AND code = ?
                  AND source = 'legacy_migration'
                LIMIT 1
                """,
                (user_id or "", code),
            )
            if cursor.fetchone():
                continue

            cursor.execute(
                """
                INSERT INTO portfolio_adjustment_ledger (
                    user_id,
                    code,
                    event_type,
                    amount,
                    curr,
                    note,
                    source,
                    updated_at
                )
                VALUES (?, ?, 'manual_adjustment', ?, ?, '历史 adjustment 迁移', 'legacy_migration', datetime('now','localtime'))
                """,
                (user_id or "", code, float(adjustment or 0.0), curr or "CNY"),
            )
            inserted += 1

        conn.commit()
        print(f"迁移完成，新写入 {inserted} 条流水")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
