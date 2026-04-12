"""
持仓交易、投资写操作与组合兼容迁移数据库能力。

这一层只做：
- portfolio 表兼容迁移
- 持仓 CRUD
- 买入 / 卖出 / 撤销
- 持仓交易历史与已实现盈亏
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from .day_pnl_attribution import effective_date_from_transaction_time
    from .market_calendar import market_from_asset
    from .parser import parse_code
    from .logo_utils import suggest_logo_url
except ImportError:  # 兼容被单文件动态加载的测试场景
    from core.day_pnl_attribution import effective_date_from_transaction_time
    from core.market_calendar import market_from_asset
    from core.parser import parse_code
    from core.logo_utils import suggest_logo_url

logger = logging.getLogger(__name__)
DEFAULT_MARKETS = ("a", "hk", "us", "fund")
PORTFOLIO_ADJUSTMENT_EVENT_TYPES = (
    "dividend",
    "fee",
    "tax",
)


class PortfolioDatabaseMixin:
    """给 DatabaseManager 提供持仓、交易与组合兼容迁移相关方法。"""

    def _build_transaction_identity(
        self,
        *,
        code: str,
        curr: str = "",
        asset_type: str = "",
        tx_time: str = "",
    ) -> Dict[str, str]:
        raw_code = str(code or "").strip()
        normalized = parse_code(raw_code, str(curr or "").strip())
        normalized_code = str(normalized.get("code") or raw_code or "").strip()
        normalized_curr = str(normalized.get("curr") or curr or "").strip().upper()
        raw_asset_type = str(asset_type or "").strip().lower()
        if raw_asset_type in DEFAULT_MARKETS:
            market = raw_asset_type
        else:
            market = str(
                market_from_asset({
                    "code": normalized_code,
                    "asset_type": raw_asset_type,
                })
                or "a"
            ).lower()
        if market not in DEFAULT_MARKETS:
            market = "a"
        effective_date = effective_date_from_transaction_time(tx_time, market) if tx_time else None
        return {
            "code": raw_code,
            "curr": normalized_curr,
            "market": market,
            "effective_date": str(effective_date or "").strip(),
        }

    def _resolve_transaction_row_identity(self, row: Any, fallback_code: str = "") -> Dict[str, str]:
        code = str(row["code"] or "").strip() if "code" in row.keys() else str(fallback_code or "").strip()
        curr = str(row["curr"] or "").strip().upper() if "curr" in row.keys() else ""
        raw_market = str(row["market"] or "").strip().lower() if "market" in row.keys() else ""
        raw_effective_date = str(row["effective_date"] or "").strip() if "effective_date" in row.keys() else ""
        tx_time = str(row["time"] or "").strip() if "time" in row.keys() else ""
        identity = self._build_transaction_identity(
            code=code,
            curr=curr,
            asset_type=raw_market,
            tx_time=tx_time,
        )
        if raw_market in DEFAULT_MARKETS:
            identity["market"] = raw_market
        if raw_effective_date:
            identity["effective_date"] = raw_effective_date[:10]
        return identity

    def _fetch_portfolio_row_by_code(self, cursor, code: str, user_id: str = None, ledger_id: int | None = None):
        ledger_condition = " AND ledger_id = ?" if ledger_id is not None else ""
        ledger_param = (ledger_id,) if ledger_id is not None else ()
        if user_id:
            cursor.execute(
                f"""
                SELECT name, qty, price, curr, adjustment, asset_type
                FROM portfolio
                WHERE code = ? AND user_id = ?{ledger_condition}
                """,
                (code, user_id) + ledger_param,
            )
        else:
            cursor.execute(
                f"""
                SELECT name, qty, price, curr, adjustment, asset_type
                FROM portfolio
                WHERE code = ? AND (user_id IS NULL OR user_id = ''){ledger_condition}
                """,
                (code,) + ledger_param,
            )
        return cursor.fetchone()

    def _resolve_existing_portfolio_code(
        self,
        cursor,
        code: str,
        user_id: str = None,
        legacy_codes: Optional[List[str]] = None,
        ledger_id: int | None = None,
    ) -> tuple[str, Any]:
        candidates: List[str] = []
        seen: set[str] = set()
        for raw in [code, *(legacy_codes or [])]:
            candidate = str(raw or "").strip()
            if not candidate or candidate in seen:
                continue
            seen.add(candidate)
            candidates.append(candidate)

        for candidate in candidates:
            row = self._fetch_portfolio_row_by_code(cursor, candidate, user_id, ledger_id=ledger_id)
            if row:
                return candidate, row
        return str(code or "").strip(), None

    def _ensure_portfolio_user_scoped_unique(self, cursor) -> None:
        """兼容旧库唯一约束，但多账本库不再按 (code, user_id) 去重。"""
        cursor.execute("PRAGMA table_info(portfolio)")
        portfolio_cols = [row[1] for row in cursor.fetchall()]
        has_ledger_id = "ledger_id" in portfolio_cols

        cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='portfolio'"
        )
        row = cursor.fetchone()
        raw_sql = row["sql"] if isinstance(row, dict) or hasattr(row, "keys") else (row[0] if row else "")
        table_sql = str(raw_sql or "").lower()
        has_legacy_unique = "code text unique" in table_sql or "code\ttext unique" in table_sql

        if has_legacy_unique and not has_ledger_id:
            logger.info("Migrating portfolio schema from global code unique to (code, user_id) unique")
            cursor.execute("DROP TABLE IF EXISTS portfolio_new")
            cursor.execute(
                """
                CREATE TABLE portfolio_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL,
                    name TEXT NOT NULL,
                    qty REAL NOT NULL,
                    price REAL NOT NULL,
                    curr TEXT NOT NULL DEFAULT 'CNY',
                    adjustment REAL DEFAULT 0.0,
                    asset_type TEXT DEFAULT 'a',
                    user_id TEXT NOT NULL DEFAULT '',
                    created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
                    updated_at TIMESTAMP DEFAULT (datetime('now','localtime'))
                )
                """
            )
            cursor.execute(
                """
                INSERT INTO portfolio_new (
                    id, code, name, qty, price, curr, adjustment, asset_type, user_id, created_at, updated_at
                )
                SELECT
                    id,
                    code,
                    name,
                    qty,
                    price,
                    COALESCE(curr, 'CNY'),
                    COALESCE(adjustment, 0.0),
                    COALESCE(NULLIF(asset_type, ''), 'a'),
                    COALESCE(user_id, ''),
                    COALESCE(created_at, datetime('now','localtime')),
                    COALESCE(updated_at, datetime('now','localtime'))
                FROM portfolio
                """
            )
            cursor.execute("DROP TABLE portfolio")
            cursor.execute("ALTER TABLE portfolio_new RENAME TO portfolio")

        cursor.execute("UPDATE portfolio SET user_id = '' WHERE user_id IS NULL")

        cursor.execute("PRAGMA index_list(portfolio)")
        for index_row in cursor.fetchall():
            index_name = index_row[1]
            is_unique = int(index_row[2] or 0) == 1
            if not is_unique:
                continue
            safe_name = str(index_name).replace('"', '""')
            cursor.execute(f'PRAGMA index_info("{safe_name}")')
            cols = [str(col_row[2]) for col_row in cursor.fetchall()]
            if cols == ["code"] or cols == ["code", "user_id"]:
                cursor.execute(f'DROP INDEX IF EXISTS "{safe_name}"')

        if has_ledger_id:
            return

        removed = self._deduplicate_portfolio_by_code_user(cursor)
        if removed > 0:
            logger.warning(
                "Removed %s duplicate portfolio rows before creating (code, user_id) unique index",
                removed,
            )

    def _deduplicate_portfolio_by_code_user(self, cursor) -> int:
        """按 (code, user_id) 去重，保留最近更新的一条记录。"""
        removed = 0
        cursor.execute(
            """
            SELECT code, COALESCE(user_id, '') AS uid, COUNT(1) AS c
            FROM portfolio
            GROUP BY code, COALESCE(user_id, '')
            HAVING COUNT(1) > 1
            """
        )
        duplicates = cursor.fetchall()
        for row in duplicates:
            code = row[0]
            user_id = row[1]
            cursor.execute(
                """
                SELECT id
                FROM portfolio
                WHERE code = ? AND COALESCE(user_id, '') = ?
                ORDER BY datetime(COALESCE(updated_at, created_at, '1970-01-01 00:00:00')) DESC, id DESC
                """,
                (code, user_id),
            )
            ids = [int(r[0]) for r in cursor.fetchall()]
            for drop_id in ids[1:]:
                cursor.execute("DELETE FROM portfolio WHERE id = ?", (drop_id,))
                removed += 1
        return removed

    def _ensure_portfolio_asset_type(self, cursor) -> None:
        """确保 portfolio 表有 asset_type 字段，并回填默认值。"""
        try:
            cursor.execute("PRAGMA table_info(portfolio)")
            cols = [row[1] for row in cursor.fetchall()]
            if "asset_type" not in cols:
                cursor.execute("ALTER TABLE portfolio ADD COLUMN asset_type TEXT DEFAULT 'a'")
                logger.info("Added asset_type column to portfolio")
            cursor.execute("SELECT code, name FROM portfolio WHERE asset_type IS NULL OR asset_type = ''")
            rows = cursor.fetchall()
            if rows:
                from .asset_type import infer_asset_type

                for row in rows:
                    code = row[0]
                    name = row[1]
                    asset_type = infer_asset_type(code, name)
                    cursor.execute(
                        "UPDATE portfolio SET asset_type = ? WHERE code = ?",
                        (asset_type, code),
                    )
                logger.info("Backfilled asset_type for %s records", len(rows))
        except Exception as exc:
            logger.warning("Failed to ensure asset_type column: %s", exc)

    def _ensure_b_share_currency(self, cursor) -> None:
        """修正历史 B 股币种：沪 B=USD，深 B=HKD。"""
        try:
            cursor.execute(
                """
                UPDATE portfolio
                SET curr = 'USD'
                WHERE lower(code) LIKE 'sh900%' AND upper(coalesce(curr, '')) != 'USD'
                """
            )
            sh_updated = int(cursor.rowcount or 0)
            cursor.execute(
                """
                UPDATE portfolio
                SET curr = 'HKD'
                WHERE lower(code) LIKE 'sz200%' AND upper(coalesce(curr, '')) != 'HKD'
                """
            )
            sz_updated = int(cursor.rowcount or 0)
            total = sh_updated + sz_updated
            if total > 0:
                logger.info("Backfilled B-share currency for %s records", total)
        except Exception as exc:
            logger.warning("Failed to backfill B-share currency: %s", exc)

    def _fetch_portfolio_adjustment_ledger_sums(
        self,
        cursor,
        codes: List[str],
        user_id: str = None,
        ledger_id: int | None = None,
    ) -> Dict[str, float]:
        """按 code 批量汇总分红/手续费/税金流水金额。"""
        clean_codes = [str(code or "").strip() for code in codes if str(code or "").strip()]
        if not clean_codes:
            return {}

        placeholders = ",".join("?" for _ in clean_codes)
        event_types = ("dividend", "fee", "tax")
        type_placeholders = ",".join("?" for _ in event_types)
        ledger_condition = " AND ledger_id = ?" if ledger_id is not None else ""
        ledger_param = (ledger_id,) if ledger_id is not None else ()
        if user_id:
            cursor.execute(
                f"""
                SELECT code, COALESCE(SUM(amount), 0.0) AS total_amount
                FROM portfolio_adjustment_ledger
                WHERE user_id = ? AND event_type IN ({type_placeholders}) AND code IN ({placeholders}){ledger_condition}
                GROUP BY code
                """,
                (user_id, *event_types, *clean_codes) + ledger_param,
            )
        else:
            cursor.execute(
                f"""
                SELECT code, COALESCE(SUM(amount), 0.0) AS total_amount
                FROM portfolio_adjustment_ledger
                WHERE (user_id IS NULL OR user_id = '') AND event_type IN ({type_placeholders}) AND code IN ({placeholders}){ledger_condition}
                GROUP BY code
                """,
                (*event_types, *clean_codes) + ledger_param,
            )
        return {
            str(row["code"]): float(row["total_amount"] or 0.0)
            for row in cursor.fetchall()
        }

    def _fetch_portfolio_realized_pnl_sums(
        self,
        cursor,
        codes: List[str],
        user_id: str = None,
        ledger_id: int | None = None,
    ) -> Dict[str, float]:
        """按 code 批量汇总减仓已实现盈亏。"""
        clean_codes = [str(code or "").strip() for code in codes if str(code or "").strip()]
        if not clean_codes:
            return {}

        placeholders = ",".join("?" for _ in clean_codes)
        ledger_condition = " AND ledger_id = ?" if ledger_id is not None else ""
        ledger_param = (ledger_id,) if ledger_id is not None else ()
        if user_id:
            cursor.execute(
                f"""
                SELECT code, COALESCE(SUM(pnl), 0.0) AS total_pnl
                FROM transactions
                WHERE user_id = ? AND type = '减仓' AND code IN ({placeholders}){ledger_condition}
                GROUP BY code
                """,
                (user_id, *clean_codes) + ledger_param,
            )
        else:
            cursor.execute(
                f"""
                SELECT code, COALESCE(SUM(pnl), 0.0) AS total_pnl
                FROM transactions
                WHERE (user_id IS NULL OR user_id = '') AND type = '减仓' AND code IN ({placeholders}){ledger_condition}
                GROUP BY code
                """,
                tuple(clean_codes) + ledger_param,
            )
        return {
            str(row["code"]): float(row["total_pnl"] or 0.0)
            for row in cursor.fetchall()
        }

    def _is_portfolio_legacy_adjustment_ignored(
        self,
        cursor,
        user_id: str = None,
    ) -> bool:
        """判断指定用户是否已切到“不再读取 legacy adjustment”的新口径。"""
        uid = user_id or ""
        cursor.execute(
            """
            SELECT ignore_legacy_adjustment
            FROM portfolio_legacy_adjustment_states
            WHERE user_id = ?
            LIMIT 1
            """,
            (uid,),
        )
        row = cursor.fetchone()
        if not row:
            return False
        try:
            return bool(int(row["ignore_legacy_adjustment"] or 0))
        except Exception:
            return False

    def set_portfolio_legacy_adjustment_ignored(
        self,
        ignored: bool,
        user_id: str = None,
        note: str = "",
    ) -> bool:
        """设置指定用户是否忽略 legacy adjustment。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        uid = user_id or ""
        try:
            cursor.execute(
                """
                INSERT INTO portfolio_legacy_adjustment_states
                (user_id, ignore_legacy_adjustment, note, updated_at)
                VALUES (?, ?, ?, datetime('now','localtime'))
                ON CONFLICT(user_id) DO UPDATE SET
                    ignore_legacy_adjustment = excluded.ignore_legacy_adjustment,
                    note = excluded.note,
                    updated_at = datetime('now','localtime')
                """,
                (
                    uid,
                    1 if ignored else 0,
                    str(note or ""),
                ),
            )
            conn.commit()
            return True
        except Exception as exc:
            logger.error(
                "Failed to set legacy adjustment mode: user_id=%s ignored=%s err=%s",
                uid,
                ignored,
                exc,
            )
            conn.rollback()
            return False
        finally:
            conn.close()

    def _build_portfolio_legacy_adjustment_migration_report(
        self,
        cursor,
        user_id: str = None,
    ) -> Dict[str, Any]:
        """生成单个用户的 legacy adjustment 迁移盘点结果。"""
        uid = user_id or ""
        user_condition = "user_id = ?" if user_id else "(user_id IS NULL OR user_id = '')"
        user_param = (user_id,) if user_id else ()

        cursor.execute(
            f"""
            SELECT code, name, qty, price, curr, adjustment, asset_type
            FROM portfolio
            WHERE {user_condition}
            ORDER BY ABS(COALESCE(adjustment, 0.0)) DESC, code ASC
            """,
            user_param,
        )
        portfolio_rows = cursor.fetchall()
        codes = [str(row["code"] or "").strip() for row in portfolio_rows if str(row["code"] or "").strip()]

        ledger_sums = self._fetch_portfolio_adjustment_ledger_sums(cursor, codes, user_id) if codes else {}
        realized_sums = self._fetch_portfolio_realized_pnl_sums(cursor, codes, user_id) if codes else {}

        tx_meta: Dict[str, Dict[str, Any]] = {}
        correction_meta: Dict[str, Dict[str, Any]] = {}

        if codes:
            placeholders = ",".join("?" for _ in codes)
            if user_id:
                cursor.execute(
                    f"""
                    SELECT
                        code,
                        COUNT(1) AS tx_count,
                        MIN(time) AS first_tx_time,
                        MAX(time) AS last_tx_time
                    FROM transactions
                    WHERE user_id = ? AND code IN ({placeholders})
                    GROUP BY code
                    """,
                    (user_id, *codes),
                )
            else:
                cursor.execute(
                    f"""
                    SELECT
                        code,
                        COUNT(1) AS tx_count,
                        MIN(time) AS first_tx_time,
                        MAX(time) AS last_tx_time
                    FROM transactions
                    WHERE (user_id IS NULL OR user_id = '') AND code IN ({placeholders})
                    GROUP BY code
                    """,
                    codes,
                )
            tx_meta = {
                str(row["code"]): {
                    "tx_count": int(row["tx_count"] or 0),
                    "first_tx_time": str(row["first_tx_time"] or ""),
                    "last_tx_time": str(row["last_tx_time"] or ""),
                }
                for row in cursor.fetchall()
            }

            if user_id:
                cursor.execute(
                    f"""
                    SELECT
                        code,
                        COUNT(1) AS correction_count,
                        MIN(created_at) AS first_correction_time,
                        MAX(created_at) AS last_correction_time
                    FROM portfolio_correction_logs
                    WHERE user_id = ? AND code IN ({placeholders})
                    GROUP BY code
                    """,
                    (user_id, *codes),
                )
            else:
                cursor.execute(
                    f"""
                    SELECT
                        code,
                        COUNT(1) AS correction_count,
                        MIN(created_at) AS first_correction_time,
                        MAX(created_at) AS last_correction_time
                    FROM portfolio_correction_logs
                    WHERE (user_id IS NULL OR user_id = '') AND code IN ({placeholders})
                    GROUP BY code
                    """,
                    codes,
                )
            correction_meta = {
                str(row["code"]): {
                    "correction_count": int(row["correction_count"] or 0),
                    "first_correction_time": str(row["first_correction_time"] or ""),
                    "last_correction_time": str(row["last_correction_time"] or ""),
                }
                for row in cursor.fetchall()
            }

        positions: List[Dict[str, Any]] = []
        nonzero_legacy_position_count = 0
        nonzero_legacy_adjustment_total = 0.0
        for row in portfolio_rows:
            code = str(row["code"] or "").strip()
            legacy_adjustment = float(row["adjustment"] or 0.0)
            has_nonzero_legacy = abs(legacy_adjustment) > 1e-9
            if has_nonzero_legacy:
                nonzero_legacy_position_count += 1
                nonzero_legacy_adjustment_total += legacy_adjustment

            tx_info = tx_meta.get(code, {})
            correction_info = correction_meta.get(code, {})
            positions.append(
                {
                    "code": code,
                    "name": str(row["name"] or ""),
                    "qty": float(row["qty"] or 0.0),
                    "price": float(row["price"] or 0.0),
                    "curr": str(row["curr"] or ""),
                    "asset_type": str(row["asset_type"] or ""),
                    "legacy_adjustment": legacy_adjustment,
                    "ledger_adjustment": float(ledger_sums.get(code, 0.0)),
                    "realized_pnl_adjustment": float(realized_sums.get(code, 0.0)),
                    "has_nonzero_legacy_adjustment": has_nonzero_legacy,
                    "tx_count": int(tx_info.get("tx_count") or 0),
                    "first_tx_time": str(tx_info.get("first_tx_time") or ""),
                    "last_tx_time": str(tx_info.get("last_tx_time") or ""),
                    "correction_count": int(correction_info.get("correction_count") or 0),
                    "first_correction_time": str(correction_info.get("first_correction_time") or ""),
                    "last_correction_time": str(correction_info.get("last_correction_time") or ""),
                    "migration_hint": "需要人工迁移" if has_nonzero_legacy else "可直接切新口径",
                }
            )

        ready_to_ignore_now = nonzero_legacy_position_count == 0
        return {
            "user_id": uid,
            "legacy_adjustment_ignored": self._is_portfolio_legacy_adjustment_ignored(cursor, user_id),
            "position_count": len(portfolio_rows),
            "nonzero_legacy_position_count": nonzero_legacy_position_count,
            "nonzero_legacy_adjustment_total": nonzero_legacy_adjustment_total,
            "ready_to_ignore_now": ready_to_ignore_now,
            "migration_status": "可直接切新口径" if ready_to_ignore_now else "仍需人工迁移",
            "positions": positions,
        }

    def get_portfolio_legacy_adjustment_migration_report(
        self,
        user_id: str = None,
    ) -> Dict[str, Any]:
        """获取单个用户的 legacy adjustment 迁移盘点结果。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            return self._build_portfolio_legacy_adjustment_migration_report(cursor, user_id)
        finally:
            conn.close()

    def list_portfolio_legacy_adjustment_migration_reports(self) -> List[Dict[str, Any]]:
        """列出当前库里所有有持仓或迁移状态记录的用户盘点结果。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT DISTINCT user_id
                FROM (
                    SELECT COALESCE(user_id, '') AS user_id FROM portfolio
                    UNION
                    SELECT COALESCE(user_id, '') AS user_id FROM portfolio_legacy_adjustment_states
                )
                ORDER BY CASE WHEN user_id = '' THEN 0 ELSE 1 END, user_id ASC
                """
            )
            user_ids = [str(row["user_id"] or "") for row in cursor.fetchall()]
            return [
                self._build_portfolio_legacy_adjustment_migration_report(cursor, uid or None)
                for uid in user_ids
            ]
        finally:
            conn.close()

    def _get_portfolio_adjustment_breakdown(
        self,
        cursor,
        code: str,
        *,
        legacy_adjustment: float = 0.0,
        include_legacy_adjustment: bool = True,
        user_id: str = None,
        ledger_id: int | None = None,
    ) -> Dict[str, float]:
        """返回单只持仓的旧 adjustment、现金收益事件和已实现盈亏汇总。"""
        ledger_map = self._fetch_portfolio_adjustment_ledger_sums(
            cursor,
            [code],
            user_id,
            ledger_id=ledger_id,
        )
        realized_map = self._fetch_portfolio_realized_pnl_sums(
            cursor,
            [code],
            user_id,
            ledger_id=ledger_id,
        )
        ledger_adjustment = float(ledger_map.get(str(code or "").strip(), 0.0))
        realized_pnl_adjustment = float(realized_map.get(str(code or "").strip(), 0.0))
        legacy_value = float(legacy_adjustment or 0.0) if include_legacy_adjustment else 0.0
        total_adjustment = legacy_value + ledger_adjustment + realized_pnl_adjustment
        return {
            "legacy_adjustment": legacy_value,
            "ledger_adjustment": ledger_adjustment,
            "cash_event_adjustment": ledger_adjustment,
            "realized_pnl_adjustment": realized_pnl_adjustment,
            "total_adjustment": total_adjustment,
        }

    def _append_portfolio_adjustment_event(
        self,
        cursor,
        *,
        code: str,
        event_type: str,
        amount: float,
        curr: str,
        user_id: str = None,
        note: str = "",
        source: str = "manual",
        related_tx_id: int | None = None,
        ledger_id: int = 0,
    ) -> int:
        """写入一条投资收益事件流水。"""
        normalized_type = str(event_type or "").strip()
        if normalized_type not in PORTFOLIO_ADJUSTMENT_EVENT_TYPES:
            raise ValueError(f"Unsupported portfolio adjustment event type: {normalized_type}")

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
                related_tx_id,
                ledger_id,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
            """,
            (
                user_id or "",
                str(code or "").strip(),
                normalized_type,
                float(amount),
                str(curr or "CNY").strip().upper() or "CNY",
                str(note or ""),
                str(source or "manual"),
                related_tx_id,
                ledger_id,
            ),
        )
        return int(cursor.lastrowid or 0)

    def _append_portfolio_correction_log(
        self,
        cursor,
        *,
        code: str,
        correction_type: str,
        before_qty: float | None,
        after_qty: float | None,
        before_price: float | None,
        after_price: float | None,
        note: str = "",
        user_id: str = None,
        legacy_ledger_id: int | None = None,
        created_at: str | None = None,
        ledger_id: int = 0,
    ) -> int:
        created_time = str(created_at or "").strip() or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            """
            INSERT INTO portfolio_correction_logs (
                user_id,
                code,
                correction_type,
                before_qty,
                after_qty,
                before_price,
                after_price,
                note,
                legacy_ledger_id,
                ledger_id,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
            """,
            (
                user_id or "",
                str(code or "").strip(),
                str(correction_type or "").strip() or "holding",
                before_qty,
                after_qty,
                before_price,
                after_price,
                str(note or "").strip(),
                legacy_ledger_id,
                ledger_id,
                created_time,
            ),
        )
        return int(cursor.lastrowid or 0)

    def _infer_portfolio_correction_type(
        self,
        *,
        before_qty: float | None,
        after_qty: float | None,
        before_price: float | None,
        after_price: float | None,
        note: str = "",
    ) -> str:
        clean_note = str(note or "").strip()
        has_cost = "成本" in clean_note
        has_qty = "数量" in clean_note
        if has_cost and has_qty:
            return "holding"
        if has_cost:
            return "cost_price"
        if has_qty:
            return "quantity"
        qty_changed = (
            before_qty is not None
            and after_qty is not None
            and abs(float(after_qty) - float(before_qty)) > 1e-6
        )
        price_changed = (
            before_price is not None
            and after_price is not None
            and abs(float(after_price) - float(before_price)) > 1e-9
        )
        if qty_changed and not price_changed:
            return "quantity"
        if price_changed and not qty_changed:
            return "cost_price"
        return "holding"

    def _migrate_portfolio_corrections_schema(self, cursor) -> None:
        """把旧 manual_adjustment 迁到修正审计表。"""
        cursor.execute(
            """
            SELECT id, user_id, code, note, created_at
            FROM portfolio_adjustment_ledger
            WHERE event_type = 'manual_adjustment'
            ORDER BY id ASC
            """
        )
        rows = cursor.fetchall()
        migrated = 0
        for row in rows:
            legacy_id = int(row["id"])
            cursor.execute(
                "SELECT id FROM portfolio_correction_logs WHERE legacy_ledger_id = ?",
                (legacy_id,),
            )
            if cursor.fetchone():
                continue
            self._append_portfolio_correction_log(
                cursor,
                code=str(row["code"] or ""),
                correction_type=self._infer_portfolio_correction_type(
                    before_qty=None,
                    after_qty=None,
                    before_price=None,
                    after_price=None,
                    note=str(row["note"] or ""),
                ),
                before_qty=None,
                after_qty=None,
                before_price=None,
                after_price=None,
                note=str(row["note"] or ""),
                user_id=str(row["user_id"] or ""),
                legacy_ledger_id=legacy_id,
                created_at=str(row["created_at"] or ""),
            )
            migrated += 1
        if migrated > 0:
            logger.info("Migrated %s manual adjustment rows to portfolio_correction_logs", migrated)

    # ─── 账本 CRUD ────────────────────────────────────

    def get_default_ledger_id(self, user_id: str) -> int:
        """返回用户的默认账本 ID，不存在时自动创建。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id FROM investment_ledgers WHERE user_id = ? AND is_default = 1",
                (user_id,),
            )
            row = cursor.fetchone()
            if row:
                return int(row[0])
            # 自动创建默认账本
            cursor.execute(
                """
                INSERT INTO investment_ledgers (user_id, name, is_default, sort_order)
                VALUES (?, '默认账本', 1, 0)
                """,
                (user_id,),
            )
            conn.commit()
            return int(cursor.lastrowid or 0)
        finally:
            conn.close()

    def get_ledgers(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户的所有账本列表。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, user_id, name, description, sort_order, is_default, created_at, updated_at
                FROM investment_ledgers
                WHERE user_id = ?
                ORDER BY sort_order, id
                """,
                (user_id,),
            )
            return [
                {
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "name": row["name"],
                    "description": row["description"] or "",
                    "sort_order": row["sort_order"],
                    "is_default": bool(row["is_default"]),
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
                for row in cursor.fetchall()
            ]
        finally:
            conn.close()

    def create_ledger(self, user_id: str, name: str, description: str = "") -> Dict[str, Any]:
        """创建新账本，返回 {"ok": True, "ledger_id": ...} 或错误。"""
        clean_name = str(name or "").strip()
        if not clean_name:
            return {"ok": False, "code": "INVALID_NAME", "error": "账本名称不能为空"}
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO investment_ledgers (user_id, name, description, sort_order, is_default)
                VALUES (?, ?, ?, (SELECT COALESCE(MAX(sort_order), 0) + 1 FROM investment_ledgers WHERE user_id = ?), 0)
                """,
                (user_id, clean_name, str(description or "").strip(), user_id),
            )
            conn.commit()
            return {"ok": True, "ledger_id": int(cursor.lastrowid or 0)}
        except Exception as exc:
            conn.rollback()
            if "UNIQUE constraint failed" in str(exc):
                return {"ok": False, "code": "DUPLICATE_NAME", "error": "同名账本已存在"}
            logger.error("Failed to create ledger: %s", exc)
            return {"ok": False, "code": "CREATE_FAILED", "error": "创建账本失败"}
        finally:
            conn.close()

    def update_ledger(self, ledger_id: int, user_id: str, name: str, description: str = "") -> Dict[str, Any]:
        """更新账本信息。"""
        clean_name = str(name or "").strip()
        if not clean_name:
            return {"ok": False, "code": "INVALID_NAME", "error": "账本名称不能为空"}
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE investment_ledgers
                SET name = ?, description = ?, updated_at = datetime('now','localtime')
                WHERE id = ? AND user_id = ?
                """,
                (clean_name, str(description or "").strip(), ledger_id, user_id),
            )
            if cursor.rowcount <= 0:
                return {"ok": False, "code": "NOT_FOUND", "error": "账本不存在"}
            conn.commit()
            return {"ok": True}
        except Exception as exc:
            conn.rollback()
            if "UNIQUE constraint failed" in str(exc):
                return {"ok": False, "code": "DUPLICATE_NAME", "error": "同名账本已存在"}
            logger.error("Failed to update ledger: %s", exc)
            return {"ok": False, "code": "UPDATE_FAILED", "error": "更新账本失败"}
        finally:
            conn.close()

    def reorder_ledgers(self, user_id: str, ledger_ids: List[int]) -> Dict[str, Any]:
        """按传入顺序重排账本。"""
        normalized_ids: List[int] = []
        seen_ids: set[int] = set()
        for raw_id in ledger_ids:
            try:
                ledger_id = int(raw_id)
            except (TypeError, ValueError):
                return {"ok": False, "code": "INVALID_LEDGER_IDS", "error": "账本排序参数不合法"}
            if ledger_id <= 0 or ledger_id in seen_ids:
                return {"ok": False, "code": "INVALID_LEDGER_IDS", "error": "账本排序参数不合法"}
            seen_ids.add(ledger_id)
            normalized_ids.append(ledger_id)
        if not normalized_ids:
            return {"ok": False, "code": "INVALID_LEDGER_IDS", "error": "账本排序参数不合法"}

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id
                FROM investment_ledgers
                WHERE user_id = ?
                ORDER BY sort_order, id
                """,
                (user_id,),
            )
            existing_ids = [int(row["id"]) for row in cursor.fetchall()]
            if sorted(existing_ids) != sorted(normalized_ids):
                return {"ok": False, "code": "INVALID_LEDGER_IDS", "error": "账本列表不完整或包含非法账本"}

            for index, ledger_id in enumerate(normalized_ids):
                cursor.execute(
                    """
                    UPDATE investment_ledgers
                    SET sort_order = ?, updated_at = datetime('now','localtime')
                    WHERE id = ? AND user_id = ?
                    """,
                    (index, ledger_id, user_id),
                )
            conn.commit()
            return {"ok": True}
        except Exception as exc:
            conn.rollback()
            logger.error("Failed to reorder ledgers: %s", exc)
            return {"ok": False, "code": "REORDER_FAILED", "error": "账本排序失败"}
        finally:
            conn.close()

    def delete_ledger(self, ledger_id: int, user_id: str) -> Dict[str, Any]:
        """删除账本（非默认 + 无持仓才允许）。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id, is_default FROM investment_ledgers WHERE id = ? AND user_id = ?",
                (ledger_id, user_id),
            )
            row = cursor.fetchone()
            if not row:
                return {"ok": False, "code": "NOT_FOUND", "error": "账本不存在"}
            if row["is_default"]:
                return {"ok": False, "code": "IS_DEFAULT", "error": "默认账本不能删除"}
            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM portfolio WHERE ledger_id = ? AND user_id = ? AND qty > 0",
                (ledger_id, user_id),
            )
            holdings_row = cursor.fetchone()
            holdings_count = int(holdings_row["cnt"]) if holdings_row else 0
            if holdings_count > 0:
                return {"ok": False, "code": "HAS_HOLDINGS", "error": "账本下还有持仓，不能删除"}
            cursor.execute(
                "DELETE FROM ledger_daily_snapshots WHERE ledger_id = ? AND user_id = ?",
                (ledger_id, user_id),
            )
            cursor.execute(
                "DELETE FROM investment_ledgers WHERE id = ? AND user_id = ?",
                (ledger_id, user_id),
            )
            conn.commit()
            return {"ok": True}
        except Exception as exc:
            conn.rollback()
            logger.error("Failed to delete ledger: %s", exc)
            return {"ok": False, "code": "DELETE_FAILED", "error": "删除账本失败"}
        finally:
            conn.close()

    # ─── 持仓查询 ────────────────────────────────────

    def get_portfolio(
        self,
        asset_type: str = "all",
        user_id: str = None,
        include_closed: bool = False,
        ledger_id: int | None = None,
    ) -> List[Dict[str, Any]]:
        """获取持仓数据，支持按类型筛选。"""
        conn = self.get_connection()
        cursor = conn.cursor()

        logger.info("get_portfolio called with asset_type: %s, user_id: %s, ledger_id: %s", asset_type, user_id, ledger_id)

        user_condition = "user_id = ?" if user_id else "(user_id IS NULL OR user_id = '')"
        user_param = (user_id,) if user_id else ()
        qty_condition = "" if include_closed else " AND qty != 0"
        ledger_condition = " AND ledger_id = ?" if ledger_id is not None else ""
        ledger_param = (ledger_id,) if ledger_id is not None else ()

        if asset_type == "all":
            cursor.execute(
                f"""
                SELECT code, name, qty, price, curr, adjustment, asset_type, logo_url, ledger_id
                FROM portfolio
                WHERE {user_condition}{qty_condition}{ledger_condition}
                ORDER BY code
                """,
                user_param + ledger_param,
            )
        elif asset_type in ("a", "us", "hk", "fund"):
            cursor.execute(
                f"""
                SELECT code, name, qty, price, curr, adjustment, asset_type, logo_url, ledger_id
                FROM portfolio
                WHERE {user_condition}{qty_condition}{ledger_condition} AND asset_type = ?
                ORDER BY code
                """,
                user_param + ledger_param + (asset_type,),
            )
        else:
            cursor.execute(
                f"""
                SELECT code, name, qty, price, curr, adjustment, asset_type, logo_url, ledger_id
                FROM portfolio
                WHERE {user_condition}{qty_condition}{ledger_condition}
                ORDER BY code
                """,
                user_param + ledger_param,
            )

        data = []
        from .asset_type import infer_category_type
        rows = cursor.fetchall()
        include_legacy_adjustment = not self._is_portfolio_legacy_adjustment_ignored(cursor, user_id)
        ledger_sums = self._fetch_portfolio_adjustment_ledger_sums(
            cursor,
            [row["code"] for row in rows],
            user_id,
            ledger_id=ledger_id,
        )
        realized_sums = self._fetch_portfolio_realized_pnl_sums(
            cursor,
            [row["code"] for row in rows],
            user_id,
            ledger_id=ledger_id,
        )

        for row in rows:
            code = row["code"]
            name = row["name"]
            asset_type_value = row["asset_type"] if "asset_type" in row.keys() else ""
            legacy_adjustment = (
                float(row["adjustment"] or 0.0)
                if include_legacy_adjustment
                else 0.0
            )
            ledger_adjustment = float(ledger_sums.get(code, 0.0))
            realized_pnl_adjustment = float(realized_sums.get(code, 0.0))
            total_adjustment = legacy_adjustment + ledger_adjustment + realized_pnl_adjustment
            data.append(
                {
                    "code": code,
                    "name": name,
                    "qty": float(row["qty"]),
                    "price": float(row["price"]),
                    "curr": row["curr"],
                    "adjustment": total_adjustment,
                    "adjustment_total": total_adjustment,
                    "legacy_adjustment": legacy_adjustment,
                    "ledger_adjustment": ledger_adjustment,
                    "cash_event_adjustment": ledger_adjustment,
                    "realized_pnl_adjustment": realized_pnl_adjustment,
                    "legacy_adjustment_ignored": not include_legacy_adjustment,
                    "asset_type": asset_type_value,
                    "category_type": infer_category_type(code, name, asset_type_value),
                    "logo_url": row["logo_url"] if "logo_url" in row.keys() else None,
                    "ledger_id": int(row["ledger_id"]) if "ledger_id" in row.keys() and row["ledger_id"] else 0,
                }
            )

        logger.info("get_portfolio returned %s records for type %s", len(data), asset_type)
        conn.close()
        return data

    def get_distinct_portfolio_codes(self, include_closed: bool = False) -> List[str]:
        """获取全库唯一证券代码列表（用于行情预取）。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        qty_condition = "" if include_closed else " AND qty != 0"
        try:
            cursor.execute(
                f"""
                SELECT DISTINCT code
                FROM portfolio
                WHERE COALESCE(code, '') != ''{qty_condition}
                ORDER BY code
                """
            )
            return [row[0] for row in cursor.fetchall() if row and row[0]]
        finally:
            conn.close()

    def get_asset(self, code: str, user_id: str = None, ledger_id: int | None = None) -> Optional[Dict[str, Any]]:
        """获取单个资产信息。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        ledger_condition = " AND ledger_id = ?" if ledger_id is not None else ""
        ledger_param = (ledger_id,) if ledger_id is not None else ()

        if user_id:
            cursor.execute(
                f"""
                SELECT code, name, qty, price, curr, adjustment, asset_type
                FROM portfolio
                WHERE code = ? AND user_id = ?{ledger_condition}
                """,
                (code, user_id) + ledger_param,
            )
        else:
            cursor.execute(
                f"""
                SELECT code, name, qty, price, curr, adjustment, asset_type
                FROM portfolio
                WHERE code = ? AND (user_id IS NULL OR user_id = ''){ledger_condition}
                """,
                (code,) + ledger_param,
            )

        row = cursor.fetchone()
        breakdown = None
        include_legacy_adjustment = True
        if row:
            include_legacy_adjustment = not self._is_portfolio_legacy_adjustment_ignored(cursor, user_id)
            breakdown = self._get_portfolio_adjustment_breakdown(
                cursor,
                code,
                legacy_adjustment=float(row["adjustment"] or 0.0),
                include_legacy_adjustment=include_legacy_adjustment,
                user_id=user_id,
                ledger_id=ledger_id,
            )
        conn.close()
        if row:
            return {
                "code": row["code"],
                "name": row["name"],
                "qty": float(row["qty"]),
                "price": float(row["price"]),
                "curr": row["curr"],
                "adjustment": float((breakdown or {}).get("total_adjustment", row["adjustment"] or 0.0)),
                "adjustment_total": float((breakdown or {}).get("total_adjustment", row["adjustment"] or 0.0)),
                "legacy_adjustment": float((breakdown or {}).get("legacy_adjustment", row["adjustment"] or 0.0)),
                "ledger_adjustment": float((breakdown or {}).get("ledger_adjustment", 0.0)),
                "legacy_adjustment_ignored": not include_legacy_adjustment,
                "asset_type": row["asset_type"] if "asset_type" in row.keys() else "",
            }
        return None

    def add_asset(
        self,
        data: Dict[str, Any],
        user_id: str = None,
        allow_legacy_adjustment_write: bool = False,
        ledger_id: int | None = None,
    ) -> bool:
        """添加或更新资产。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        resolved_ledger_id = ledger_id if ledger_id is not None else int(data.get("ledger_id") or 0)

        try:
            incoming_name = str(data.get("name") or "").strip()
            if not data.get("logo_url"):
                data["logo_url"] = suggest_logo_url(data.get("code"), incoming_name)

            ledger_condition = " AND ledger_id = ?" if resolved_ledger_id else ""
            ledger_param = (resolved_ledger_id,) if resolved_ledger_id else ()

            if user_id:
                cursor.execute(
                    f"SELECT id, name, adjustment FROM portfolio WHERE code = ? AND user_id = ?{ledger_condition}",
                    (data["code"], user_id) + ledger_param,
                )
            else:
                cursor.execute(
                    f"SELECT id, name, adjustment FROM portfolio WHERE code = ? AND (user_id IS NULL OR user_id = ''){ledger_condition}",
                    (data["code"],) + ledger_param,
                )
            existing = cursor.fetchone()

            if existing:
                existing_name = str(existing["name"] or "").strip()
                next_name = existing_name or incoming_name or data["code"]
                next_adjustment = (
                    float(data.get("adjustment", 0.0))
                    if allow_legacy_adjustment_write
                    else float(existing["adjustment"] or 0.0)
                )
                if user_id:
                    cursor.execute(
                        f"""
                        UPDATE portfolio
                        SET name = ?, qty = ?, price = ?, curr = ?, adjustment = ?, asset_type = ?, updated_at = datetime('now','localtime')
                        WHERE code = ? AND user_id = ?{ledger_condition}
                        """,
                        (
                            next_name,
                            data["qty"],
                            data["price"],
                            data.get("curr", "CNY"),
                            next_adjustment,
                            data.get("asset_type", "a"),
                            data["code"],
                            user_id,
                        )
                        + ledger_param,
                    )
                else:
                    cursor.execute(
                        f"""
                        UPDATE portfolio
                        SET name = ?, qty = ?, price = ?, curr = ?, adjustment = ?, asset_type = ?, updated_at = datetime('now','localtime')
                        WHERE code = ? AND (user_id IS NULL OR user_id = ''){ledger_condition}
                        """,
                        (
                            next_name,
                            data["qty"],
                            data["price"],
                            data.get("curr", "CNY"),
                            next_adjustment,
                            data.get("asset_type", "a"),
                            data["code"],
                        )
                        + ledger_param,
                    )
            else:
                next_name = incoming_name or data["code"]
                next_adjustment = float(data.get("adjustment", 0.0)) if allow_legacy_adjustment_write else 0.0
                if user_id:
                    cursor.execute(
                        """
                        INSERT INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, user_id, ledger_id, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
                        """,
                        (
                            data["code"],
                            next_name,
                            data["qty"],
                            data["price"],
                            data.get("curr", "CNY"),
                            next_adjustment,
                            data.get("asset_type", "a"),
                            user_id,
                            resolved_ledger_id,
                        ),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, ledger_id, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
                        """,
                        (
                            data["code"],
                            next_name,
                            data["qty"],
                            data["price"],
                            data.get("curr", "CNY"),
                            next_adjustment,
                            data.get("asset_type", "a"),
                            resolved_ledger_id,
                        ),
                    )
                if not allow_legacy_adjustment_write:
                    self._append_portfolio_correction_log(
                        cursor,
                        code=str(data["code"] or "").strip(),
                        correction_type="opening_balance",
                        before_qty=0.0,
                        after_qty=float(data["qty"] or 0.0),
                        before_price=None,
                        after_price=float(data["price"] or 0.0),
                        note="初始持仓录入",
                        user_id=user_id,
                        ledger_id=resolved_ledger_id,
                    )

            conn.commit()
            logger.info("Asset added/updated: %s", data["code"])
            return True
        except Exception as exc:
            logger.error(
                "Failed to add asset: code=%s user_id=%s err=%s",
                data.get("code"),
                user_id or "",
                exc,
            )
            conn.rollback()
            return False
        finally:
            conn.close()

    def update_asset(
        self,
        code: str,
        field: str,
        value: float,
        user_id: str = None,
        allow_legacy_adjustment_write: bool = False,
        ledger_id: int | None = None,
    ) -> bool:
        """更新资产字段。"""
        if field not in self.VALID_FIELDS:
            logger.error("Invalid field name: %s", field)
            return False
        if field == "adjustment" and not allow_legacy_adjustment_write:
            logger.warning("Blocked legacy adjustment update: code=%s user_id=%s", code, user_id or "")
            return False

        conn = self.get_connection()
        cursor = conn.cursor()
        ledger_condition = " AND ledger_id = ?" if ledger_id is not None else ""
        ledger_param = (ledger_id,) if ledger_id is not None else ()

        try:
            if user_id:
                user_condition = "AND user_id = ?"
                params_suffix = (code, user_id) + ledger_param
            else:
                user_condition = "AND (user_id IS NULL OR user_id = '')"
                params_suffix = (code,) + ledger_param

            if field == "adjustment":
                cursor.execute(
                    f"""
                    UPDATE portfolio SET adjustment = COALESCE(adjustment, 0) + ?, updated_at = datetime('now','localtime')
                    WHERE code = ? {user_condition}{ledger_condition}
                    """,
                    (value,) + params_suffix,
                )
            else:
                cursor.execute(
                    f"""
                    UPDATE portfolio SET {field} = ?, updated_at = datetime('now','localtime')
                    WHERE code = ? {user_condition}{ledger_condition}
                    """,
                    (value,) + params_suffix,
                )

            if cursor.rowcount > 0:
                conn.commit()
                logger.info("Asset updated: %s, %s = %s", code, field, value)
                return True
            return False
        except Exception as exc:
            logger.error("Failed to update asset: %s", exc)
            conn.rollback()
            return False
        finally:
            conn.close()

    def modify_asset(
        self,
        code: str,
        qty: float,
        price: float,
        adjustment: float | None = None,
        note: str = "",
        user_id: str = None,
        return_detail: bool = False,
        ledger_id: int | None = None,
    ):
        """修正资产数据。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        ledger_condition = " AND ledger_id = ?" if ledger_id is not None else ""
        ledger_param = (ledger_id,) if ledger_id is not None else ()

        try:
            if user_id:
                cursor.execute(
                    f"""
                    SELECT name, qty, price, curr, adjustment, asset_type
                    FROM portfolio
                    WHERE code = ? AND user_id = ?{ledger_condition}
                    """,
                    (code, user_id) + ledger_param,
                )
            else:
                cursor.execute(
                    f"""
                    SELECT name, qty, price, curr, adjustment, asset_type
                    FROM portfolio
                    WHERE code = ? AND (user_id IS NULL OR user_id = ''){ledger_condition}
                    """,
                    (code,) + ledger_param,
                )
            old_row = cursor.fetchone()
            if not old_row:
                if return_detail:
                    return {"ok": False, "code": "ASSET_NOT_FOUND", "error": "Asset not found"}
                return False

            before_asset = {
                "code": code,
                "name": old_row["name"],
                "qty": float(old_row["qty"]),
                "price": float(old_row["price"]),
                "curr": old_row["curr"],
                "adjustment": float(old_row["adjustment"]),
                "asset_type": old_row["asset_type"] if "asset_type" in old_row.keys() else "a",
            }
            adjustment_breakdown = self._get_portfolio_adjustment_breakdown(
                cursor,
                code,
                legacy_adjustment=before_asset["adjustment"],
                user_id=user_id,
                ledger_id=ledger_id,
            )
            ledger_adjustment = float(adjustment_breakdown["ledger_adjustment"])
            old_total_adjustment = float(adjustment_breakdown["total_adjustment"])
            next_legacy_adjustment = before_asset["adjustment"]

            if user_id:
                cursor.execute(
                    f"""
                    UPDATE portfolio
                    SET qty = ?, price = ?, updated_at = datetime('now','localtime')
                    WHERE code = ? AND user_id = ?{ledger_condition}
                    """,
                    (qty, price, code, user_id) + ledger_param,
                )
            else:
                cursor.execute(
                    f"""
                    UPDATE portfolio
                    SET qty = ?, price = ?, updated_at = datetime('now','localtime')
                    WHERE code = ? AND (user_id IS NULL OR user_id = ''){ledger_condition}
                    """,
                    (qty, price, code) + ledger_param,
                )

            if cursor.rowcount <= 0:
                if return_detail:
                    return {"ok": False, "code": "ASSET_NOT_FOUND", "error": "Asset not found"}
                return False

            clean_note = str(note or "").strip()
            qty_changed = abs(float(qty) - before_asset["qty"]) > 1e-6
            price_changed = abs(float(price) - before_asset["price"]) > 1e-9
            correction_log_id = None
            if qty_changed or price_changed or clean_note:
                correction_log_id = self._append_portfolio_correction_log(
                    cursor,
                    code=code,
                    correction_type=self._infer_portfolio_correction_type(
                        before_qty=before_asset["qty"],
                        after_qty=float(qty),
                        before_price=before_asset["price"],
                        after_price=float(price),
                        note=clean_note,
                    ),
                    before_qty=before_asset["qty"],
                    after_qty=float(qty),
                    before_price=before_asset["price"],
                    after_price=float(price),
                    note=clean_note,
                    user_id=user_id,
                    ledger_id=ledger_id or 0,
                )

            conn.commit()
            logger.info(
                "Asset modified: %s, qty=%s, price=%s, legacy_adj=%s, total_adj_before=%s, note=%s, correction_log_id=%s",
                code,
                qty,
                price,
                next_legacy_adjustment,
                old_total_adjustment,
                clean_note,
                correction_log_id,
            )
            if return_detail:
                return {
                    "ok": True,
                    "correction_log_id": correction_log_id,
                    "before_asset": before_asset,
                    "after_asset": {
                        "code": code,
                        "name": before_asset["name"],
                        "qty": float(qty),
                        "price": float(price),
                        "curr": before_asset["curr"],
                        "adjustment": float(next_legacy_adjustment),
                        "adjustment_total": float(old_total_adjustment),
                        "legacy_adjustment": float(next_legacy_adjustment),
                        "ledger_adjustment": float(ledger_adjustment),
                        "cash_event_adjustment": float(adjustment_breakdown["cash_event_adjustment"]),
                        "realized_pnl_adjustment": float(adjustment_breakdown["realized_pnl_adjustment"]),
                        "asset_type": before_asset["asset_type"],
                    },
                }
            return True
        except Exception as exc:
            logger.error("Failed to modify asset: %s", exc)
            conn.rollback()
            if return_detail:
                return {"ok": False, "code": "ASSET_MODIFY_FAILED", "error": "Failed to modify asset"}
            return False
        finally:
            conn.close()

    def add_portfolio_adjustment_event(
        self,
        code: str,
        event_type: str,
        amount: float,
        note: str = "",
        curr: str | None = None,
        user_id: str = None,
        return_detail: bool = False,
        ledger_id: int | None = None,
    ):
        """新增一条投资收益事件流水。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        ledger_condition = " AND ledger_id = ?" if ledger_id is not None else ""
        ledger_param = (ledger_id,) if ledger_id is not None else ()

        try:
            if user_id:
                cursor.execute(
                    f"""
                    SELECT name, qty, price, curr, adjustment, asset_type
                    FROM portfolio
                    WHERE code = ? AND user_id = ?{ledger_condition}
                    """,
                    (code, user_id) + ledger_param,
                )
            else:
                cursor.execute(
                    f"""
                    SELECT name, qty, price, curr, adjustment, asset_type
                    FROM portfolio
                    WHERE code = ? AND (user_id IS NULL OR user_id = ''){ledger_condition}
                    """,
                    (code,) + ledger_param,
                )
            row = cursor.fetchone()
            if not row:
                if return_detail:
                    return {"ok": False, "code": "ASSET_NOT_FOUND", "error": "Asset not found"}
                return False

            normalized_type = str(event_type or "").strip()
            normalized_amount = float(amount or 0.0)
            clean_note = str(note or "").strip()
            before_asset = {
                "code": code,
                "name": row["name"],
                "qty": float(row["qty"]),
                "price": float(row["price"]),
                "curr": row["curr"],
                "adjustment": float(row["adjustment"] or 0.0),
                "asset_type": row["asset_type"] if "asset_type" in row.keys() else "a",
            }
            adjustment_breakdown = self._get_portfolio_adjustment_breakdown(
                cursor,
                code,
                legacy_adjustment=before_asset["adjustment"],
                user_id=user_id,
                ledger_id=ledger_id,
            )
            old_ledger_adjustment = float(adjustment_breakdown["ledger_adjustment"])
            old_realized_pnl_adjustment = float(adjustment_breakdown["realized_pnl_adjustment"])
            old_total_adjustment = float(adjustment_breakdown["total_adjustment"])

            ledger_event_id = self._append_portfolio_adjustment_event(
                cursor,
                code=code,
                event_type=normalized_type,
                amount=normalized_amount,
                curr=curr or before_asset["curr"],
                user_id=user_id,
                note=clean_note,
                source="manual_adjust_dialog",
                ledger_id=ledger_id or 0,
            )

            conn.commit()
            if return_detail:
                return {
                    "ok": True,
                    "ledger_event_id": ledger_event_id,
                    "before_asset": before_asset,
                    "after_asset": {
                        "code": code,
                        "name": before_asset["name"],
                        "qty": before_asset["qty"],
                        "price": before_asset["price"],
                        "curr": before_asset["curr"],
                        "adjustment": before_asset["adjustment"],
                        "adjustment_total": old_total_adjustment + normalized_amount,
                        "legacy_adjustment": before_asset["adjustment"],
                        "ledger_adjustment": old_ledger_adjustment + normalized_amount,
                        "cash_event_adjustment": old_ledger_adjustment + normalized_amount,
                        "realized_pnl_adjustment": old_realized_pnl_adjustment,
                        "asset_type": before_asset["asset_type"],
                    },
                }
            return True
        except Exception as exc:
            logger.error(
                "Failed to add portfolio adjustment event: code=%s event_type=%s err=%s",
                code,
                event_type,
                exc,
            )
            conn.rollback()
            if return_detail:
                return {
                    "ok": False,
                    "code": "PORTFOLIO_ADJUSTMENT_EVENT_FAILED",
                    "error": "Failed to add portfolio adjustment event",
                }
            return False
        finally:
            conn.close()

    def delete_asset(self, code: str, user_id: str = None, ledger_id: int | None = None) -> bool:
        """删除资产。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        ledger_condition = " AND ledger_id = ?" if ledger_id is not None else ""
        ledger_param = (ledger_id,) if ledger_id is not None else ()

        try:
            if user_id:
                cursor.execute(
                    f"DELETE FROM portfolio WHERE code = ? AND user_id = ?{ledger_condition}",
                    (code, user_id) + ledger_param,
                )
            else:
                cursor.execute(
                    f"DELETE FROM portfolio WHERE code = ? AND (user_id IS NULL OR user_id = ''){ledger_condition}",
                    (code,) + ledger_param,
                )
            conn.commit()
            logger.info("Asset deleted: %s", code)
            return True
        except Exception as exc:
            logger.error("Failed to delete asset: %s", exc)
            conn.rollback()
            return False
        finally:
            conn.close()

    def delete_asset_corrective(self, code: str, user_id: str = None, ledger_id: int | None = None) -> Optional[Dict[str, Any]]:
        """删除资产并清理该资产交易历史与受影响快照区间。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        ledger_condition = " AND ledger_id = ?" if ledger_id is not None else ""
        ledger_param = (ledger_id,) if ledger_id is not None else ()

        try:
            if user_id:
                cursor.execute(
                    f"""
                    SELECT time FROM transactions
                    WHERE code = ? AND user_id = ?{ledger_condition}
                    ORDER BY time ASC
                    LIMIT 1
                    """,
                    (code, user_id) + ledger_param,
                )
                tx_row = cursor.fetchone()
                cursor.execute(
                    f"""
                    SELECT created_at
                    FROM portfolio_correction_logs
                    WHERE code = ? AND user_id = ?{ledger_condition}
                    ORDER BY created_at ASC, id ASC
                    LIMIT 1
                    """,
                    (code, user_id) + ledger_param,
                )
                correction_row = cursor.fetchone()
                cursor.execute(
                    f"""
                    SELECT created_at, updated_at
                    FROM portfolio
                    WHERE code = ? AND user_id = ?{ledger_condition}
                    LIMIT 1
                    """,
                    (code, user_id) + ledger_param,
                )
                pf_row = cursor.fetchone()
            else:
                cursor.execute(
                    f"""
                    SELECT time FROM transactions
                    WHERE code = ? AND (user_id IS NULL OR user_id = ''){ledger_condition}
                    ORDER BY time ASC
                    LIMIT 1
                    """,
                    (code,) + ledger_param,
                )
                tx_row = cursor.fetchone()
                cursor.execute(
                    f"""
                    SELECT created_at
                    FROM portfolio_correction_logs
                    WHERE code = ? AND (user_id IS NULL OR user_id = ''){ledger_condition}
                    ORDER BY created_at ASC, id ASC
                    LIMIT 1
                    """,
                    (code,) + ledger_param,
                )
                correction_row = cursor.fetchone()
                cursor.execute(
                    f"""
                    SELECT created_at, updated_at
                    FROM portfolio
                    WHERE code = ? AND (user_id IS NULL OR user_id = ''){ledger_condition}
                    LIMIT 1
                    """,
                    (code,) + ledger_param,
                )
                pf_row = cursor.fetchone()

            from_date = datetime.now().strftime("%Y-%m-%d")
            candidate_dates: List[str] = []
            tx_time = str(tx_row["time"]) if tx_row and tx_row["time"] else ""
            correction_time = str(correction_row["created_at"]) if correction_row and correction_row["created_at"] else ""
            pf_created_at = str(pf_row["created_at"] or "") if pf_row else ""
            pf_updated_at = str(pf_row["updated_at"] or "") if pf_row else ""
            for raw_value in (tx_time, correction_time, pf_created_at, pf_updated_at):
                if len(raw_value) >= 10:
                    candidate_dates.append(raw_value[:10])
            if candidate_dates:
                from_date = min(candidate_dates)

            if user_id:
                cursor.execute(
                    f"DELETE FROM portfolio WHERE code = ? AND user_id = ?{ledger_condition}",
                    (code, user_id) + ledger_param,
                )
            else:
                cursor.execute(
                    f"DELETE FROM portfolio WHERE code = ? AND (user_id IS NULL OR user_id = ''){ledger_condition}",
                    (code,) + ledger_param,
                )
            portfolio_deleted = cursor.rowcount

            if user_id:
                cursor.execute(
                    f"DELETE FROM transactions WHERE code = ? AND user_id = ?{ledger_condition}",
                    (code, user_id) + ledger_param,
                )
            else:
                cursor.execute(
                    f"DELETE FROM transactions WHERE code = ? AND (user_id IS NULL OR user_id = ''){ledger_condition}",
                    (code,) + ledger_param,
                )
            tx_deleted = cursor.rowcount

            if user_id:
                cursor.execute(
                    f"DELETE FROM portfolio_adjustment_ledger WHERE code = ? AND user_id = ?{ledger_condition}",
                    (code, user_id) + ledger_param,
                )
            else:
                cursor.execute(
                    f"DELETE FROM portfolio_adjustment_ledger WHERE code = ? AND (user_id IS NULL OR user_id = ''){ledger_condition}",
                    (code,) + ledger_param,
                )
            ledger_deleted = cursor.rowcount

            if user_id:
                cursor.execute(
                    f"DELETE FROM portfolio_correction_logs WHERE code = ? AND user_id = ?{ledger_condition}",
                    (code, user_id) + ledger_param,
                )
            else:
                cursor.execute(
                    f"DELETE FROM portfolio_correction_logs WHERE code = ? AND (user_id IS NULL OR user_id = ''){ledger_condition}",
                    (code,) + ledger_param,
                )
            correction_deleted = cursor.rowcount

            if portfolio_deleted <= 0 and tx_deleted <= 0 and ledger_deleted <= 0 and correction_deleted <= 0:
                logger.info("Corrective delete noop: %s", code)

            if user_id:
                cursor.execute("DELETE FROM daily_snapshots WHERE date >= ? AND user_id = ?", (from_date, user_id))
            else:
                cursor.execute(
                    "DELETE FROM daily_snapshots WHERE date >= ? AND (user_id IS NULL OR user_id = '')",
                    (from_date,),
                )
            snapshots_deleted = cursor.rowcount

            if user_id:
                if ledger_id is not None:
                    cursor.execute(
                        "DELETE FROM ledger_daily_snapshots WHERE date >= ? AND user_id = ? AND ledger_id = ?",
                        (from_date, user_id, ledger_id),
                    )
                else:
                    cursor.execute(
                        "DELETE FROM ledger_daily_snapshots WHERE date >= ? AND user_id = ?",
                        (from_date, user_id),
                    )
            else:
                if ledger_id is not None:
                    cursor.execute(
                        "DELETE FROM ledger_daily_snapshots WHERE date >= ? AND user_id = '' AND ledger_id = ?",
                        (from_date, ledger_id),
                    )
                else:
                    cursor.execute(
                        "DELETE FROM ledger_daily_snapshots WHERE date >= ? AND user_id = ''",
                        (from_date,),
                    )
            ledger_snapshots_deleted = cursor.rowcount

            conn.commit()
            logger.info(
                "Corrective delete done: code=%s from_date=%s portfolio=%s tx=%s ledger=%s correction=%s snapshots=%s ledger_snapshots=%s",
                code,
                from_date,
                portfolio_deleted,
                tx_deleted,
                ledger_deleted,
                correction_deleted,
                snapshots_deleted,
                ledger_snapshots_deleted,
            )
            return {
                "portfolio": int(portfolio_deleted),
                "transactions": int(tx_deleted),
                "ledger": int(ledger_deleted),
                "corrections": int(correction_deleted),
                "snapshots": int(snapshots_deleted),
                "ledger_snapshots": int(ledger_snapshots_deleted),
                "from_date": from_date,
            }
        except Exception as exc:
            logger.error("Failed to corrective delete asset: %s", exc)
            conn.rollback()
            return None
        finally:
            conn.close()

    def buy_asset(
        self,
        code: str,
        price: float,
        qty: float,
        user_id: str = None,
        return_detail: bool = False,
        ledger_id: int | None = None,
    ):
        """加仓。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        ledger_condition = " AND ledger_id = ?" if ledger_id is not None else ""
        ledger_param = (ledger_id,) if ledger_id is not None else ()

        try:
            if user_id:
                cursor.execute(
                    f"""
                    SELECT name, qty, price, curr, adjustment, asset_type
                    FROM portfolio
                    WHERE code = ? AND user_id = ?{ledger_condition}
                    """,
                    (code, user_id) + ledger_param,
                )
            else:
                cursor.execute(
                    f"""
                    SELECT name, qty, price, curr, adjustment, asset_type
                    FROM portfolio
                    WHERE code = ? AND (user_id IS NULL OR user_id = ''){ledger_condition}
                    """,
                    (code,) + ledger_param,
                )
            row = cursor.fetchone()

            if not row:
                if return_detail:
                    return {"ok": False, "code": "ASSET_NOT_FOUND", "error": "Asset not found"}
                return False

            name = row["name"]
            old_qty = float(row["qty"])
            old_price = float(row["price"])
            old_adjustment = float(row["adjustment"])
            curr = row["curr"]
            asset_type = row["asset_type"] if "asset_type" in row.keys() else "a"

            before_asset = {
                "code": code,
                "name": name,
                "qty": old_qty,
                "price": old_price,
                "curr": curr,
                "adjustment": old_adjustment,
                "asset_type": asset_type,
            }

            new_qty = old_qty + qty
            new_price = (old_qty * old_price + qty * price) / new_qty if new_qty > 0 else 0

            if user_id:
                cursor.execute(
                    f"""
                    UPDATE portfolio SET qty = ?, price = ?, updated_at = datetime('now','localtime')
                    WHERE code = ? AND user_id = ?{ledger_condition}
                    """,
                    (new_qty, new_price, code, user_id) + ledger_param,
                )
            else:
                cursor.execute(
                    f"""
                    UPDATE portfolio SET qty = ?, price = ?, updated_at = datetime('now','localtime')
                    WHERE code = ? AND (user_id IS NULL OR user_id = ''){ledger_condition}
                    """,
                    (new_qty, new_price, code) + ledger_param,
                )

            tx_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            tx_identity = self._build_transaction_identity(
                code=code,
                curr=curr,
                asset_type=asset_type,
                tx_time=tx_time,
            )
            cursor.execute(
                """
                INSERT INTO transactions (
                    time, code, name, type, price, qty, amount, pnl, curr, market, effective_date, user_id, ledger_id
                )
                VALUES (?, ?, ?, '加仓', ?, ?, ?, 0, ?, ?, ?, ?, ?)
                """,
                (
                    tx_time,
                    tx_identity["code"],
                    name,
                    price,
                    qty,
                    price * qty,
                    tx_identity["curr"],
                    tx_identity["market"],
                    tx_identity["effective_date"],
                    user_id,
                    ledger_id or 0,
                ),
            )
            tx_id = int(cursor.lastrowid or 0)

            conn.commit()
            logger.info("Buy: %s, qty=%s, price=%s", code, qty, price)
            if return_detail:
                return {
                    "ok": True,
                    "tx_id": tx_id,
                    "before_asset": before_asset,
                    "after_asset": {
                        "code": code,
                        "name": name,
                        "qty": float(new_qty),
                        "price": float(new_price),
                        "curr": curr,
                        "adjustment": old_adjustment,
                        "asset_type": asset_type,
                    },
                }
            return True
        except Exception as exc:
            logger.error("Failed to buy asset: %s", exc)
            conn.rollback()
            if return_detail:
                return {"ok": False, "code": "ASSET_BUY_FAILED", "error": "Failed to buy asset"}
            return False
        finally:
            conn.close()

    def sell_asset(
        self,
        code: str,
        price: float,
        qty: float,
        user_id: str = None,
        return_detail: bool = False,
        ledger_id: int | None = None,
    ):
        """减仓。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        ledger_condition = " AND ledger_id = ?" if ledger_id is not None else ""
        ledger_param = (ledger_id,) if ledger_id is not None else ()

        try:
            if user_id:
                cursor.execute(
                    f"""
                    SELECT name, qty, price, curr, adjustment, asset_type
                    FROM portfolio
                    WHERE code = ? AND user_id = ?{ledger_condition}
                    """,
                    (code, user_id) + ledger_param,
                )
            else:
                cursor.execute(
                    f"""
                    SELECT name, qty, price, curr, adjustment, asset_type
                    FROM portfolio
                    WHERE code = ? AND (user_id IS NULL OR user_id = ''){ledger_condition}
                    """,
                    (code,) + ledger_param,
                )
            row = cursor.fetchone()

            if not row:
                if return_detail:
                    return {"ok": False, "code": "ASSET_NOT_FOUND", "error": "Asset not found"}
                return False

            name = row["name"]
            old_qty = float(row["qty"])
            old_price = float(row["price"])
            curr = row["curr"]
            old_adj = float(row["adjustment"])
            asset_type = row["asset_type"] if "asset_type" in row.keys() else "a"
            adjustment_breakdown = self._get_portfolio_adjustment_breakdown(
                cursor,
                code,
                legacy_adjustment=old_adj,
                user_id=user_id,
                ledger_id=ledger_id,
            )
            old_ledger_adjustment = float(adjustment_breakdown["ledger_adjustment"])
            old_realized_pnl_adjustment = float(adjustment_breakdown["realized_pnl_adjustment"])
            old_total_adjustment = float(adjustment_breakdown["total_adjustment"])

            if qty > old_qty + 1e-6:
                logger.warning("Oversell: %s", code)
                if return_detail:
                    return {"ok": False, "code": "OVERSELL", "error": "Sell quantity exceeds holding"}
                return False

            before_asset = {
                "code": code,
                "name": name,
                "qty": old_qty,
                "price": old_price,
                "curr": curr,
                "adjustment": old_adj,
                "adjustment_total": old_total_adjustment,
                "legacy_adjustment": old_adj,
                "ledger_adjustment": old_ledger_adjustment,
                "cash_event_adjustment": old_ledger_adjustment,
                "realized_pnl_adjustment": old_realized_pnl_adjustment,
                "asset_type": asset_type,
            }

            pnl = (price - old_price) * qty
            new_qty = old_qty - qty
            if new_qty < 0.001:
                if user_id:
                    cursor.execute(
                        f"""
                        UPDATE portfolio
                        SET qty = 0, updated_at = datetime('now','localtime')
                        WHERE code = ? AND user_id = ?{ledger_condition}
                        """,
                        (code, user_id) + ledger_param,
                    )
                else:
                    cursor.execute(
                        f"""
                        UPDATE portfolio
                        SET qty = 0, updated_at = datetime('now','localtime')
                        WHERE code = ? AND (user_id IS NULL OR user_id = ''){ledger_condition}
                        """,
                        (code,) + ledger_param,
                    )
                after_asset = None
            else:
                if user_id:
                    cursor.execute(
                        f"""
                        UPDATE portfolio SET qty = ?, updated_at = datetime('now','localtime')
                        WHERE code = ? AND user_id = ?{ledger_condition}
                        """,
                        (new_qty, code, user_id) + ledger_param,
                    )
                else:
                    cursor.execute(
                        f"""
                        UPDATE portfolio SET qty = ?, updated_at = datetime('now','localtime')
                        WHERE code = ? AND (user_id IS NULL OR user_id = ''){ledger_condition}
                        """,
                        (new_qty, code) + ledger_param,
                    )
                after_asset = {
                    "code": code,
                    "name": name,
                    "qty": float(new_qty),
                    "price": old_price,
                    "curr": curr,
                    "adjustment": old_adj,
                    "adjustment_total": old_total_adjustment + pnl,
                    "legacy_adjustment": old_adj,
                    "ledger_adjustment": old_ledger_adjustment,
                    "cash_event_adjustment": old_ledger_adjustment,
                    "realized_pnl_adjustment": old_realized_pnl_adjustment + pnl,
                    "asset_type": asset_type,
                }

            tx_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            tx_identity = self._build_transaction_identity(
                code=code,
                curr=curr,
                asset_type=asset_type,
                tx_time=tx_time,
            )
            cursor.execute(
                """
                INSERT INTO transactions (
                    time, code, name, type, price, qty, amount, pnl, curr, market, effective_date, user_id, ledger_id
                )
                VALUES (?, ?, ?, '减仓', ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tx_time,
                    tx_identity["code"],
                    name,
                    price,
                    qty,
                    price * qty,
                    pnl,
                    tx_identity["curr"],
                    tx_identity["market"],
                    tx_identity["effective_date"],
                    user_id,
                    ledger_id or 0,
                ),
            )
            tx_id = int(cursor.lastrowid or 0)

            conn.commit()
            logger.info("Sell: %s, qty=%s, price=%s, pnl=%s", code, qty, price, pnl)
            if return_detail:
                return {
                    "ok": True,
                    "tx_id": tx_id,
                    "before_asset": before_asset,
                    "after_asset": after_asset,
                }
            return True
        except Exception as exc:
            logger.error("Failed to sell asset: %s", exc)
            conn.rollback()
            if return_detail:
                return {"ok": False, "code": "ASSET_SELL_FAILED", "error": "Failed to sell asset"}
            return False
        finally:
            conn.close()

    def sell_asset_to_cash(
        self,
        code: str,
        price: float,
        qty: float,
        cash_asset_id: int,
        cash_add_amount: float,
        user_id: str = None,
        return_detail: bool = False,
        ledger_id: int | None = None,
    ) -> Dict[str, Any]:
        """减仓并回款到现金账户。"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            if qty <= 0 or price <= 0:
                return {"ok": False, "code": "INVALID_VALUE", "error": "Invalid value"}
            if cash_add_amount <= 0:
                return {"ok": False, "code": "INVALID_CASH_AMOUNT", "error": "Invalid cash amount"}

            if user_id:
                cursor.execute(
                    """
                    SELECT id, name, amount, curr
                    FROM cash_assets
                    WHERE id = ? AND user_id = ?
                    """,
                    (cash_asset_id, user_id),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, name, amount, curr
                    FROM cash_assets
                    WHERE id = ? AND (user_id IS NULL OR user_id = '')
                    """,
                    (cash_asset_id,),
                )
            cash_row = cursor.fetchone()
            if not cash_row:
                return {"ok": False, "code": "CASH_ASSET_NOT_FOUND", "error": "Cash account not found"}

            sell_detail = self.sell_asset(code, price, qty, user_id=user_id, return_detail=True, ledger_id=ledger_id)
            if not sell_detail or not sell_detail.get("ok"):
                return sell_detail or {"ok": False, "code": "ASSET_SELL_FAILED", "error": "Failed to sell asset"}

            cash_before = float(cash_row["amount"])
            cash_after = cash_before + float(cash_add_amount)
            if user_id:
                cursor.execute(
                    """
                    UPDATE cash_assets
                    SET amount = ?, updated_at = datetime('now','localtime')
                    WHERE id = ? AND user_id = ?
                    """,
                    (cash_after, cash_asset_id, user_id),
                )
            else:
                cursor.execute(
                    """
                    UPDATE cash_assets
                    SET amount = ?, updated_at = datetime('now','localtime')
                    WHERE id = ? AND (user_id IS NULL OR user_id = '')
                    """,
                    (cash_after, cash_asset_id),
                )
            if cursor.rowcount <= 0:
                conn.rollback()
                return {"ok": False, "code": "CASH_ASSET_UPDATE_FAILED", "error": "Failed to update cash asset"}

            conn.commit()
            return {
                "ok": True,
                "tx_id": sell_detail.get("tx_id"),
                "before_asset": sell_detail.get("before_asset"),
                "after_asset": sell_detail.get("after_asset"),
                "cash_asset_id": int(cash_asset_id),
                "cash_curr": cash_row["curr"],
                "cash_before_amount": cash_before,
                "cash_after_amount": cash_after,
                "cash_add_amount": float(cash_add_amount),
            }
        except Exception as exc:
            logger.error(
                "Failed to sell asset to cash: code=%s user_id=%s cash_asset_id=%s err=%s",
                code,
                user_id,
                cash_asset_id,
                exc,
            )
            conn.rollback()
            return {"ok": False, "code": "ASSET_SELL_TO_CASH_FAILED", "error": "Failed to sell asset to cash"}
        finally:
            conn.close()

    def buy_asset_with_cash(
        self,
        code: str,
        name: str,
        price: float,
        qty: float,
        curr: str,
        asset_type: str,
        cash_asset_id: int,
        cash_deduct_amount: float,
        user_id: str = None,
        legacy_codes: Optional[List[str]] = None,
        ledger_id: int | None = None,
    ) -> Dict[str, Any]:
        """使用现金账户买入。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        ledger_condition = " AND ledger_id = ?" if ledger_id is not None else ""
        ledger_param = (ledger_id,) if ledger_id is not None else ()

        try:
            if qty <= 0 or price <= 0:
                return {"ok": False, "code": "INVALID_VALUE", "error": "Invalid value"}
            if cash_deduct_amount <= 0:
                return {"ok": False, "code": "INVALID_CASH_AMOUNT", "error": "Invalid cash deduction amount"}

            if user_id:
                cursor.execute(
                    """
                    SELECT id, name, amount, curr
                    FROM cash_assets
                    WHERE id = ? AND user_id = ?
                    """,
                    (cash_asset_id, user_id),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, name, amount, curr
                    FROM cash_assets
                    WHERE id = ? AND (user_id IS NULL OR user_id = '')
                    """,
                    (cash_asset_id,),
                )
            cash_row = cursor.fetchone()
            if not cash_row:
                return {"ok": False, "code": "CASH_ASSET_NOT_FOUND", "error": "Cash account not found"}

            cash_before = float(cash_row["amount"])
            if cash_before + 1e-9 < cash_deduct_amount:
                return {
                    "ok": False,
                    "code": "INSUFFICIENT_CASH",
                    "error": "Insufficient cash balance",
                    "available": cash_before,
                    "required": float(cash_deduct_amount),
                    "cash_curr": cash_row["curr"],
                }
            cash_after = cash_before - cash_deduct_amount

            if user_id:
                cursor.execute(
                    """
                    UPDATE cash_assets
                    SET amount = ?, updated_at = datetime('now','localtime')
                    WHERE id = ? AND user_id = ?
                    """,
                    (cash_after, cash_asset_id, user_id),
                )
            else:
                cursor.execute(
                    """
                    UPDATE cash_assets
                    SET amount = ?, updated_at = datetime('now','localtime')
                    WHERE id = ? AND (user_id IS NULL OR user_id = '')
                    """,
                    (cash_after, cash_asset_id),
                )
            if cursor.rowcount <= 0:
                return {"ok": False, "code": "CASH_ASSET_UPDATE_FAILED", "error": "Failed to update cash asset"}

            target_code, row = self._resolve_existing_portfolio_code(
                cursor,
                code,
                user_id,
                legacy_codes=legacy_codes,
                ledger_id=ledger_id,
            )

            before_asset = None
            if row:
                old_name = row["name"]
                old_qty = float(row["qty"])
                old_price = float(row["price"])
                old_adjustment = float(row["adjustment"])
                old_curr = row["curr"]
                old_asset_type = row["asset_type"] if "asset_type" in row.keys() else "a"
                before_asset = {
                    "code": target_code,
                    "name": old_name,
                    "qty": old_qty,
                    "price": old_price,
                    "curr": old_curr,
                    "adjustment": old_adjustment,
                    "asset_type": old_asset_type,
                }

                new_qty = old_qty + qty
                new_price = (old_qty * old_price + qty * price) / new_qty if new_qty > 0 else 0
                if user_id:
                    cursor.execute(
                        f"""
                        UPDATE portfolio SET qty = ?, price = ?, updated_at = datetime('now','localtime')
                        WHERE code = ? AND user_id = ?{ledger_condition}
                        """,
                        (new_qty, new_price, target_code, user_id) + ledger_param,
                    )
                else:
                    cursor.execute(
                        f"""
                        UPDATE portfolio SET qty = ?, price = ?, updated_at = datetime('now','localtime')
                        WHERE code = ? AND (user_id IS NULL OR user_id = ''){ledger_condition}
                        """,
                        (new_qty, new_price, target_code) + ledger_param,
                    )
                after_asset = {
                    "code": target_code,
                    "name": old_name,
                    "qty": float(new_qty),
                    "price": float(new_price),
                    "curr": old_curr,
                    "adjustment": old_adjustment,
                    "asset_type": old_asset_type,
                }
                tx_name = old_name
            else:
                tx_name = (name or code).strip() or code
                next_asset_type = (asset_type or "a").strip() or "a"
                next_curr = (curr or "CNY").strip() or "CNY"
                target_code = str(code or "").strip()
                if user_id:
                    cursor.execute(
                        """
                        INSERT INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, user_id, ledger_id, updated_at)
                        VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, datetime('now','localtime'))
                        """,
                        (target_code, tx_name, qty, price, next_curr, next_asset_type, user_id, ledger_id or 0),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, ledger_id, updated_at)
                        VALUES (?, ?, ?, ?, ?, 0, ?, ?, datetime('now','localtime'))
                        """,
                        (target_code, tx_name, qty, price, next_curr, next_asset_type, ledger_id or 0),
                    )
                after_asset = {
                    "code": target_code,
                    "name": tx_name,
                    "qty": float(qty),
                    "price": float(price),
                    "curr": next_curr,
                    "adjustment": 0.0,
                    "asset_type": next_asset_type,
                }

            tx_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            tx_identity = self._build_transaction_identity(
                code=target_code,
                curr=after_asset.get("curr") if after_asset else "",
                asset_type=after_asset.get("asset_type") if after_asset else "",
                tx_time=tx_time,
            )
            cursor.execute(
                """
                INSERT INTO transactions (
                    time, code, name, type, price, qty, amount, pnl, curr, market, effective_date, user_id, ledger_id
                )
                VALUES (?, ?, ?, '加仓', ?, ?, ?, 0, ?, ?, ?, ?, ?)
                """,
                (
                    tx_time,
                    tx_identity["code"],
                    tx_name,
                    price,
                    qty,
                    price * qty,
                    tx_identity["curr"],
                    tx_identity["market"],
                    tx_identity["effective_date"],
                    user_id,
                    ledger_id or 0,
                ),
            )
            tx_id = int(cursor.lastrowid or 0)

            conn.commit()
            return {
                "ok": True,
                "tx_id": tx_id,
                "before_asset": before_asset,
                "after_asset": after_asset,
                "cash_asset_id": int(cash_asset_id),
                "cash_curr": cash_row["curr"],
                "cash_before_amount": cash_before,
                "cash_after_amount": cash_after,
                "cash_deduct_amount": float(cash_deduct_amount),
            }
        except Exception as exc:
            logger.error(
                "Failed to buy asset with cash: code=%s user_id=%s cash_asset_id=%s err=%s",
                code,
                user_id or "",
                cash_asset_id,
                exc,
            )
            conn.rollback()
            return {"ok": False, "code": "ASSET_BUY_WITH_CASH_FAILED", "error": "Failed to buy asset with cash"}
        finally:
            conn.close()

    def undo_invest_operation(self, operation: Dict[str, Any], user_id: str = None) -> Dict[str, Any]:
        """撤销投资写操作。"""
        if not isinstance(operation, dict):
            return {"ok": False, "code": "INVALID_OPERATION", "error": "Invalid undo operation"}

        code = str(operation.get("code") or "").strip()
        if not code:
            return {"ok": False, "code": "INVALID_OPERATION", "error": "Missing code in undo operation"}

        before_asset = operation.get("before_asset")
        tx_id = operation.get("tx_id")
        ledger_event_id = operation.get("ledger_event_id")
        correction_log_id = operation.get("correction_log_id")
        cash_asset_id = operation.get("cash_asset_id")
        cash_before_amount = operation.get("cash_before_amount")
        raw_ledger_id = operation.get("ledger_id")
        try:
            ledger_id = int(raw_ledger_id) if raw_ledger_id is not None else None
        except (TypeError, ValueError):
            ledger_id = None
        ledger_condition = " AND ledger_id = ?" if ledger_id is not None else ""
        ledger_param = (ledger_id,) if ledger_id is not None else ()

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if before_asset is None:
                if user_id:
                    cursor.execute(
                        f"DELETE FROM portfolio WHERE code = ? AND user_id = ?{ledger_condition}",
                        (code, user_id) + ledger_param,
                    )
                else:
                    cursor.execute(
                        f"DELETE FROM portfolio WHERE code = ? AND (user_id IS NULL OR user_id = ''){ledger_condition}",
                        (code,) + ledger_param,
                    )
            else:
                name = str(before_asset.get("name") or code)
                qty = float(before_asset.get("qty") or 0.0)
                price = float(before_asset.get("price") or 0.0)
                curr = str(before_asset.get("curr") or "CNY")
                adjustment = float(before_asset.get("adjustment") or 0.0)
                asset_type = str(before_asset.get("asset_type") or "a")

                if user_id:
                    cursor.execute(
                        f"SELECT id FROM portfolio WHERE code = ? AND user_id = ?{ledger_condition}",
                        (code, user_id) + ledger_param,
                    )
                else:
                    cursor.execute(
                        f"SELECT id FROM portfolio WHERE code = ? AND (user_id IS NULL OR user_id = ''){ledger_condition}",
                        (code,) + ledger_param,
                    )
                existing = cursor.fetchone()
                if existing:
                    if user_id:
                        cursor.execute(
                            f"""
                            UPDATE portfolio
                            SET name = ?, qty = ?, price = ?, curr = ?, adjustment = ?, asset_type = ?, updated_at = datetime('now','localtime')
                            WHERE code = ? AND user_id = ?{ledger_condition}
                            """,
                            (name, qty, price, curr, adjustment, asset_type, code, user_id)
                            + ledger_param,
                        )
                    else:
                        cursor.execute(
                            f"""
                            UPDATE portfolio
                            SET name = ?, qty = ?, price = ?, curr = ?, adjustment = ?, asset_type = ?, updated_at = datetime('now','localtime')
                            WHERE code = ? AND (user_id IS NULL OR user_id = ''){ledger_condition}
                            """,
                            (name, qty, price, curr, adjustment, asset_type, code)
                            + ledger_param,
                        )
                else:
                    if user_id:
                        cursor.execute(
                            """
                            INSERT INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, user_id, ledger_id, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
                            """,
                            (code, name, qty, price, curr, adjustment, asset_type, user_id, ledger_id or 0),
                        )
                    else:
                        cursor.execute(
                            """
                            INSERT INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, ledger_id, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
                            """,
                            (code, name, qty, price, curr, adjustment, asset_type, ledger_id or 0),
                        )

            if tx_id is not None:
                try:
                    tx_id_int = int(tx_id)
                except (TypeError, ValueError):
                    tx_id_int = 0
                if tx_id_int > 0:
                    if user_id:
                        cursor.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (tx_id_int, user_id))
                    else:
                        cursor.execute(
                            "DELETE FROM transactions WHERE id = ? AND (user_id IS NULL OR user_id = '')",
                            (tx_id_int,),
                        )

            if ledger_event_id is not None:
                try:
                    ledger_event_id_int = int(ledger_event_id)
                except (TypeError, ValueError):
                    ledger_event_id_int = 0
                if ledger_event_id_int > 0:
                    if user_id:
                        cursor.execute(
                            "DELETE FROM portfolio_adjustment_ledger WHERE id = ? AND user_id = ?",
                            (ledger_event_id_int, user_id),
                        )
                    else:
                        cursor.execute(
                            "DELETE FROM portfolio_adjustment_ledger WHERE id = ? AND (user_id IS NULL OR user_id = '')",
                            (ledger_event_id_int,),
                        )

            if correction_log_id is not None:
                try:
                    correction_log_id_int = int(correction_log_id)
                except (TypeError, ValueError):
                    correction_log_id_int = 0
                if correction_log_id_int > 0:
                    if user_id:
                        cursor.execute(
                            "DELETE FROM portfolio_correction_logs WHERE id = ? AND user_id = ?",
                            (correction_log_id_int, user_id),
                        )
                    else:
                        cursor.execute(
                            "DELETE FROM portfolio_correction_logs WHERE id = ? AND (user_id IS NULL OR user_id = '')",
                            (correction_log_id_int,),
                        )

            if cash_asset_id is not None and cash_before_amount is not None:
                try:
                    cash_asset_id_int = int(cash_asset_id)
                    cash_before = float(cash_before_amount)
                except (TypeError, ValueError):
                    return {"ok": False, "code": "INVALID_CASH_RESTORE", "error": "Invalid cash restore payload"}
                if user_id:
                    cursor.execute(
                        """
                        UPDATE cash_assets
                        SET amount = ?, updated_at = datetime('now','localtime')
                        WHERE id = ? AND user_id = ?
                        """,
                        (cash_before, cash_asset_id_int, user_id),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE cash_assets
                        SET amount = ?, updated_at = datetime('now','localtime')
                        WHERE id = ? AND (user_id IS NULL OR user_id = '')
                        """,
                        (cash_before, cash_asset_id_int),
                    )
                if cursor.rowcount <= 0:
                    return {"ok": False, "code": "CASH_ASSET_NOT_FOUND", "error": "Cash account not found"}

            conn.commit()
            return {"ok": True}
        except Exception as exc:
            logger.error("Failed to undo invest operation: %s", exc)
            conn.rollback()
            return {"ok": False, "code": "UNDO_FAILED", "error": "Failed to undo operation"}
        finally:
            conn.close()

    def backup_from_csv(self, csv_path: str) -> bool:
        """从 CSV 备份数据导入数据库。"""
        try:
            import pandas as pd

            df = pd.read_csv(csv_path)
            conn = self.get_connection()
            cursor = conn.cursor()

            for _, row in df.iterrows():
                code = row["code"]
                name = row["name"]
                qty = row["qty"]
                price = row["price"]
                curr = row.get("curr", "CNY")
                adjustment = row.get("adjustment", 0.0)
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO portfolio (code, name, qty, price, curr, adjustment)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (code, name, qty, price, curr, adjustment),
                )

            conn.commit()
            conn.close()
            logger.info("Backup imported from CSV: %s", csv_path)
            return True
        except Exception as exc:
            logger.error("Failed to backup from CSV: %s", exc)
            return False

    def get_today_realized_pnl(self, user_id: str = None) -> float:
        """获取今日已实现盈亏。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")

        user_condition = "AND user_id = ?" if user_id else "AND (user_id IS NULL OR user_id = '')"
        user_param = (user_id,) if user_id else ()

        try:
            cursor.execute(
                """
                SELECT SUM(pnl)
                FROM transactions
                WHERE type = '减仓' AND time LIKE ?
                """
                + f" {user_condition}",
                (f"{today}%",) + user_param,
            )
            result = cursor.fetchone()[0]
            return float(result) if result else 0.0
        except Exception as exc:
            logger.error("Failed to get realized pnl: %s", exc)
            return 0.0
        finally:
            conn.close()

    def get_today_buy_transactions(
        self,
        date_str: str,
        user_id: str = None,
        ledger_id: int | None = None,
    ) -> Dict[str, Dict[str, float]]:
        """返回指定日期的加仓记录，按 code 聚合 qty 和 amount。

        Returns: {code: {"qty": float, "amount": float}}
        """
        return self.get_buy_transactions_by_effective_date(date_str, user_id=user_id, ledger_id=ledger_id)

    def get_buy_transactions_grouped_by_effective_date(
        self,
        user_id: str = None,
        ledger_id: int | None = None,
    ) -> Dict[str, Dict[str, Dict[str, float]]]:
        """按市场本地日期聚合加仓记录。

        Returns:
            {
                "2026-03-20": {
                    "AAPL": {"qty": 1.0, "amount": 100.0}
                }
            }
        """
        result: Dict[str, Dict[str, Dict[str, float]]] = {}
        conn = self.get_connection()
        cursor = conn.cursor()
        user_condition = "user_id = ?" if user_id else "(user_id IS NULL OR user_id = '')"
        user_param = (user_id,) if user_id else ()
        ledger_condition = " AND ledger_id = ?" if ledger_id is not None else ""
        ledger_param = (ledger_id,) if ledger_id is not None else ()
        try:
            cursor.execute(
                """
                SELECT time, code, qty, amount, curr, market, effective_date
                FROM transactions
                WHERE type = '加仓' AND
                """
                + f" {user_condition}{ledger_condition}",
                user_param + ledger_param,
            )
            for row in cursor.fetchall():
                identity = self._resolve_transaction_row_identity(row)
                code = identity["code"]
                effective_date = identity["effective_date"]
                if not effective_date:
                    continue
                by_code = result.setdefault(effective_date, {})
                bucket = by_code.setdefault(code, {"qty": 0.0, "amount": 0.0})
                bucket["qty"] += float(row["qty"] or 0.0)
                bucket["amount"] += float(row["amount"] or 0.0)
            return result
        except Exception as exc:
            logger.error("Failed to get buy transactions grouped by effective date: %s", exc)
            return result
        finally:
            conn.close()

    def get_sell_transactions_grouped_by_effective_date(
        self,
        user_id: str = None,
        ledger_id: int | None = None,
    ) -> Dict[str, Dict[str, Dict[str, float]]]:
        """按市场本地日期聚合减仓记录。"""
        result: Dict[str, Dict[str, Dict[str, float]]] = {}
        conn = self.get_connection()
        cursor = conn.cursor()
        user_condition = "user_id = ?" if user_id else "(user_id IS NULL OR user_id = '')"
        user_param = (user_id,) if user_id else ()
        ledger_condition = " AND ledger_id = ?" if ledger_id is not None else ""
        ledger_param = (ledger_id,) if ledger_id is not None else ()
        try:
            cursor.execute(
                """
                SELECT time, code, qty, amount, curr, market, effective_date
                FROM transactions
                WHERE type = '减仓' AND
                """
                + f" {user_condition}{ledger_condition}",
                user_param + ledger_param,
            )
            for row in cursor.fetchall():
                identity = self._resolve_transaction_row_identity(row)
                code = identity["code"]
                effective_date = identity["effective_date"]
                if not effective_date:
                    continue
                by_code = result.setdefault(effective_date, {})
                bucket = by_code.setdefault(code, {"qty": 0.0, "amount": 0.0})
                bucket["qty"] += float(row["qty"] or 0.0)
                bucket["amount"] += float(row["amount"] or 0.0)
            return result
        except Exception as exc:
            logger.error("Failed to get sell transactions grouped by effective date: %s", exc)
            return result
        finally:
            conn.close()

    def get_buy_transactions_by_effective_date(
        self,
        date_str: str,
        user_id: str = None,
        ledger_id: int | None = None,
    ) -> Dict[str, Dict[str, float]]:
        grouped = self.get_buy_transactions_grouped_by_effective_date(user_id=user_id, ledger_id=ledger_id)
        return grouped.get(str(date_str or "").strip(), {})

    def get_portfolio_transactions(self, code: str, user_id: str = None, ledger_id: int | None = None) -> list:
        """获取指定 code 的全部交易记录、收益事件和修正审计，按时间倒序返回。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        user_condition = "AND user_id = ?" if user_id else "AND (user_id IS NULL OR user_id = '')"
        user_param = (user_id,) if user_id else ()
        ledger_condition = " AND ledger_id = ?" if ledger_id is not None else ""
        ledger_param = (ledger_id,) if ledger_id is not None else ()
        event_type_labels = {
            "dividend": "分红",
            "fee": "手续费",
            "tax": "税金",
        }
        correction_type_labels = {
            "opening_balance": "初始持仓",
            "cost_price": "成本修正",
            "quantity": "数量修正",
            "holding": "持仓修正",
        }
        try:
            # 交易记录
            cursor.execute(
                """
                SELECT id, type, price, qty, amount, pnl, time
                FROM transactions
                WHERE code = ?
                """
                + f" {user_condition}{ledger_condition}"
                + " ORDER BY time DESC, id DESC",
                (code,) + user_param + ledger_param,
            )
            records = []
            for row in cursor.fetchall():
                records.append({
                    "_sort_id": int(row["id"] or 0),
                    "type": row["type"],
                    "price": float(row["price"] or 0),
                    "qty": float(row["qty"] or 0),
                    "amount": float(row["amount"] or 0),
                    "pnl": float(row["pnl"] or 0),
                    "time": str(row["time"] or ""),
                })

            # 调整台账
            cursor.execute(
                """
                SELECT id, event_type, amount, note, created_at
                FROM portfolio_adjustment_ledger
                WHERE code = ? AND event_type IN ('dividend', 'fee', 'tax')
                """
                + f" {user_condition}{ledger_condition}"
                + " ORDER BY created_at DESC, id DESC",
                (code,) + user_param + ledger_param,
            )
            for row in cursor.fetchall():
                raw_type = str(row["event_type"] or "")
                records.append({
                    "_sort_id": int(row["id"] or 0),
                    "type": event_type_labels.get(raw_type, raw_type),
                    "amount": float(row["amount"] or 0),
                    "note": str(row["note"] or ""),
                    "time": str(row["created_at"] or ""),
                })

            cursor.execute(
                """
                SELECT id, correction_type, before_qty, after_qty, before_price, after_price, note, created_at
                FROM portfolio_correction_logs
                WHERE code = ?
                """
                + f" {user_condition}{ledger_condition}"
                + " ORDER BY created_at DESC, id DESC",
                (code,) + user_param + ledger_param,
            )
            for row in cursor.fetchall():
                raw_type = str(row["correction_type"] or "")
                records.append({
                    "_sort_id": int(row["id"] or 0),
                    "type": correction_type_labels.get(raw_type, "持仓修正"),
                    "note": str(row["note"] or ""),
                    "before_qty": row["before_qty"],
                    "after_qty": row["after_qty"],
                    "before_price": row["before_price"],
                    "after_price": row["after_price"],
                    "time": str(row["created_at"] or ""),
                })

            records.sort(
                key=lambda r: (
                    str(r.get("time", "")),
                    int(r.get("_sort_id") or 0),
                ),
                reverse=True,
            )
            for row in records:
                row.pop("_sort_id", None)
            return records
        except Exception as exc:
            logger.error("Failed to get portfolio transactions code=%s: %s", code, exc)
            return []
        finally:
            conn.close()

    def get_realized_pnl_by_date(
        self,
        date_str: str,
        user_id: str = None,
        ledger_id: int | None = None,
    ) -> Dict[str, float]:
        """获取指定日期按市场聚合的已实现盈亏。"""
        grouped = self.get_realized_pnl_grouped_by_effective_date(user_id=user_id, ledger_id=ledger_id)
        normalized = str(date_str or "").strip()
        return grouped.get(normalized, {k: 0.0 for k in DEFAULT_MARKETS})

    def get_realized_pnl_grouped_by_effective_date(
        self,
        user_id: str = None,
        ledger_id: int | None = None,
    ) -> Dict[str, Dict[str, float]]:
        """按市场本地日期聚合已实现盈亏。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        grouped: Dict[str, Dict[str, float]] = {}
        user_condition = "AND user_id = ?" if user_id else "AND (user_id IS NULL OR user_id = '')"
        user_param = (user_id,) if user_id else ()
        ledger_condition = " AND ledger_id = ?" if ledger_id is not None else ""
        ledger_param = (ledger_id,) if ledger_id is not None else ()

        try:
            cursor.execute(
                """
                SELECT time, code, pnl, curr, market, effective_date
                FROM transactions
                WHERE type = '减仓'
                """
                + f" {user_condition}{ledger_condition}",
                user_param + ledger_param,
            )
            for row in cursor.fetchall():
                identity = self._resolve_transaction_row_identity(row)
                market = identity["market"]
                effective_date = identity["effective_date"]
                if not effective_date:
                    continue
                bucket = grouped.setdefault(effective_date, {k: 0.0 for k in DEFAULT_MARKETS})
                bucket[market] += float(row["pnl"] or 0.0)
            return grouped
        except Exception as exc:
            logger.error("Failed to get realized pnl grouped by effective date: %s", exc)
            return grouped
        finally:
            conn.close()

    def get_position_qty_as_of_effective_date(
        self,
        code: str,
        effective_date: str,
        user_id: str = None,
        ledger_id: int | None = None,
    ) -> float:
        """反推出某只资产在 effective_date 当日收盘后的持仓数量。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        user_condition = "AND user_id = ?" if user_id else "AND (user_id IS NULL OR user_id = '')"
        user_param = (user_id,) if user_id else ()
        ledger_condition = " AND ledger_id = ?" if ledger_id is not None else ""
        ledger_param = (ledger_id,) if ledger_id is not None else ()

        try:
            current_row = self._fetch_portfolio_row_by_code(cursor, code, user_id, ledger_id=ledger_id)
            qty = float(current_row["qty"] or 0.0) if current_row else 0.0
            cursor.execute(
                """
                SELECT time, type, qty, curr, market, effective_date
                FROM transactions
                WHERE code = ?
                """
                + f" {user_condition}"
                + ledger_condition
                + " ORDER BY time DESC, id DESC",
                (code,) + user_param + ledger_param,
            )
            for row in cursor.fetchall():
                tx_effective_date = self._resolve_transaction_row_identity(row, fallback_code=code)["effective_date"]
                if not tx_effective_date or tx_effective_date <= effective_date:
                    continue
                tx_qty = float(row["qty"] or 0.0)
                tx_type = str(row["type"] or "").strip()
                if tx_type == "加仓":
                    qty -= tx_qty
                elif tx_type == "减仓":
                    qty += tx_qty

            cursor.execute(
                """
                SELECT before_qty, after_qty
                FROM portfolio_correction_logs
                WHERE code = ?
                  AND correction_type IN ('opening_balance', 'quantity', 'holding')
                  AND created_at > ?
                """
                + f" {user_condition}"
                + ledger_condition
                + " ORDER BY created_at DESC, id DESC",
                (code, f"{effective_date} 23:59:59") + user_param + ledger_param,
            )
            for row in cursor.fetchall():
                before_qty = row["before_qty"]
                after_qty = row["after_qty"]
                if before_qty is None or after_qty is None:
                    continue
                qty = float(before_qty)

            return max(0.0, qty)
        except Exception as exc:
            logger.error(
                "Failed to reconstruct position qty code=%s effective_date=%s: %s",
                code,
                effective_date,
                exc,
            )
            return 0.0
        finally:
            conn.close()
