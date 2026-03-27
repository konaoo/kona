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
ASSET_BREAKDOWN_MARKETS = ("a", "hk", "us", "fund", "unallocated")


class SnapshotDatabaseMixin:
    """给 DatabaseManager 提供快照、历史与同步版本相关方法。"""

    def _fetch_snapshot_day_pnl(
        self,
        cursor,
        *,
        date_str: str,
        user_id: str = "",
        ledger_id: int | None = None,
    ) -> float | None:
        if ledger_id is None:
            cursor.execute(
                """
                SELECT day_pnl
                FROM daily_snapshots
                WHERE date = ? AND user_id = ?
                LIMIT 1
                """,
                (str(date_str or ""), str(user_id or "")),
            )
        else:
            cursor.execute(
                """
                SELECT day_pnl
                FROM ledger_daily_snapshots
                WHERE date = ? AND user_id = ? AND ledger_id = ?
                LIMIT 1
                """,
                (str(date_str or ""), str(user_id or ""), int(ledger_id)),
            )
        row = cursor.fetchone()
        if not row:
            return None
        return round(float((row["day_pnl"] if row["day_pnl"] is not None else 0.0) or 0.0), 2)

    def _fetch_market_breakdown_rows(
        self,
        cursor,
        *,
        date_str: str,
        user_id: str = "",
        ledger_id: int | None = None,
    ) -> Dict[str, Dict[str, Any]]:
        if ledger_id is None:
            cursor.execute(
                """
                SELECT market, day_pnl, snapshot_date, source, confidence, meta_json
                FROM daily_snapshot_market_breakdowns
                WHERE date = ? AND user_id = ?
                """,
                (str(date_str or ""), str(user_id or "")),
            )
        else:
            cursor.execute(
                """
                SELECT market, day_pnl, snapshot_date, source, confidence, meta_json
                FROM ledger_daily_snapshot_market_breakdowns
                WHERE date = ? AND user_id = ? AND ledger_id = ?
                """,
                (str(date_str or ""), str(user_id or ""), int(ledger_id)),
            )
        rows: Dict[str, Dict[str, Any]] = {}
        for row in cursor.fetchall():
            market = str(row["market"] or "").strip().lower()
            if market not in MARKET_BREAKDOWN_MARKETS:
                continue
            rows[market] = {
                "day_pnl": round(float((row["day_pnl"] if row["day_pnl"] is not None else 0.0) or 0.0), 2),
                "snapshot_date": str(row["snapshot_date"] or "").strip(),
                "source": str(row["source"] or "").strip(),
                "confidence": float((row["confidence"] if row["confidence"] is not None else 1.0) or 1.0),
                "meta_json": row["meta_json"],
            }
        return rows

    def get_daily_snapshot_asset_breakdown_rows(
        self,
        *,
        date_str: str,
        user_id: str = None,
        ledger_id: int | None = None,
    ) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        uid = user_id or ""
        try:
            if ledger_id is None:
                cursor.execute(
                    """
                    SELECT code, name, market, curr, day_pnl, day_base, snapshot_date, source, confidence
                    FROM daily_snapshot_asset_breakdowns
                    WHERE date = ? AND user_id = ?
                    ORDER BY code ASC
                    """,
                    (str(date_str or ""), uid),
                )
            else:
                cursor.execute(
                    """
                    SELECT code, name, market, curr, day_pnl, day_base, snapshot_date, source, confidence
                    FROM ledger_daily_snapshot_asset_breakdowns
                    WHERE date = ? AND user_id = ? AND ledger_id = ?
                    ORDER BY code ASC
                    """,
                    (str(date_str or ""), uid, int(ledger_id)),
                )
            return [
                {
                    "code": str(row["code"] or ""),
                    "name": str(row["name"] or row["code"] or ""),
                    "market": str(row["market"] or "a").strip().lower(),
                    "curr": str(row["curr"] or "CNY").strip().upper(),
                    "day_pnl": round(float((row["day_pnl"] if row["day_pnl"] is not None else 0.0) or 0.0), 2),
                    "day_base": round(float((row["day_base"] if row["day_base"] is not None else 0.0) or 0.0), 2),
                    "snapshot_date": str(row["snapshot_date"] or "").strip(),
                    "source": str(row["source"] or "").strip(),
                    "confidence": float((row["confidence"] if row["confidence"] is not None else 1.0) or 1.0),
                }
                for row in cursor.fetchall()
            ]
        finally:
            conn.close()

    def get_daily_snapshot_asset_breakdown_rows_by_period(
        self,
        *,
        start_date: str,
        end_date: str,
        user_id: str = None,
        ledger_id: int | None = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        uid = user_id or ""
        try:
            if ledger_id is None:
                cursor.execute(
                    """
                    SELECT date, code, name, market, curr, day_pnl, day_base, snapshot_date, source, confidence
                    FROM daily_snapshot_asset_breakdowns
                    WHERE user_id = ? AND date >= ? AND date <= ?
                    ORDER BY date ASC, code ASC
                    """,
                    (uid, str(start_date or ""), str(end_date or "")),
                )
            else:
                cursor.execute(
                    """
                    SELECT date, code, name, market, curr, day_pnl, day_base, snapshot_date, source, confidence
                    FROM ledger_daily_snapshot_asset_breakdowns
                    WHERE user_id = ? AND ledger_id = ? AND date >= ? AND date <= ?
                    ORDER BY date ASC, code ASC
                    """,
                    (uid, int(ledger_id), str(start_date or ""), str(end_date or "")),
                )
            result: Dict[str, List[Dict[str, Any]]] = {}
            for row in cursor.fetchall():
                date_key = str(row["date"] or "").strip()
                result.setdefault(date_key, []).append(
                    {
                        "code": str(row["code"] or ""),
                        "name": str(row["name"] or row["code"] or ""),
                        "market": str(row["market"] or "a").strip().lower(),
                        "curr": str(row["curr"] or "CNY").strip().upper(),
                        "day_pnl": round(float((row["day_pnl"] if row["day_pnl"] is not None else 0.0) or 0.0), 2),
                        "day_base": round(float((row["day_base"] if row["day_base"] is not None else 0.0) or 0.0), 2),
                        "snapshot_date": str(row["snapshot_date"] or "").strip(),
                        "source": str(row["source"] or "").strip(),
                        "confidence": float((row["confidence"] if row["confidence"] is not None else 1.0) or 1.0),
                    }
                )
            return result
        finally:
            conn.close()

    def _upsert_market_breakdown_row(
        self,
        cursor,
        *,
        date_str: str,
        user_id: str = "",
        market: str,
        day_pnl: float,
        snapshot_date: str,
        source: str,
        confidence: float,
        meta_json: str | None = None,
        ledger_id: int | None = None,
    ) -> None:
        if ledger_id is None:
            cursor.execute(
                """
                INSERT INTO daily_snapshot_market_breakdowns
                (date, user_id, market, day_pnl, snapshot_date, source, confidence, meta_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
                ON CONFLICT(date, user_id, market) DO UPDATE SET
                    day_pnl = excluded.day_pnl,
                    snapshot_date = excluded.snapshot_date,
                    source = excluded.source,
                    confidence = excluded.confidence,
                    meta_json = excluded.meta_json,
                    updated_at = datetime('now','localtime')
                """,
                (
                    str(date_str or ""),
                    str(user_id or ""),
                    str(market or ""),
                    round(float(day_pnl or 0.0), 2),
                    str(snapshot_date or date_str or ""),
                    str(source or "exact"),
                    float(confidence),
                    meta_json,
                ),
            )
            return

        cursor.execute(
            """
            INSERT INTO ledger_daily_snapshot_market_breakdowns
            (user_id, ledger_id, date, snapshot_date, market, day_pnl, source, confidence, meta_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
            ON CONFLICT(user_id, ledger_id, date, market) DO UPDATE SET
                snapshot_date = excluded.snapshot_date,
                day_pnl = excluded.day_pnl,
                source = excluded.source,
                confidence = excluded.confidence,
                meta_json = excluded.meta_json,
                updated_at = datetime('now','localtime')
            """,
            (
                str(user_id or ""),
                int(ledger_id),
                str(date_str or ""),
                str(snapshot_date or date_str or ""),
                str(market or ""),
                round(float(day_pnl or 0.0), 2),
                str(source or "exact"),
                float(confidence),
                meta_json,
            ),
        )

    def _reconcile_market_breakdown_rows(
        self,
        cursor,
        *,
        date_str: str,
        user_id: str = "",
        ledger_id: int | None = None,
        snapshot_date: str | None = None,
        source: str = "recalculated",
        confidence: float = 1.0,
        market_updates: Optional[Dict[str, float]] = None,
        meta_by_market: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, float] | None:
        total_day_pnl = self._fetch_snapshot_day_pnl(
            cursor,
            date_str=date_str,
            user_id=user_id,
            ledger_id=ledger_id,
        )
        if total_day_pnl is None:
            return None

        existing = self._fetch_market_breakdown_rows(
            cursor,
            date_str=date_str,
            user_id=user_id,
            ledger_id=ledger_id,
        )
        values = {market: 0.0 for market in MARKET_BREAKDOWN_MARKETS}
        for market, payload in existing.items():
            values[market] = round(float(payload.get("day_pnl") or 0.0), 2)

        clean_updates: Dict[str, float] = {}
        for raw_market, raw_value in (market_updates or {}).items():
            market = str(raw_market or "").strip().lower()
            if market not in ("a", "hk", "us", "fund"):
                continue
            clean_updates[market] = round(float(raw_value or 0.0), 2)
            values[market] = clean_updates[market]

        allocated = sum(float(values[market] or 0.0) for market in ("a", "hk", "us", "fund"))
        values["unallocated"] = round(float(total_day_pnl) - allocated, 2)

        meta_map = meta_by_market or {}
        write_markets = {"unallocated"}
        write_markets.update(clean_updates.keys())
        write_markets.update(market for market in MARKET_BREAKDOWN_MARKETS if market not in existing)

        for market in write_markets:
            current = existing.get(market) or {}
            row_snapshot_date = str(current.get("snapshot_date") or snapshot_date or date_str or "")
            row_source = str(current.get("source") or source or "exact")
            row_confidence = float(current.get("confidence") if current.get("confidence") is not None else confidence)
            row_meta_json = current.get("meta_json")

            if market in clean_updates or market == "unallocated" or market not in existing:
                payload = meta_map.get(market)
                if payload is not None:
                    try:
                        row_meta_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
                    except Exception:
                        row_meta_json = json.dumps({"raw": str(payload)}, ensure_ascii=False, separators=(",", ":"))
                row_snapshot_date = str(snapshot_date or row_snapshot_date or date_str or "")
                row_source = str(source or row_source or "exact")
                row_confidence = float(confidence)

            self._upsert_market_breakdown_row(
                cursor,
                date_str=date_str,
                user_id=user_id,
                ledger_id=ledger_id,
                market=market,
                day_pnl=values[market],
                snapshot_date=row_snapshot_date,
                source=row_source,
                confidence=row_confidence,
                meta_json=row_meta_json,
            )

        return values

    def _ensure_ledger_breakdowns_complete_for_date(
        self,
        cursor,
        *,
        user_id: str,
        date_str: str,
        snapshot_date: str | None = None,
        source: str = "recalculated",
        confidence: float = 1.0,
    ) -> None:
        cursor.execute(
            """
            SELECT ledger_id
            FROM ledger_daily_snapshots
            WHERE user_id = ? AND date = ?
            """,
            (str(user_id or ""), str(date_str or "")),
        )
        for row in cursor.fetchall():
            self._reconcile_market_breakdown_rows(
                cursor,
                date_str=date_str,
                user_id=user_id,
                ledger_id=int(row["ledger_id"]),
                snapshot_date=snapshot_date,
                source=source,
                confidence=confidence,
            )

    def cleanup_orphan_ledger_daily_snapshots(self, cursor, user_id: str | None = None) -> int:
        """清理已经失去对应账本主表记录的孤儿账本快照。"""
        params: list[Any] = []
        user_filter_sql = ""
        if user_id is not None:
            user_filter_sql = "AND s.user_id = ?"
            params.append(str(user_id))

        cursor.execute(
            f"""
            DELETE FROM ledger_daily_snapshots
            WHERE id IN (
                SELECT s.id
                FROM ledger_daily_snapshots s
                LEFT JOIN investment_ledgers l ON l.id = s.ledger_id
                WHERE l.id IS NULL
                {user_filter_sql}
            )
            """,
            params,
        )
        cursor.execute("SELECT changes()")
        changed = int(cursor.fetchone()[0] or 0)
        if changed > 0:
            logger.info("Cleaned up %s orphan ledger daily snapshots", changed)
        return changed

    def backfill_default_ledger_daily_snapshots(self, cursor, user_id: str | None = None) -> int:
        """
        为“默认账本可明确承接旧历史”的用户补齐缺失的账本历史快照。

        背景：
        - 老用户在多账本上线前，只有 daily_snapshots 全局历史
        - 多账本迁移时，只给持仓/交易补了 ledger_id，没有把历史快照补到 ledger_daily_snapshots

        这里的原则是：
        - 单账本用户：全部旧历史都归默认账本
        - 多账本用户：只把“早于任何非默认账本存在/活动证据”的旧历史补给默认账本
        - 只补缺失日期，不覆盖已有账本快照
        - 一旦非默认账本在某天已经存在或有活动，就不再对该日及之后的全局历史做猜测

        注意：
        - 旧全局快照没有“按账本的历史 total_cost”，只有 total_invest
        - 为了让单账本老用户的账本分析历史和旧全局分析历史保持一致，
          这里把 total_invest 同时映射到 total_market_value / total_cost，
          total_pnl_rate 也按 total_invest 作为基数回填
        """
        cursor.execute(
            """
            SELECT user_id, id AS ledger_id
            FROM investment_ledgers
            WHERE is_default = 1
            """
            + (" AND user_id = ?" if user_id is not None else ""),
            ((str(user_id),) if user_id is not None else ()),
        )
        default_ledgers = cursor.fetchall()
        inserted_total = 0

        def _pick_earliest_date(candidates: list[str | None]) -> str | None:
            normalized = sorted(
                {
                    str(value).strip()
                    for value in candidates
                    if value is not None and str(value).strip()
                }
            )
            return normalized[0] if normalized else None

        for row in default_ledgers:
            uid = str(row["user_id"] or "")
            ledger_id = int(row["ledger_id"])
            cutoff_candidates: list[str | None] = []

            cursor.execute(
                """
                SELECT date(created_at) AS cutoff_date
                FROM investment_ledgers
                WHERE user_id = ? AND id != ?
                """,
                (uid, ledger_id),
            )
            cutoff_candidates.extend(
                str(item["cutoff_date"]).strip() if item["cutoff_date"] else None
                for item in cursor.fetchall()
            )

            for sql in (
                """
                SELECT MIN(date(time)) AS cutoff_date
                FROM transactions
                WHERE user_id = ? AND ledger_id IS NOT NULL AND ledger_id != 0 AND ledger_id != ?
                """,
                """
                SELECT MIN(date(created_at)) AS cutoff_date
                FROM portfolio
                WHERE user_id = ? AND ledger_id IS NOT NULL AND ledger_id != 0 AND ledger_id != ?
                """,
                """
                SELECT MIN(date(created_at)) AS cutoff_date
                FROM portfolio_adjustment_ledger
                WHERE user_id = ? AND ledger_id IS NOT NULL AND ledger_id != 0 AND ledger_id != ?
                """,
                """
                SELECT MIN(date(created_at)) AS cutoff_date
                FROM portfolio_correction_logs
                WHERE user_id = ? AND ledger_id IS NOT NULL AND ledger_id != 0 AND ledger_id != ?
                """,
            ):
                cursor.execute(sql, (uid, ledger_id))
                activity_row = cursor.fetchone()
                cutoff_candidates.append(
                    str(activity_row["cutoff_date"]).strip()
                    if activity_row and activity_row["cutoff_date"]
                    else None
                )

            cutoff_date = _pick_earliest_date(cutoff_candidates)
            cursor.execute(
                """
                INSERT INTO ledger_daily_snapshots (
                    user_id, ledger_id, date,
                    total_market_value, total_cost, total_pnl, total_pnl_rate,
                    day_pnl, holdings_count, created_at
                )
                SELECT
                    ds.user_id,
                    ?,
                    ds.date,
                    ROUND(COALESCE(ds.total_invest, 0), 2),
                    ROUND(COALESCE(ds.total_invest, 0), 2),
                    ROUND(COALESCE(ds.total_pnl, 0), 2),
                    CASE
                        WHEN ABS(COALESCE(ds.total_invest, 0)) > 0
                            THEN ROUND(COALESCE(ds.total_pnl, 0) / ds.total_invest * 100, 2)
                        ELSE 0
                    END,
                    ROUND(COALESCE(ds.day_pnl, 0), 2),
                    0,
                    COALESCE(ds.updated_at, datetime('now','localtime'))
                FROM daily_snapshots ds
                WHERE ds.user_id = ?
                  AND (? IS NULL OR ds.date < ?)
                  AND NOT EXISTS (
                      SELECT 1
                      FROM ledger_daily_snapshots lds
                      WHERE lds.user_id = ds.user_id
                        AND lds.ledger_id = ?
                        AND lds.date = ds.date
                  )
                ORDER BY ds.date ASC
                """,
                (ledger_id, uid, cutoff_date, cutoff_date, ledger_id),
            )
            cursor.execute("SELECT changes()")
            changed = int(cursor.fetchone()[0] or 0)
            if changed > 0:
                inserted_total += changed
                logger.info(
                    "Backfilled %s ledger snapshots for default ledger user=%s ledger_id=%s cutoff=%s",
                    changed,
                    uid,
                    ledger_id,
                    cutoff_date,
                )

        return inserted_total

    def backfill_single_ledger_daily_snapshots(self, cursor, user_id: str | None = None) -> int:
        """
        兼容旧调用名。

        现在的正式实现已经升级成：
        - 单账本用户补全部旧历史
        - 多账本用户补“明确属于默认账本”的旧历史
        """
        return self.backfill_default_ledger_daily_snapshots(cursor, user_id=user_id)

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
        snapshot_date: str | None = None,
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
                    (date, user_id, market, day_pnl, snapshot_date, source, confidence, meta_json, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
                    ON CONFLICT(date, user_id, market) DO UPDATE SET
                        day_pnl = excluded.day_pnl,
                        snapshot_date = excluded.snapshot_date,
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
                        str(snapshot_date or date_str or ""),
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

    def save_daily_snapshot_asset_breakdowns(
        self,
        *,
        date_str: str,
        items: List[Dict[str, Any]],
        user_id: str = None,
        snapshot_date: str | None = None,
        source: str = "exact",
        confidence: float = 1.0,
        replace_existing: bool = True,
        ledger_id: int | None = None,
    ) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        uid = user_id or ""
        table = "ledger_daily_snapshot_asset_breakdowns" if ledger_id is not None else "daily_snapshot_asset_breakdowns"
        try:
            if replace_existing:
                if ledger_id is None:
                    cursor.execute(
                        f"DELETE FROM {table} WHERE date = ? AND user_id = ?",
                        (str(date_str or ""), uid),
                    )
                else:
                    cursor.execute(
                        f"DELETE FROM {table} WHERE date = ? AND user_id = ? AND ledger_id = ?",
                        (str(date_str or ""), uid, int(ledger_id)),
                    )

            for item in items or []:
                code = str(item.get("code") or "").strip()
                if not code:
                    continue
                name = str(item.get("name") or code)
                market = str(item.get("market") or "a").strip().lower()
                if market not in ASSET_BREAKDOWN_MARKETS:
                    market = "a"
                curr = str(item.get("curr") or "CNY").strip().upper()
                day_pnl = round(float(item.get("day_pnl") or item.get("pnl") or 0.0), 2)
                day_base = round(float(item.get("day_base") or item.get("base") or 0.0), 2)
                if ledger_id is None:
                    cursor.execute(
                        f"""
                        INSERT INTO {table}
                        (date, user_id, code, name, market, curr, day_pnl, day_base, snapshot_date, source, confidence, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
                        ON CONFLICT(date, user_id, code) DO UPDATE SET
                            name = excluded.name,
                            market = excluded.market,
                            curr = excluded.curr,
                            day_pnl = excluded.day_pnl,
                            day_base = excluded.day_base,
                            snapshot_date = excluded.snapshot_date,
                            source = excluded.source,
                            confidence = excluded.confidence,
                            updated_at = datetime('now','localtime')
                        """,
                        (
                            str(date_str or ""),
                            uid,
                            code,
                            name,
                            market,
                            curr,
                            day_pnl,
                            day_base,
                            str(snapshot_date or date_str or ""),
                            str(source or "exact"),
                            float(confidence),
                        ),
                    )
                else:
                    cursor.execute(
                        f"""
                        INSERT INTO {table}
                        (user_id, ledger_id, date, code, name, market, curr, day_pnl, day_base, snapshot_date, source, confidence, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
                        ON CONFLICT(user_id, ledger_id, date, code) DO UPDATE SET
                            name = excluded.name,
                            market = excluded.market,
                            curr = excluded.curr,
                            day_pnl = excluded.day_pnl,
                            day_base = excluded.day_base,
                            snapshot_date = excluded.snapshot_date,
                            source = excluded.source,
                            confidence = excluded.confidence,
                            updated_at = datetime('now','localtime')
                        """,
                        (
                            uid,
                            int(ledger_id),
                            str(date_str or ""),
                            code,
                            name,
                            market,
                            curr,
                            day_pnl,
                            day_base,
                            str(snapshot_date or date_str or ""),
                            str(source or "exact"),
                            float(confidence),
                        ),
                    )
            conn.commit()
            return True
        except Exception as exc:
            logger.error(
                "Failed to save asset breakdown date=%s user_id=%s ledger_id=%s: %s",
                date_str,
                uid,
                ledger_id,
                exc,
            )
            conn.rollback()
            return False
        finally:
            conn.close()

    def save_daily_snapshot_market_breakdown_partial(
        self,
        date_str: str,
        market_updates: Dict[str, float],
        user_id: str = None,
        snapshot_date: str | None = None,
        source: str = "exact",
        confidence: float = 1.0,
        meta_by_market: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """只更新指定市场，不覆盖同一天的其他市场拆分。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        uid = user_id or ""

        try:
            values = self._reconcile_market_breakdown_rows(
                cursor,
                date_str=str(date_str or ""),
                user_id=uid,
                snapshot_date=str(snapshot_date or date_str or ""),
                source=str(source or "exact"),
                confidence=float(confidence),
                market_updates=market_updates,
                meta_by_market=meta_by_market,
            )
            if values is None:
                return True
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

    def save_daily_snapshot_market_breakdown_row(
        self,
        *,
        date_str: str,
        market: str,
        day_pnl: float,
        user_id: str = None,
        snapshot_date: str | None = None,
        source: str = "exact",
        confidence: float = 1.0,
        meta_json: str | None = None,
        ledger_id: int | None = None,
    ) -> bool:
        """只覆盖单个市场行，不自动改写其他市场或 unallocated。"""
        normalized_market = str(market or "").strip().lower()
        if normalized_market not in MARKET_BREAKDOWN_MARKETS:
            logger.error("Invalid market breakdown row market=%s date=%s", market, date_str)
            return False

        conn = self.get_connection()
        cursor = conn.cursor()
        uid = user_id or ""

        try:
            self._upsert_market_breakdown_row(
                cursor,
                date_str=str(date_str or ""),
                user_id=uid,
                ledger_id=ledger_id,
                market=normalized_market,
                day_pnl=round(float(day_pnl or 0.0), 2),
                snapshot_date=str(snapshot_date or date_str or ""),
                source=str(source or "exact"),
                confidence=float(confidence),
                meta_json=meta_json,
            )
            conn.commit()
            return True
        except Exception as exc:
            logger.error(
                "Failed to save single market breakdown row date=%s user_id=%s ledger_id=%s market=%s: %s",
                date_str,
                uid,
                ledger_id,
                normalized_market,
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

    def sync_ledger_daily_snapshot_day_pnl_from_breakdown(
        self,
        *,
        date_str: str,
        user_id: str,
        ledger_id: int,
    ) -> bool:
        """按账本分市场拆分回写指定日期的账本 day_pnl。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        uid = user_id or ""

        try:
            cursor.execute(
                """
                SELECT COALESCE(SUM(day_pnl), 0.0) AS total
                FROM ledger_daily_snapshot_market_breakdowns
                WHERE date = ? AND user_id = ? AND ledger_id = ?
                """,
                (str(date_str or ""), uid, int(ledger_id)),
            )
            row = cursor.fetchone()
            total = round(float((row["total"] if row else 0.0) or 0.0), 2)
            cursor.execute(
                """
                UPDATE ledger_daily_snapshots
                SET day_pnl = ?, created_at = datetime('now','localtime')
                WHERE date = ? AND user_id = ? AND ledger_id = ?
                """,
                (total, str(date_str or ""), uid, int(ledger_id)),
            )
            updated = int(cursor.rowcount or 0)
            conn.commit()
            return updated > 0
        except Exception as exc:
            logger.error(
                "Failed to sync ledger day_pnl from breakdown date=%s user_id=%s ledger_id=%s: %s",
                date_str,
                uid,
                ledger_id,
                exc,
            )
            conn.rollback()
            return False
        finally:
            conn.close()

    def save_ledger_daily_snapshot_market_breakdown(
        self,
        *,
        user_id: str,
        ledger_id: int,
        date_str: str,
        day_pnl_by_market: Dict[str, float],
        total_day_pnl: float,
        snapshot_date: str | None = None,
        source: str = "exact",
        confidence: float = 1.0,
        meta_by_market: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """保存账本级分市场收益快照。"""
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
                    INSERT INTO ledger_daily_snapshot_market_breakdowns
                    (user_id, ledger_id, date, snapshot_date, market, day_pnl, source, confidence, meta_json, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
                    ON CONFLICT(user_id, ledger_id, date, market) DO UPDATE SET
                        snapshot_date = excluded.snapshot_date,
                        day_pnl = excluded.day_pnl,
                        source = excluded.source,
                        confidence = excluded.confidence,
                        meta_json = excluded.meta_json,
                        updated_at = datetime('now','localtime')
                    """,
                    (
                        uid,
                        int(ledger_id),
                        str(date_str or ""),
                        str(snapshot_date or date_str or ""),
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
            logger.error(
                "Failed to save ledger market breakdown ledger=%s date=%s user_id=%s: %s",
                ledger_id,
                date_str,
                uid,
                exc,
            )
            conn.rollback()
            return False
        finally:
            conn.close()

    def save_ledger_daily_snapshot_market_breakdown_partial(
        self,
        *,
        user_id: str,
        ledger_id: int,
        date_str: str,
        market_updates: Dict[str, float],
        snapshot_date: str | None = None,
        source: str = "exact",
        confidence: float = 1.0,
        meta_by_market: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """局部更新账本级分市场收益快照。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        uid = user_id or ""

        try:
            values = self._reconcile_market_breakdown_rows(
                cursor,
                date_str=str(date_str or ""),
                user_id=uid,
                ledger_id=int(ledger_id),
                snapshot_date=str(snapshot_date or date_str or ""),
                source=str(source or "exact"),
                confidence=float(confidence),
                market_updates=market_updates,
                meta_by_market=meta_by_market,
            )
            if values is None:
                return True
            conn.commit()
            return True
        except Exception as exc:
            logger.error(
                "Failed to partially save ledger market breakdown ledger=%s date=%s user_id=%s: %s",
                ledger_id,
                date_str,
                uid,
                exc,
            )
            conn.rollback()
            return False
        finally:
            conn.close()

    def aggregate_daily_snapshot_from_ledgers(
        self,
        *,
        user_id: str,
        date_str: str,
        total_asset: float,
        total_invest: float,
        total_cash: float,
        total_other: float,
        total_liability: float,
        total_pnl: float,
        source: str = "recalculated",
        snapshot_date: str | None = None,
    ) -> bool:
        """根据账本聚合结果回写全局主快照。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        uid = user_id or ""

        try:
            cursor.execute(
                """
                SELECT COALESCE(SUM(day_pnl), 0.0) AS total_day_pnl
                FROM ledger_daily_snapshots
                WHERE user_id = ? AND date = ?
                """,
                (uid, str(date_str or "")),
            )
            row = cursor.fetchone()
            day_pnl = round(float((row["total_day_pnl"] if row else 0.0) or 0.0), 2)
            cursor.execute(
                """
                INSERT INTO daily_snapshots (
                    date, total_asset, total_invest, total_cash,
                    total_other, total_liability, total_pnl, day_pnl,
                    snapshot_date, source, user_id, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
                ON CONFLICT(date, user_id) DO UPDATE SET
                    total_asset = excluded.total_asset,
                    total_invest = excluded.total_invest,
                    total_cash = excluded.total_cash,
                    total_other = excluded.total_other,
                    total_liability = excluded.total_liability,
                    total_pnl = excluded.total_pnl,
                    day_pnl = excluded.day_pnl,
                    snapshot_date = excluded.snapshot_date,
                    source = excluded.source,
                    updated_at = datetime('now','localtime')
                """,
                (
                    str(date_str or ""),
                    round(float(total_asset or 0.0), 2),
                    round(float(total_invest or 0.0), 2),
                    round(float(total_cash or 0.0), 2),
                    round(float(total_other or 0.0), 2),
                    round(float(total_liability or 0.0), 2),
                    round(float(total_pnl or 0.0), 2),
                    day_pnl,
                    str(snapshot_date or date_str or ""),
                    str(source or "recalculated"),
                    uid,
                ),
            )
            conn.commit()
            return True
        except Exception as exc:
            logger.error("Failed to aggregate global snapshot from ledgers date=%s user_id=%s: %s", date_str, uid, exc)
            conn.rollback()
            return False
        finally:
            conn.close()

    def aggregate_daily_snapshot_market_breakdown_from_ledgers(
        self,
        *,
        user_id: str,
        date_str: str,
        snapshot_date: str | None = None,
        source: str = "recalculated",
    ) -> bool:
        """按账本分市场快照聚合全局分市场快照。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        uid = user_id or ""

        try:
            self._ensure_ledger_breakdowns_complete_for_date(
                cursor,
                user_id=uid,
                date_str=str(date_str or ""),
                snapshot_date=snapshot_date,
                source=source,
                confidence=1.0,
            )
            cursor.execute(
                """
                SELECT market, COALESCE(SUM(day_pnl), 0.0) AS total_day_pnl
                FROM ledger_daily_snapshot_market_breakdowns
                WHERE user_id = ? AND date = ?
                GROUP BY market
                """,
                (uid, str(date_str or "")),
            )
            totals = {market: 0.0 for market in MARKET_BREAKDOWN_MARKETS}
            for row in cursor.fetchall():
                market = str(row["market"] or "").strip().lower()
                if market in totals:
                    totals[market] = round(float(row["total_day_pnl"] or 0.0), 2)
            total_day_pnl = sum(float(value or 0.0) for value in totals.values())
            conn.close()
            return self.save_daily_snapshot_market_breakdown(
                date_str=str(date_str or ""),
                day_pnl_by_market=totals,
                total_day_pnl=total_day_pnl,
                user_id=uid,
                snapshot_date=snapshot_date or date_str,
                source=source,
                confidence=1.0,
            )
        except Exception as exc:
            logger.error(
                "Failed to aggregate global market breakdown from ledgers date=%s user_id=%s: %s",
                date_str,
                uid,
                exc,
            )
            conn.close()
            return False

    def sync_ledger_daily_snapshot_day_pnl(self, date_str: str, user_id: str = None) -> bool:
        """
        同步全局的 day_pnl 调整到 ledger_daily_snapshots。
        如果只有一个活跃账本，直接 100% 覆盖。如果有多个账本，按当时的 total_market_value 比例分配全局的 day_pnl。
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        uid = user_id or ""
        try:
            cursor.execute(
                "SELECT day_pnl FROM daily_snapshots WHERE date = ? AND user_id = ?",
                (str(date_str or ""), uid)
            )
            row = cursor.fetchone()
            if not row:
                return False
            global_day_pnl = float((row["day_pnl"] if row else 0.0) or 0.0)

            cursor.execute(
                "SELECT ledger_id, total_market_value FROM ledger_daily_snapshots WHERE date = ? AND user_id = ?",
                (str(date_str or ""), uid)
            )
            ledgers = cursor.fetchall()
            if not ledgers:
                return False

            if len(ledgers) == 1:
                cursor.execute(
                    """
                    UPDATE ledger_daily_snapshots 
                    SET day_pnl = ?, created_at = datetime('now','localtime') 
                    WHERE date = ? AND user_id = ? AND ledger_id = ?
                    """,
                    (round(global_day_pnl, 2), str(date_str or ""), uid, ledgers[0]["ledger_id"])
                )
            else:
                total_mv = sum(float((l["total_market_value"] if l else 0.0) or 0.0) for l in ledgers)
                for l in ledgers:
                    lid = l["ledger_id"]
                    mv = float((l["total_market_value"] if l else 0.0) or 0.0)
                    ratio = mv / total_mv if total_mv > 0 else 0
                    allocated_pnl = round(global_day_pnl * ratio, 2)
                    cursor.execute(
                        """
                        UPDATE ledger_daily_snapshots 
                        SET day_pnl = ?, created_at = datetime('now','localtime') 
                        WHERE date = ? AND user_id = ? AND ledger_id = ?
                        """,
                        (allocated_pnl, str(date_str or ""), uid, lid)
                    )
            conn.commit()
            return True
        except Exception as exc:
            logger.error(
                "Failed to sync ledger day_pnl date=%s user_id=%s: %s",
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
        snapshot_date: str | None = None,
        source: str = "recalculated",
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
                    day_pnl, snapshot_date, source, holdings_count, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
                ON CONFLICT(user_id, ledger_id, date) DO UPDATE SET
                    total_market_value = excluded.total_market_value,
                    total_cost = excluded.total_cost,
                    total_pnl = excluded.total_pnl,
                    total_pnl_rate = excluded.total_pnl_rate,
                    day_pnl = excluded.day_pnl,
                    snapshot_date = excluded.snapshot_date,
                    source = excluded.source,
                    holdings_count = excluded.holdings_count,
                    created_at = datetime('now','localtime')
                """,
                (
                    user_id, ledger_id, date_str,
                    round(total_market_value, 2), round(total_cost, 2),
                    round(total_pnl, 2), round(total_pnl_rate, 2),
                    round(day_pnl, 2), str(snapshot_date or date_str or ""), str(source or "recalculated"), holdings_count,
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

    def save_daily_snapshot(
        self,
        data: Dict[str, float],
        user_id: str = None,
        snapshot_date: str = None,
        source: str = "recalculated",
    ) -> bool:
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
                    total_other, total_liability, total_pnl, day_pnl,
                    snapshot_date, source, user_id, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
                ON CONFLICT(date, user_id) DO UPDATE SET
                    total_asset = excluded.total_asset,
                    total_invest = excluded.total_invest,
                    total_cash = excluded.total_cash,
                    total_other = excluded.total_other,
                    total_liability = excluded.total_liability,
                    total_pnl = excluded.total_pnl,
                    day_pnl = excluded.day_pnl,
                    snapshot_date = excluded.snapshot_date,
                    source = excluded.source,
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
                    data.get("snapshot_date") or today,
                    str(data.get("source") or source or "recalculated"),
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
