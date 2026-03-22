"""
快照写入、历史曲线与同步版本数据库能力。

这一层只做：
- daily_snapshots 表兼容迁移
- 每日快照与分市场快照写入
- 历史曲线读取
- sync/bootstrap 版本号计算
"""
import hashlib
import json
import logging
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)
MARKET_BREAKDOWN_MARKETS = ("a", "hk", "us", "fund", "unallocated")


class SnapshotDatabaseMixin:
    """给 DatabaseManager 提供快照、历史与同步版本相关方法。"""

    def has_daily_snapshot(self, date_str: str, user_id: str = None) -> bool:
        """判断指定日期是否已有主快照。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        uid = user_id or ""
        try:
            cursor.execute(
                """
                SELECT 1
                FROM daily_snapshots
                WHERE date = ? AND user_id = ?
                LIMIT 1
                """,
                (str(date_str or ""), uid),
            )
            return cursor.fetchone() is not None
        finally:
            conn.close()

    def get_daily_snapshot_market_breakdown_map(
        self,
        date_str: str,
        user_id: str = None,
    ) -> Dict[str, float]:
        """读取指定日期的分市场拆分。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        uid = user_id or ""

        try:
            cursor.execute(
                """
                SELECT market, day_pnl
                FROM daily_snapshot_market_breakdowns
                WHERE date = ? AND user_id = ?
                """,
                (str(date_str or ""), uid),
            )
            result = {market: 0.0 for market in MARKET_BREAKDOWN_MARKETS}
            for row in cursor.fetchall():
                market = str(row["market"] or "").strip().lower()
                if market in result:
                    result[market] = float(row["day_pnl"] or 0.0)
            return result
        finally:
            conn.close()

    def _ensure_daily_snapshots_schema(self, cursor) -> None:
        """
        统一 daily_snapshots 表结构到：
        - user_id 非空（默认 ''）
        - 唯一键 UNIQUE(date, user_id)
        并对历史重复数据做去重（保留最新 id）。
        """
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='daily_snapshots'")
        row = cursor.fetchone()
        table_sql = (row[0] or "").upper() if row and row[0] else ""
        has_old_date_unique = "DATE TEXT NOT NULL UNIQUE" in table_sql
        has_new_unique = "UNIQUE(DATE, USER_ID)" in table_sql

        if has_old_date_unique or not has_new_unique:
            logger.info("Migrating daily_snapshots schema to UNIQUE(date, user_id)")
            cursor.execute("DROP TABLE IF EXISTS daily_snapshots_new")
            cursor.execute(
                """
                CREATE TABLE daily_snapshots_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    total_asset REAL NOT NULL,
                    total_invest REAL NOT NULL,
                    total_cash REAL NOT NULL,
                    total_other REAL NOT NULL,
                    total_liability REAL NOT NULL,
                    total_pnl REAL NOT NULL,
                    day_pnl REAL NOT NULL,
                    user_id TEXT NOT NULL DEFAULT '',
                    updated_at TIMESTAMP DEFAULT (datetime('now','localtime')),
                    UNIQUE(date, user_id)
                )
                """
            )

            cursor.execute(
                """
                INSERT INTO daily_snapshots_new (
                    date, total_asset, total_invest, total_cash,
                    total_other, total_liability, total_pnl, day_pnl, user_id, updated_at
                )
                SELECT
                    d.date, d.total_asset, d.total_invest, d.total_cash,
                    d.total_other, d.total_liability, d.total_pnl, d.day_pnl,
                    COALESCE(d.user_id, '') AS user_id,
                    d.updated_at
                FROM daily_snapshots d
                INNER JOIN (
                    SELECT MAX(id) AS id
                    FROM daily_snapshots
                    GROUP BY date, COALESCE(user_id, '')
                ) t ON d.id = t.id
                """
            )

            cursor.execute("DROP TABLE daily_snapshots")
            cursor.execute("ALTER TABLE daily_snapshots_new RENAME TO daily_snapshots")
            logger.info("daily_snapshots schema migration completed")

    def save_daily_snapshot_market_breakdown(
        self,
        date_str: str,
        day_pnl_by_market: Dict[str, float],
        total_day_pnl: float,
        user_id: str = None,
        source: str = "exact",
        confidence: float = 1.0,
        meta_by_market: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """保存每日分市场收益快照。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        uid = user_id or ""

        try:
            normalized = {k: 0.0 for k in MARKET_BREAKDOWN_MARKETS}
            for market in ("a", "hk", "us", "fund"):
                normalized[market] = float((day_pnl_by_market or {}).get(market, 0.0) or 0.0)
            explicit_unallocated = (day_pnl_by_market or {}).get("unallocated")
            if explicit_unallocated is None:
                allocated = sum(normalized[m] for m in ("a", "hk", "us", "fund"))
                normalized["unallocated"] = float(total_day_pnl or 0.0) - allocated
            else:
                normalized["unallocated"] = float(explicit_unallocated or 0.0)

            market_meta = meta_by_market or {}
            for market in MARKET_BREAKDOWN_MARKETS:
                payload = market_meta.get(market)
                meta_json = None
                if payload is not None:
                    try:
                        meta_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
                    except Exception:
                        meta_json = json.dumps({"raw": str(payload)}, ensure_ascii=False, separators=(",", ":"))
                cursor.execute(
                    """
                    INSERT INTO daily_snapshot_market_breakdowns
                    (date, user_id, market, day_pnl, source, confidence, meta_json, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
                    ON CONFLICT(date, user_id, market) DO UPDATE SET
                        day_pnl = excluded.day_pnl,
                        source = excluded.source,
                        confidence = excluded.confidence,
                        meta_json = excluded.meta_json,
                        updated_at = datetime('now','localtime')
                    """,
                    (
                        str(date_str),
                        uid,
                        market,
                        round(float(normalized[market]), 2),
                        str(source or "exact"),
                        float(confidence),
                        meta_json,
                    ),
                )
            conn.commit()
            return True
        except Exception as exc:
            logger.error("Failed to save market breakdown date=%s user_id=%s: %s", date_str, uid, exc)
            conn.rollback()
            return False
        finally:
            conn.close()

    def save_daily_snapshot_market_breakdown_partial(
        self,
        date_str: str,
        market_updates: Dict[str, float],
        user_id: str = None,
        source: str = "exact",
        confidence: float = 1.0,
        meta_by_market: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """只更新指定市场，不覆盖同一天的其他市场拆分。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        uid = user_id or ""

        try:
            clean_updates = {}
            for raw_market, raw_value in (market_updates or {}).items():
                market = str(raw_market or "").strip().lower()
                if market not in MARKET_BREAKDOWN_MARKETS:
                    continue
                clean_updates[market] = round(float(raw_value or 0.0), 2)

            if not clean_updates:
                return True

            market_meta = meta_by_market or {}
            for market, value in clean_updates.items():
                payload = market_meta.get(market)
                meta_json = None
                if payload is not None:
                    try:
                        meta_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
                    except Exception:
                        meta_json = json.dumps({"raw": str(payload)}, ensure_ascii=False, separators=(",", ":"))
                cursor.execute(
                    """
                    INSERT INTO daily_snapshot_market_breakdowns
                    (date, user_id, market, day_pnl, source, confidence, meta_json, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
                    ON CONFLICT(date, user_id, market) DO UPDATE SET
                        day_pnl = excluded.day_pnl,
                        source = excluded.source,
                        confidence = excluded.confidence,
                        meta_json = excluded.meta_json,
                        updated_at = datetime('now','localtime')
                    """,
                    (
                        str(date_str or ""),
                        uid,
                        market,
                        value,
                        str(source or "exact"),
                        float(confidence),
                        meta_json,
                    ),
                )
            conn.commit()
            return True
        except Exception as exc:
            logger.error(
                "Failed to partially save market breakdown date=%s user_id=%s: %s",
                date_str,
                uid,
                exc,
            )
            conn.rollback()
            return False
        finally:
            conn.close()

    def sync_daily_snapshot_day_pnl_from_breakdown(
        self,
        date_str: str,
        user_id: str = None,
    ) -> bool:
        """按分市场拆分回写指定日期的主快照 day_pnl。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        uid = user_id or ""

        try:
            cursor.execute(
                """
                SELECT COALESCE(SUM(day_pnl), 0.0) AS total
                FROM daily_snapshot_market_breakdowns
                WHERE date = ? AND user_id = ?
                """,
                (str(date_str or ""), uid),
            )
            row = cursor.fetchone()
            total = round(float((row["total"] if row else 0.0) or 0.0), 2)
            cursor.execute(
                """
                UPDATE daily_snapshots
                SET day_pnl = ?, updated_at = datetime('now','localtime')
                WHERE date = ? AND user_id = ?
                """,
                (total, str(date_str or ""), uid),
            )
            updated = int(cursor.rowcount or 0)
            conn.commit()
            return updated > 0
        except Exception as exc:
            logger.error(
                "Failed to sync day_pnl from breakdown date=%s user_id=%s: %s",
                date_str,
                uid,
                exc,
            )
            conn.rollback()
            return False
        finally:
            conn.close()

    def save_ledger_daily_snapshot(
        self,
        *,
        user_id: str,
        ledger_id: int,
        date_str: str,
        total_market_value: float = 0,
        total_cost: float = 0,
        total_pnl: float = 0,
        total_pnl_rate: float = 0,
        day_pnl: float = 0,
        holdings_count: int = 0,
    ) -> bool:
        """保存单个账本的每日快照。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO ledger_daily_snapshots (
                    user_id, ledger_id, date,
                    total_market_value, total_cost, total_pnl, total_pnl_rate,
                    day_pnl, holdings_count, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
                ON CONFLICT(user_id, ledger_id, date) DO UPDATE SET
                    total_market_value = excluded.total_market_value,
                    total_cost = excluded.total_cost,
                    total_pnl = excluded.total_pnl,
                    total_pnl_rate = excluded.total_pnl_rate,
                    day_pnl = excluded.day_pnl,
                    holdings_count = excluded.holdings_count,
                    created_at = datetime('now','localtime')
                """,
                (
                    user_id, ledger_id, date_str,
                    round(total_market_value, 2), round(total_cost, 2),
                    round(total_pnl, 2), round(total_pnl_rate, 2),
                    round(day_pnl, 2), holdings_count,
                ),
            )
            conn.commit()
            return True
        except Exception as exc:
            logger.error("Failed to save ledger daily snapshot: ledger=%s date=%s err=%s", ledger_id, date_str, exc)
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_ledger_history(self, user_id: str, ledger_id: int, limit: int = 365) -> List[Dict[str, Any]]:
        """获取指定账本的历史快照数据。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT date, total_market_value, total_cost, total_pnl, total_pnl_rate, day_pnl, holdings_count
                FROM ledger_daily_snapshots
                WHERE user_id = ? AND ledger_id = ?
                ORDER BY date ASC
                LIMIT ?
                """,
                (user_id, ledger_id, limit),
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def save_daily_snapshot(self, data: Dict[str, float], user_id: str = None, snapshot_date: str = None) -> bool:
        """保存每日资产快照。"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 优先用调用方传入的日期，保证和 market_breakdown 写同一天
        today = snapshot_date or data.get("snapshot_date") or datetime.now().strftime("%Y-%m-%d")
        uid = user_id or ""

        try:
            cursor.execute(
                """
                INSERT INTO daily_snapshots (
                    date, total_asset, total_invest, total_cash,
                    total_other, total_liability, total_pnl, day_pnl, user_id, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
                ON CONFLICT(date, user_id) DO UPDATE SET
                    total_asset = excluded.total_asset,
                    total_invest = excluded.total_invest,
                    total_cash = excluded.total_cash,
                    total_other = excluded.total_other,
                    total_liability = excluded.total_liability,
                    total_pnl = excluded.total_pnl,
                    day_pnl = excluded.day_pnl,
                    updated_at = datetime('now','localtime')
                """,
                (
                    today,
                    data.get("total_asset", 0),
                    data.get("total_invest", 0),
                    data.get("total_cash", 0),
                    data.get("total_other", 0),
                    data.get("total_liability", 0),
                    data.get("total_pnl", 0),
                    data.get("day_pnl", 0),
                    uid,
                ),
            )

            conn.commit()
            logger.info("Daily snapshot saved for %s", today)
            return True
        except Exception as exc:
            logger.error("Failed to save snapshot: %s", exc)
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_history(self, limit: int = 365, user_id: str = None) -> List[Dict[str, Any]]:
        """获取历史资产数据。"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            if user_id:
                cursor.execute(
                    """
                    SELECT * FROM daily_snapshots
                    WHERE user_id = ?
                      AND date >= COALESCE(
                        (
                          SELECT SUBSTR(build_start_at, 1, 10)
                          FROM users
                          WHERE id = ?
                            AND TRIM(COALESCE(build_start_at, '')) != ''
                          LIMIT 1
                        ),
                        ''
                      )
                    ORDER BY date ASC
                    LIMIT ?
                    """,
                    (user_id, user_id, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM daily_snapshots
                    WHERE user_id IS NULL OR user_id = ''
                    ORDER BY date ASC
                    LIMIT ?
                    """,
                    (limit,),
                )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def _sync_version_from_parts(self, domain: str, *parts: str) -> str:
        raw = f"{domain}|" + "|".join(str(p or "") for p in parts)
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]

    def get_sync_versions(self, user_id: str = None) -> Dict[str, str]:
        """计算客户端增量同步版本号。"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        uid = str(user_id or "")
        user_condition = "user_id = ?" if user_id else "(user_id IS NULL OR user_id = '')"
        user_param = (user_id,) if user_id else ()

        def _table_version(table: str) -> str:
            cursor.execute(
                f"""
                SELECT COALESCE(MAX(updated_at), '') AS max_updated, COUNT(*) AS cnt
                FROM {table}
                WHERE {user_condition}
                """,
                user_param,
            )
            row = cursor.fetchone() or {}
            max_updated = str((row["max_updated"] if isinstance(row, sqlite3.Row) else "") or "")
            cnt = str((row["cnt"] if isinstance(row, sqlite3.Row) else 0) or 0)
            return self._sync_version_from_parts(table, max_updated, cnt, uid)

        try:
            versions: Dict[str, str] = {
                "portfolio": _table_version("portfolio"),
                "cash_assets": _table_version("cash_assets"),
                "other_assets": _table_version("other_assets"),
                "liabilities": _table_version("liabilities"),
            }

            cursor.execute(
                f"""
                SELECT COALESCE(MAX(date), '') AS max_date, COUNT(*) AS cnt
                FROM daily_snapshots
                WHERE {user_condition}
                """,
                user_param,
            )
            history_row = cursor.fetchone() or {}
            max_date = str((history_row["max_date"] if isinstance(history_row, sqlite3.Row) else "") or "")
            history_cnt = str((history_row["cnt"] if isinstance(history_row, sqlite3.Row) else 0) or 0)
            versions["history"] = self._sync_version_from_parts("history", max_date, history_cnt, uid)

            cursor.execute(
                f"""
                SELECT COALESCE(MAX(updated_at), '') AS max_updated, COUNT(*) AS cnt
                FROM daily_snapshots
                WHERE {user_condition}
                """,
                user_param,
            )
            overview_row = cursor.fetchone() or {}
            overview_updated = str((overview_row["max_updated"] if isinstance(overview_row, sqlite3.Row) else "") or "")
            overview_cnt = str((overview_row["cnt"] if isinstance(overview_row, sqlite3.Row) else 0) or 0)
            versions["overview_all"] = self._sync_version_from_parts(
                "overview_all",
                overview_updated,
                overview_cnt,
                uid,
            )
            return versions
        finally:
            conn.close()
