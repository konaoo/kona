"""
资产账户与交易记录数据库能力。

这一层只做：
- 交易记录查询
- 现金 / 其他资产 / 负债的 CRUD

这样 db.py 可以少背一坨“资产账户细节”职责。
"""
import logging
import sqlite3
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AssetAccountDatabaseMixin:
    """给 DatabaseManager 提供资产账户与交易记录相关方法。"""

    def get_transactions(self, limit: int = 100, user_id: str = None) -> List[Dict[str, Any]]:
        """获取交易记录。"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if user_id:
            cursor.execute(
                '''
                SELECT time, code, name, type, price, qty, amount, pnl
                FROM transactions
                WHERE user_id = ?
                ORDER BY time DESC
                LIMIT ?
                ''',
                (user_id, limit),
            )
        else:
            cursor.execute(
                '''
                SELECT time, code, name, type, price, qty, amount, pnl
                FROM transactions
                WHERE user_id IS NULL OR user_id = ''
                ORDER BY time DESC
                LIMIT ?
                ''',
                (limit,),
            )

        data = []
        for row in cursor.fetchall():
            data.append(
                {
                    'time': row['time'],
                    'code': row['code'],
                    'name': row['name'],
                    'type': row['type'],
                    'price': float(row['price']),
                    'qty': float(row['qty']),
                    'amount': float(row['amount']),
                    'pnl': float(row['pnl']),
                }
            )

        conn.close()
        return data

    def get_cash_assets(self, user_id: str = None) -> List[Dict[str, Any]]:
        """获取所有现金资产。"""
        return self._list_named_assets(
            table='cash_assets',
            default_icon='🏦',
            user_id=user_id,
        )

    def get_cash_asset_by_id(self, asset_id: int, user_id: str = None) -> Optional[Dict[str, Any]]:
        """按 ID 获取现金资产。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if user_id:
                cursor.execute(
                    '''
                    SELECT id, icon, name, amount, curr
                    FROM cash_assets
                    WHERE id = ? AND user_id = ?
                    LIMIT 1
                    ''',
                    (asset_id, user_id),
                )
            else:
                cursor.execute(
                    '''
                    SELECT id, icon, name, amount, curr
                    FROM cash_assets
                    WHERE id = ? AND (user_id IS NULL OR user_id = '')
                    LIMIT 1
                    ''',
                    (asset_id,),
                )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                'id': int(row['id']),
                'icon': row['icon'] or '🏦',
                'name': row['name'],
                'amount': float(row['amount']),
                'curr': row['curr'],
            }
        finally:
            conn.close()

    def add_cash_asset(
        self,
        name: str,
        amount: float,
        curr: str = 'CNY',
        user_id: str = None,
        icon: str = '🏦',
    ) -> bool:
        """添加现金资产。"""
        return self._insert_named_asset(
            table='cash_assets',
            default_icon='🏦',
            name=name,
            amount=amount,
            curr=curr,
            user_id=user_id,
            icon=icon,
            label='Cash asset',
        )

    def delete_cash_asset(self, asset_id: int, user_id: str = None) -> bool:
        """删除现金资产。"""
        return self._delete_named_asset(
            table='cash_assets',
            asset_id=asset_id,
            user_id=user_id,
            label='Cash asset',
        )

    def update_cash_asset(
        self,
        asset_id: int,
        name: str,
        amount: float,
        curr: str = 'CNY',
        user_id: str = None,
        icon: str = '🏦',
    ) -> bool:
        """更新现金资产。"""
        return self._update_named_asset(
            table='cash_assets',
            default_icon='🏦',
            asset_id=asset_id,
            name=name,
            amount=amount,
            curr=curr,
            user_id=user_id,
            icon=icon,
            label='Cash asset',
        )

    def get_other_assets(self, user_id: str = None) -> List[Dict[str, Any]]:
        """获取所有其他资产。"""
        return self._list_named_assets(
            table='other_assets',
            default_icon='📦',
            user_id=user_id,
        )

    def add_other_asset(
        self,
        name: str,
        amount: float,
        curr: str = 'CNY',
        user_id: str = None,
        icon: str = '📦',
    ) -> bool:
        """添加其他资产。"""
        return self._insert_named_asset(
            table='other_assets',
            default_icon='📦',
            name=name,
            amount=amount,
            curr=curr,
            user_id=user_id,
            icon=icon,
            label='Other asset',
        )

    def delete_other_asset(self, asset_id: int, user_id: str = None) -> bool:
        """删除其他资产。"""
        return self._delete_named_asset(
            table='other_assets',
            asset_id=asset_id,
            user_id=user_id,
            label='Other asset',
        )

    def update_other_asset(
        self,
        asset_id: int,
        name: str,
        amount: float,
        curr: str = 'CNY',
        user_id: str = None,
        icon: str = '📦',
    ) -> bool:
        """更新其他资产。"""
        return self._update_named_asset(
            table='other_assets',
            default_icon='📦',
            asset_id=asset_id,
            name=name,
            amount=amount,
            curr=curr,
            user_id=user_id,
            icon=icon,
            label='Other asset',
        )

    def get_liabilities(self, user_id: str = None) -> List[Dict[str, Any]]:
        """获取所有负债。"""
        return self._list_named_assets(
            table='liabilities',
            default_icon='💳',
            user_id=user_id,
        )

    def add_liability(
        self,
        name: str,
        amount: float,
        curr: str = 'CNY',
        user_id: str = None,
        icon: str = '💳',
    ) -> bool:
        """添加负债。"""
        return self._insert_named_asset(
            table='liabilities',
            default_icon='💳',
            name=name,
            amount=amount,
            curr=curr,
            user_id=user_id,
            icon=icon,
            label='Liability',
        )

    def delete_liability(self, liability_id: int, user_id: str = None) -> bool:
        """删除负债。"""
        return self._delete_named_asset(
            table='liabilities',
            asset_id=liability_id,
            user_id=user_id,
            label='Liability',
        )

    def update_liability(
        self,
        liability_id: int,
        name: str,
        amount: float,
        curr: str = 'CNY',
        user_id: str = None,
        icon: str = '💳',
    ) -> bool:
        """更新负债。"""
        return self._update_named_asset(
            table='liabilities',
            default_icon='💳',
            asset_id=liability_id,
            name=name,
            amount=amount,
            curr=curr,
            user_id=user_id,
            icon=icon,
            label='Liability',
        )

    def _list_named_assets(
        self,
        table: str,
        default_icon: str,
        user_id: Optional[str],
    ) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()

        if user_id:
            cursor.execute(
                f'''
                SELECT id, icon, name, amount, curr
                FROM {table}
                WHERE user_id = ?
                ORDER BY id
                ''',
                (user_id,),
            )
        else:
            cursor.execute(
                f'''
                SELECT id, icon, name, amount, curr
                FROM {table}
                WHERE user_id IS NULL OR user_id = ''
                ORDER BY id
                '''
            )

        data = []
        for row in cursor.fetchall():
            data.append(
                {
                    'id': row['id'],
                    'icon': row['icon'] or default_icon,
                    'name': row['name'],
                    'amount': float(row['amount']),
                    'curr': row['curr'],
                }
            )

        conn.close()
        return data

    def _insert_named_asset(
        self,
        table: str,
        default_icon: str,
        name: str,
        amount: float,
        curr: str,
        user_id: Optional[str],
        icon: str,
        label: str,
    ) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            try:
                cursor.execute(
                    f'''
                    INSERT INTO {table} (icon, name, amount, curr, user_id)
                    VALUES (?, ?, ?, ?, ?)
                    ''',
                    (icon or default_icon, name, amount, curr, user_id),
                )
            except sqlite3.OperationalError as exc:
                logger.warning(f"{table} insert fallback due to schema mismatch: {exc}")
                cursor.execute(
                    f'''
                    INSERT INTO {table} (name, amount)
                    VALUES (?, ?)
                    ''',
                    (name, amount),
                )

            conn.commit()
            logger.info(f"{label} added: {name}, amount={amount}")
            return True
        except Exception as exc:
            logger.error(f"Failed to add {label.lower()}: {exc}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def _delete_named_asset(
        self,
        table: str,
        asset_id: int,
        user_id: Optional[str],
        label: str,
    ) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            if user_id:
                cursor.execute(
                    f'DELETE FROM {table} WHERE id = ? AND user_id = ?',
                    (asset_id, user_id),
                )
            else:
                cursor.execute(
                    f'DELETE FROM {table} WHERE id = ? AND (user_id IS NULL OR user_id = "")',
                    (asset_id,),
                )
            conn.commit()
            logger.info(f"{label} deleted: {asset_id}")
            return True
        except Exception as exc:
            logger.error(f"Failed to delete {label.lower()}: {exc}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def _update_named_asset(
        self,
        table: str,
        default_icon: str,
        asset_id: int,
        name: str,
        amount: float,
        curr: str,
        user_id: Optional[str],
        icon: str,
        label: str,
    ) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            try:
                if user_id:
                    cursor.execute(
                        f'''
                        UPDATE {table} SET icon = ?, name = ?, amount = ?, curr = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ? AND user_id = ?
                        ''',
                        (icon or default_icon, name, amount, curr, asset_id, user_id),
                    )
                else:
                    cursor.execute(
                        f'''
                        UPDATE {table} SET icon = ?, name = ?, amount = ?, curr = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ? AND (user_id IS NULL OR user_id = '')
                        ''',
                        (icon or default_icon, name, amount, curr, asset_id),
                    )
            except sqlite3.OperationalError as exc:
                logger.warning(f"{table} update fallback due to schema mismatch: {exc}")
                cursor.execute(
                    f'''
                    UPDATE {table} SET name = ?, amount = ?
                    WHERE id = ?
                    ''',
                    (name, amount, asset_id),
                )

            conn.commit()
            logger.info(f"{label} updated: {asset_id}")
            return True
        except Exception as exc:
            logger.error(f"Failed to update {label.lower()}: {exc}")
            conn.rollback()
            return False
        finally:
            conn.close()
