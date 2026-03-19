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
    from .market_calendar import market_from_asset
    from .parser import parse_code
    from .logo_utils import suggest_logo_url
except ImportError:  # 兼容被单文件动态加载的测试场景
    from core.market_calendar import market_from_asset
    from core.parser import parse_code
    from core.logo_utils import suggest_logo_url

logger = logging.getLogger(__name__)
DEFAULT_MARKETS = ("a", "hk", "us", "fund")


class PortfolioDatabaseMixin:
    """给 DatabaseManager 提供持仓、交易与组合兼容迁移相关方法。"""

    def _fetch_portfolio_row_by_code(self, cursor, code: str, user_id: str = None):
        if user_id:
            cursor.execute(
                """
                SELECT name, qty, price, curr, adjustment, asset_type
                FROM portfolio
                WHERE code = ? AND user_id = ?
                """,
                (code, user_id),
            )
        else:
            cursor.execute(
                """
                SELECT name, qty, price, curr, adjustment, asset_type
                FROM portfolio
                WHERE code = ? AND (user_id IS NULL OR user_id = '')
                """,
                (code,),
            )
        return cursor.fetchone()

    def _resolve_existing_portfolio_code(
        self,
        cursor,
        code: str,
        user_id: str = None,
        legacy_codes: Optional[List[str]] = None,
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
            row = self._fetch_portfolio_row_by_code(cursor, candidate, user_id)
            if row:
                return candidate, row
        return str(code or "").strip(), None

    def _ensure_portfolio_user_scoped_unique(self, cursor) -> None:
        """将 portfolio 的全局 code 唯一约束迁移为 (code, user_id) 唯一约束。"""
        cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='portfolio'"
        )
        row = cursor.fetchone()
        raw_sql = row["sql"] if isinstance(row, dict) or hasattr(row, "keys") else (row[0] if row else "")
        table_sql = str(raw_sql or "").lower()
        has_legacy_unique = "code text unique" in table_sql or "code\ttext unique" in table_sql

        if has_legacy_unique:
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
            if cols == ["code"]:
                cursor.execute(f'DROP INDEX IF EXISTS "{safe_name}"')

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

    def get_portfolio(
        self,
        asset_type: str = "all",
        user_id: str = None,
        include_closed: bool = False,
    ) -> List[Dict[str, Any]]:
        """获取持仓数据，支持按类型筛选。"""
        conn = self.get_connection()
        cursor = conn.cursor()

        logger.info("get_portfolio called with asset_type: %s, user_id: %s", asset_type, user_id)

        user_condition = "user_id = ?" if user_id else "(user_id IS NULL OR user_id = '')"
        user_param = (user_id,) if user_id else ()
        qty_condition = "" if include_closed else " AND qty > 0"

        if asset_type == "all":
            cursor.execute(
                f"""
                SELECT code, name, qty, price, curr, adjustment, asset_type, logo_url
                FROM portfolio
                WHERE {user_condition}{qty_condition}
                ORDER BY code
                """,
                user_param,
            )
        elif asset_type in ("a", "us", "hk", "fund"):
            cursor.execute(
                f"""
                SELECT code, name, qty, price, curr, adjustment, asset_type, logo_url
                FROM portfolio
                WHERE {user_condition}{qty_condition} AND asset_type = ?
                ORDER BY code
                """,
                user_param + (asset_type,),
            )
        else:
            cursor.execute(
                f"""
                SELECT code, name, qty, price, curr, adjustment, asset_type, logo_url
                FROM portfolio
                WHERE {user_condition}{qty_condition}
                ORDER BY code
                """,
                user_param,
            )

        data = []
        from .asset_type import infer_category_type

        for row in cursor.fetchall():
            code = row["code"]
            name = row["name"]
            asset_type_value = row["asset_type"] if "asset_type" in row.keys() else ""
            data.append(
                {
                    "code": code,
                    "name": name,
                    "qty": float(row["qty"]),
                    "price": float(row["price"]),
                    "curr": row["curr"],
                    "adjustment": float(row["adjustment"]),
                    "asset_type": asset_type_value,
                    "category_type": infer_category_type(code, name, asset_type_value),
                    "logo_url": row["logo_url"] if "logo_url" in row.keys() else None,
                }
            )

        logger.info("get_portfolio returned %s records for type %s", len(data), asset_type)
        conn.close()
        return data

    def get_distinct_portfolio_codes(self, include_closed: bool = False) -> List[str]:
        """获取全库唯一证券代码列表（用于行情预取）。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        qty_condition = "" if include_closed else " AND qty > 0"
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

    def get_asset(self, code: str, user_id: str = None) -> Optional[Dict[str, Any]]:
        """获取单个资产信息。"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if user_id:
            cursor.execute(
                """
                SELECT code, name, qty, price, curr, adjustment, asset_type
                FROM portfolio
                WHERE code = ? AND user_id = ?
                """,
                (code, user_id),
            )
        else:
            cursor.execute(
                """
                SELECT code, name, qty, price, curr, adjustment, asset_type
                FROM portfolio
                WHERE code = ? AND (user_id IS NULL OR user_id = '')
                """,
                (code,),
            )

        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "code": row["code"],
                "name": row["name"],
                "qty": float(row["qty"]),
                "price": float(row["price"]),
                "curr": row["curr"],
                "adjustment": float(row["adjustment"]),
                "asset_type": row["asset_type"] if "asset_type" in row.keys() else "",
            }
        return None

    def add_asset(self, data: Dict[str, Any], user_id: str = None) -> bool:
        """添加或更新资产。"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            incoming_name = str(data.get("name") or "").strip()
            if not data.get("logo_url"):
                data["logo_url"] = suggest_logo_url(data.get("code"), incoming_name)

            if user_id:
                cursor.execute(
                    "SELECT id, name FROM portfolio WHERE code = ? AND user_id = ?",
                    (data["code"], user_id),
                )
            else:
                cursor.execute(
                    "SELECT id, name FROM portfolio WHERE code = ? AND (user_id IS NULL OR user_id = '')",
                    (data["code"],),
                )
            existing = cursor.fetchone()

            if existing:
                existing_name = str(existing["name"] or "").strip()
                next_name = existing_name or incoming_name or data["code"]
                if user_id:
                    cursor.execute(
                        """
                        UPDATE portfolio
                        SET name = ?, qty = ?, price = ?, curr = ?, adjustment = ?, asset_type = ?, updated_at = datetime('now','localtime')
                        WHERE code = ? AND user_id = ?
                        """,
                        (
                            next_name,
                            data["qty"],
                            data["price"],
                            data.get("curr", "CNY"),
                            data.get("adjustment", 0.0),
                            data.get("asset_type", "a"),
                            data["code"],
                            user_id,
                        ),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE portfolio
                        SET name = ?, qty = ?, price = ?, curr = ?, adjustment = ?, asset_type = ?, updated_at = datetime('now','localtime')
                        WHERE code = ? AND (user_id IS NULL OR user_id = '')
                        """,
                        (
                            next_name,
                            data["qty"],
                            data["price"],
                            data.get("curr", "CNY"),
                            data.get("adjustment", 0.0),
                            data.get("asset_type", "a"),
                            data["code"],
                        ),
                    )
            else:
                next_name = incoming_name or data["code"]
                if user_id:
                    cursor.execute(
                        """
                        INSERT INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, user_id, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
                        """,
                        (
                            data["code"],
                            next_name,
                            data["qty"],
                            data["price"],
                            data.get("curr", "CNY"),
                            data.get("adjustment", 0.0),
                            data.get("asset_type", "a"),
                            user_id,
                        ),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
                        """,
                        (
                            data["code"],
                            next_name,
                            data["qty"],
                            data["price"],
                            data.get("curr", "CNY"),
                            data.get("adjustment", 0.0),
                            data.get("asset_type", "a"),
                        ),
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

    def update_asset(self, code: str, field: str, value: float, user_id: str = None) -> bool:
        """更新资产字段。"""
        if field not in self.VALID_FIELDS:
            logger.error("Invalid field name: %s", field)
            return False

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            if user_id:
                user_condition = "AND user_id = ?"
                params_suffix = (code, user_id)
            else:
                user_condition = "AND (user_id IS NULL OR user_id = '')"
                params_suffix = (code,)

            if field == "adjustment":
                cursor.execute(
                    f"""
                    UPDATE portfolio SET adjustment = COALESCE(adjustment, 0) + ?, updated_at = datetime('now','localtime')
                    WHERE code = ? {user_condition}
                    """,
                    (value,) + params_suffix,
                )
            else:
                cursor.execute(
                    f"""
                    UPDATE portfolio SET {field} = ?, updated_at = datetime('now','localtime')
                    WHERE code = ? {user_condition}
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
        adjustment: float,
        user_id: str = None,
        return_detail: bool = False,
    ):
        """修正资产数据。"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            if user_id:
                cursor.execute(
                    """
                    SELECT name, qty, price, curr, adjustment, asset_type
                    FROM portfolio
                    WHERE code = ? AND user_id = ?
                    """,
                    (code, user_id),
                )
            else:
                cursor.execute(
                    """
                    SELECT name, qty, price, curr, adjustment, asset_type
                    FROM portfolio
                    WHERE code = ? AND (user_id IS NULL OR user_id = '')
                    """,
                    (code,),
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

            if user_id:
                cursor.execute(
                    """
                    UPDATE portfolio
                    SET qty = ?, price = ?, adjustment = ?, updated_at = datetime('now','localtime')
                    WHERE code = ? AND user_id = ?
                    """,
                    (qty, price, adjustment, code, user_id),
                )
            else:
                cursor.execute(
                    """
                    UPDATE portfolio
                    SET qty = ?, price = ?, adjustment = ?, updated_at = datetime('now','localtime')
                    WHERE code = ? AND (user_id IS NULL OR user_id = '')
                    """,
                    (qty, price, adjustment, code),
                )

            if cursor.rowcount <= 0:
                if return_detail:
                    return {"ok": False, "code": "ASSET_NOT_FOUND", "error": "Asset not found"}
                return False

            conn.commit()
            logger.info("Asset modified: %s, qty=%s, price=%s, adj=%s", code, qty, price, adjustment)
            if return_detail:
                return {
                    "ok": True,
                    "before_asset": before_asset,
                    "after_asset": {
                        "code": code,
                        "name": before_asset["name"],
                        "qty": float(qty),
                        "price": float(price),
                        "curr": before_asset["curr"],
                        "adjustment": float(adjustment),
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

    def delete_asset(self, code: str, user_id: str = None) -> bool:
        """删除资产。"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            if user_id:
                cursor.execute("DELETE FROM portfolio WHERE code = ? AND user_id = ?", (code, user_id))
            else:
                cursor.execute(
                    "DELETE FROM portfolio WHERE code = ? AND (user_id IS NULL OR user_id = '')",
                    (code,),
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

    def delete_asset_corrective(self, code: str, user_id: str = None) -> Optional[Dict[str, Any]]:
        """删除资产并清理该资产交易历史与受影响快照区间。"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            if user_id:
                cursor.execute(
                    """
                    SELECT time FROM transactions
                    WHERE code = ? AND user_id = ?
                    ORDER BY time ASC
                    LIMIT 1
                    """,
                    (code, user_id),
                )
                tx_row = cursor.fetchone()
                cursor.execute(
                    """
                    SELECT created_at, updated_at
                    FROM portfolio
                    WHERE code = ? AND user_id = ?
                    LIMIT 1
                    """,
                    (code, user_id),
                )
                pf_row = cursor.fetchone()
            else:
                cursor.execute(
                    """
                    SELECT time FROM transactions
                    WHERE code = ? AND (user_id IS NULL OR user_id = '')
                    ORDER BY time ASC
                    LIMIT 1
                    """,
                    (code,),
                )
                tx_row = cursor.fetchone()
                cursor.execute(
                    """
                    SELECT created_at, updated_at
                    FROM portfolio
                    WHERE code = ? AND (user_id IS NULL OR user_id = '')
                    LIMIT 1
                    """,
                    (code,),
                )
                pf_row = cursor.fetchone()

            from_date = datetime.now().strftime("%Y-%m-%d")
            tx_time = str(tx_row["time"]) if tx_row and tx_row["time"] else ""
            if len(tx_time) >= 10:
                from_date = tx_time[:10]
            elif pf_row:
                pf_time = str(pf_row["updated_at"] or pf_row["created_at"] or "")
                if len(pf_time) >= 10:
                    from_date = pf_time[:10]

            if user_id:
                cursor.execute("DELETE FROM portfolio WHERE code = ? AND user_id = ?", (code, user_id))
            else:
                cursor.execute(
                    "DELETE FROM portfolio WHERE code = ? AND (user_id IS NULL OR user_id = '')",
                    (code,),
                )
            portfolio_deleted = cursor.rowcount

            if user_id:
                cursor.execute("DELETE FROM transactions WHERE code = ? AND user_id = ?", (code, user_id))
            else:
                cursor.execute(
                    "DELETE FROM transactions WHERE code = ? AND (user_id IS NULL OR user_id = '')",
                    (code,),
                )
            tx_deleted = cursor.rowcount

            if portfolio_deleted <= 0 and tx_deleted <= 0:
                logger.info("Corrective delete noop: %s", code)

            if user_id:
                cursor.execute("DELETE FROM daily_snapshots WHERE date >= ? AND user_id = ?", (from_date, user_id))
            else:
                cursor.execute(
                    "DELETE FROM daily_snapshots WHERE date >= ? AND (user_id IS NULL OR user_id = '')",
                    (from_date,),
                )
            snapshots_deleted = cursor.rowcount

            conn.commit()
            logger.info(
                "Corrective delete done: code=%s from_date=%s portfolio=%s tx=%s snapshots=%s",
                code,
                from_date,
                portfolio_deleted,
                tx_deleted,
                snapshots_deleted,
            )
            return {
                "portfolio": int(portfolio_deleted),
                "transactions": int(tx_deleted),
                "snapshots": int(snapshots_deleted),
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
    ):
        """加仓。"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            if user_id:
                cursor.execute(
                    """
                    SELECT name, qty, price, curr, adjustment, asset_type
                    FROM portfolio
                    WHERE code = ? AND user_id = ?
                    """,
                    (code, user_id),
                )
            else:
                cursor.execute(
                    """
                    SELECT name, qty, price, curr, adjustment, asset_type
                    FROM portfolio
                    WHERE code = ? AND (user_id IS NULL OR user_id = '')
                    """,
                    (code,),
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
                    """
                    UPDATE portfolio SET qty = ?, price = ?, updated_at = datetime('now','localtime')
                    WHERE code = ? AND user_id = ?
                    """,
                    (new_qty, new_price, code, user_id),
                )
            else:
                cursor.execute(
                    """
                    UPDATE portfolio SET qty = ?, price = ?, updated_at = datetime('now','localtime')
                    WHERE code = ? AND (user_id IS NULL OR user_id = '')
                    """,
                    (new_qty, new_price, code),
                )

            cursor.execute(
                """
                INSERT INTO transactions (time, code, name, type, price, qty, amount, pnl, user_id)
                VALUES (?, ?, ?, '加仓', ?, ?, ?, 0, ?)
                """,
                (
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    code,
                    name,
                    price,
                    qty,
                    price * qty,
                    user_id,
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
    ):
        """减仓。"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            if user_id:
                cursor.execute(
                    """
                    SELECT name, qty, price, curr, adjustment, asset_type
                    FROM portfolio
                    WHERE code = ? AND user_id = ?
                    """,
                    (code, user_id),
                )
            else:
                cursor.execute(
                    """
                    SELECT name, qty, price, curr, adjustment, asset_type
                    FROM portfolio
                    WHERE code = ? AND (user_id IS NULL OR user_id = '')
                    """,
                    (code,),
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
                "asset_type": asset_type,
            }

            pnl = (price - old_price) * qty
            new_qty = old_qty - qty
            if new_qty < 0.001:
                if user_id:
                    cursor.execute(
                        """
                        UPDATE portfolio
                        SET qty = 0, adjustment = COALESCE(adjustment, 0) + ?, updated_at = datetime('now','localtime')
                        WHERE code = ? AND user_id = ?
                        """,
                        (pnl, code, user_id),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE portfolio
                        SET qty = 0, adjustment = COALESCE(adjustment, 0) + ?, updated_at = datetime('now','localtime')
                        WHERE code = ? AND (user_id IS NULL OR user_id = '')
                        """,
                        (pnl, code),
                    )
                after_asset = None
            else:
                if user_id:
                    cursor.execute(
                        """
                        UPDATE portfolio SET qty = ?, adjustment = adjustment + ?, updated_at = datetime('now','localtime')
                        WHERE code = ? AND user_id = ?
                        """,
                        (new_qty, pnl, code, user_id),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE portfolio SET qty = ?, adjustment = adjustment + ?, updated_at = datetime('now','localtime')
                        WHERE code = ? AND (user_id IS NULL OR user_id = '')
                        """,
                        (new_qty, pnl, code),
                    )
                after_asset = {
                    "code": code,
                    "name": name,
                    "qty": float(new_qty),
                    "price": old_price,
                    "curr": curr,
                    "adjustment": old_adj + pnl,
                    "asset_type": asset_type,
                }

            cursor.execute(
                """
                INSERT INTO transactions (time, code, name, type, price, qty, amount, pnl, user_id)
                VALUES (?, ?, ?, '减仓', ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    code,
                    name,
                    price,
                    qty,
                    price * qty,
                    pnl,
                    user_id,
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

            sell_detail = self.sell_asset(code, price, qty, user_id=user_id, return_detail=True)
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
    ) -> Dict[str, Any]:
        """使用现金账户买入。"""
        conn = self.get_connection()
        cursor = conn.cursor()

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
                        """
                        UPDATE portfolio SET qty = ?, price = ?, updated_at = datetime('now','localtime')
                        WHERE code = ? AND user_id = ?
                        """,
                        (new_qty, new_price, target_code, user_id),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE portfolio SET qty = ?, price = ?, updated_at = datetime('now','localtime')
                        WHERE code = ? AND (user_id IS NULL OR user_id = '')
                        """,
                        (new_qty, new_price, target_code),
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
                        INSERT INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, user_id, updated_at)
                        VALUES (?, ?, ?, ?, ?, 0, ?, ?, datetime('now','localtime'))
                        """,
                        (target_code, tx_name, qty, price, next_curr, next_asset_type, user_id),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, updated_at)
                        VALUES (?, ?, ?, ?, ?, 0, ?, datetime('now','localtime'))
                        """,
                        (target_code, tx_name, qty, price, next_curr, next_asset_type),
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

            cursor.execute(
                """
                INSERT INTO transactions (time, code, name, type, price, qty, amount, pnl, user_id)
                VALUES (?, ?, ?, '加仓', ?, ?, ?, 0, ?)
                """,
                (
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    target_code,
                    tx_name,
                    price,
                    qty,
                    price * qty,
                    user_id,
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
        cash_asset_id = operation.get("cash_asset_id")
        cash_before_amount = operation.get("cash_before_amount")

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if before_asset is None:
                if user_id:
                    cursor.execute("DELETE FROM portfolio WHERE code = ? AND user_id = ?", (code, user_id))
                else:
                    cursor.execute(
                        "DELETE FROM portfolio WHERE code = ? AND (user_id IS NULL OR user_id = '')",
                        (code,),
                    )
            else:
                name = str(before_asset.get("name") or code)
                qty = float(before_asset.get("qty") or 0.0)
                price = float(before_asset.get("price") or 0.0)
                curr = str(before_asset.get("curr") or "CNY")
                adjustment = float(before_asset.get("adjustment") or 0.0)
                asset_type = str(before_asset.get("asset_type") or "a")

                if user_id:
                    cursor.execute("SELECT id FROM portfolio WHERE code = ? AND user_id = ?", (code, user_id))
                else:
                    cursor.execute(
                        "SELECT id FROM portfolio WHERE code = ? AND (user_id IS NULL OR user_id = '')",
                        (code,),
                    )
                existing = cursor.fetchone()
                if existing:
                    if user_id:
                        cursor.execute(
                            """
                            UPDATE portfolio
                            SET name = ?, qty = ?, price = ?, curr = ?, adjustment = ?, asset_type = ?, updated_at = datetime('now','localtime')
                            WHERE code = ? AND user_id = ?
                            """,
                            (name, qty, price, curr, adjustment, asset_type, code, user_id),
                        )
                    else:
                        cursor.execute(
                            """
                            UPDATE portfolio
                            SET name = ?, qty = ?, price = ?, curr = ?, adjustment = ?, asset_type = ?, updated_at = datetime('now','localtime')
                            WHERE code = ? AND (user_id IS NULL OR user_id = '')
                            """,
                            (name, qty, price, curr, adjustment, asset_type, code),
                        )
                else:
                    if user_id:
                        cursor.execute(
                            """
                            INSERT INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, user_id, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
                            """,
                            (code, name, qty, price, curr, adjustment, asset_type, user_id),
                        )
                    else:
                        cursor.execute(
                            """
                            INSERT INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
                            """,
                            (code, name, qty, price, curr, adjustment, asset_type),
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

    def get_today_buy_transactions(self, date_str: str, user_id: str = None) -> Dict[str, Dict[str, float]]:
        """返回指定日期的加仓记录，按 code 聚合 qty 和 amount。

        Returns: {code: {"qty": float, "amount": float}}
        """
        result: Dict[str, Dict[str, float]] = {}
        conn = self.get_connection()
        cursor = conn.cursor()
        user_condition = "AND user_id = ?" if user_id else "AND (user_id IS NULL OR user_id = '')"
        user_param = (user_id,) if user_id else ()
        try:
            cursor.execute(
                """
                SELECT code, SUM(qty) AS total_qty, SUM(amount) AS total_amount
                FROM transactions
                WHERE type = '加仓' AND time LIKE ?
                """
                + f" {user_condition}"
                + " GROUP BY code",
                (f"{date_str}%",) + user_param,
            )
            for row in cursor.fetchall():
                code = str(row["code"] or "")
                qty = float(row["total_qty"] or 0.0)
                amount = float(row["total_amount"] or 0.0)
                if qty > 0:
                    result[code] = {"qty": qty, "amount": amount}
            return result
        except Exception as exc:
            logger.error("Failed to get today buy transactions date=%s: %s", date_str, exc)
            return result
        finally:
            conn.close()

    def get_realized_pnl_by_date(self, date_str: str, user_id: str = None) -> Dict[str, float]:
        """获取指定日期按市场聚合的已实现盈亏。"""
        result = {k: 0.0 for k in DEFAULT_MARKETS}
        conn = self.get_connection()
        cursor = conn.cursor()
        user_condition = "AND user_id = ?" if user_id else "AND (user_id IS NULL OR user_id = '')"
        user_param = (user_id,) if user_id else ()

        try:
            cursor.execute(
                """
                SELECT code, pnl
                FROM transactions
                WHERE type = '减仓' AND time LIKE ?
                """
                + f" {user_condition}",
                (f"{date_str}%",) + user_param,
            )
            for row in cursor.fetchall():
                raw_code = str(row["code"] or "")
                normalized = parse_code(raw_code, "").get("code") or raw_code
                code = str(normalized or raw_code)
                market = str(market_from_asset(code) or "a").lower()
                if market not in result:
                    market = "a"
                result[market] += float(row["pnl"] or 0.0)
            return result
        except Exception as exc:
            logger.error("Failed to get realized pnl by date=%s: %s", date_str, exc)
            return result
        finally:
            conn.close()
