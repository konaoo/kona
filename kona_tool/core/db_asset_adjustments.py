"""
资产调整记录数据库能力。

每次对现金/其他资产/负债做增加或减少操作时，
在一个事务内同时更新资产余额并写入调整记录。
"""
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_ASSET_TYPE_TO_TABLE: Dict[str, str] = {
    'cash': 'cash_assets',
    'other': 'other_assets',
    'liability': 'liabilities',
}


class AssetAdjustmentDatabaseMixin:
    """给 DatabaseManager 提供资产调整记录相关方法。"""

    def add_asset_adjustment(
        self,
        *,
        asset_type: str,
        asset_id: int,
        mode: str,
        delta: float,
        note: str,
        name: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        在一个事务内同时更新资产余额（和名称）、写入调整记录。

        balance_after 由服务端从当前余额计算，客户端无需传入。
        返回 {"id": int, "balance_after": float}，失败返回 None。
        """
        table = _ASSET_TYPE_TO_TABLE.get(asset_type)
        if not table:
            logger.warning("[asset_adjustment] unknown asset_type=%s", asset_type)
            return None

        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # 1. 验证资产存在且属于当前用户，同时获取当前余额
            if user_id:
                cursor.execute(
                    f"SELECT id, amount FROM {table} WHERE id = ? AND user_id = ?",
                    (asset_id, user_id),
                )
            else:
                cursor.execute(
                    f"SELECT id, amount FROM {table} WHERE id = ?",
                    (asset_id,),
                )
            row = cursor.fetchone()
            if not row:
                logger.warning(
                    "[asset_adjustment] asset not found type=%s id=%s user=%s",
                    asset_type, asset_id, user_id,
                )
                return None

            # 2. 服务端计算新余额
            current_amount = float(row['amount'])
            balance_after = current_amount + delta if mode == 'add' else current_amount - delta

            # 3. 更新资产（余额 + 可选名称）
            if name:
                cursor.execute(
                    f"UPDATE {table} SET amount = ?, name = ?, updated_at = CURRENT_TIMESTAMP"
                    f" WHERE id = ?",
                    (balance_after, name, asset_id),
                )
            else:
                cursor.execute(
                    f"UPDATE {table} SET amount = ?, updated_at = CURRENT_TIMESTAMP"
                    f" WHERE id = ?",
                    (balance_after, asset_id),
                )

            # 4. 写入调整记录
            cursor.execute(
                """
                INSERT INTO asset_adjustments
                    (asset_type, asset_id, mode, delta, note, balance_after, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (asset_type, asset_id, mode, delta, note or '', balance_after, user_id),
            )
            adjustment_id = cursor.lastrowid
            conn.commit()

            logger.info(
                "[asset_adjustment_ok] type=%s id=%s mode=%s delta=%s balance_after=%s",
                asset_type, asset_id, mode, delta, balance_after,
            )
            return {"id": adjustment_id, "balance_after": balance_after}

        except Exception as exc:
            conn.rollback()
            logger.error(
                "[asset_adjustment_error] type=%s id=%s err=%s",
                asset_type, asset_id, exc,
            )
            return None
        finally:
            conn.close()

    def get_asset_adjustments(
        self,
        *,
        asset_type: str,
        asset_id: int,
        user_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """获取某资产的调整记录，最新在前。"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            if user_id:
                cursor.execute(
                    """
                    SELECT id, mode, delta, note, balance_after, created_at
                    FROM asset_adjustments
                    WHERE asset_type = ? AND asset_id = ? AND user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (asset_type, asset_id, user_id, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, mode, delta, note, balance_after, created_at
                    FROM asset_adjustments
                    WHERE asset_type = ? AND asset_id = ?
                      AND (user_id IS NULL OR user_id = '')
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (asset_type, asset_id, limit),
                )
            return [
                {
                    "id": row["id"],
                    "mode": row["mode"],
                    "delta": float(row["delta"]),
                    "note": row["note"] or '',
                    "balance_after": float(row["balance_after"]),
                    "created_at": row["created_at"],
                }
                for row in cursor.fetchall()
            ]
        finally:
            conn.close()
