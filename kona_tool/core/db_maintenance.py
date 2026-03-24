"""
快照修复与清理数据库能力。

这一层只做：
- 休市日清理预览 / 执行
- 指定日期 day_pnl 修复
"""
import logging
from typing import List, Optional

try:
    from .market_calendar import is_markets_closed_on_date
except ImportError:  # 兼容被单文件动态加载的测试场景
    from core.market_calendar import is_markets_closed_on_date

logger = logging.getLogger(__name__)
DEFAULT_MARKETS = ("a", "hk", "us", "fund")


class MaintenanceDatabaseMixin:
    """给 DatabaseManager 提供快照修复与清理相关方法。"""

    def _normalize_cleanup_markets(self, markets: Optional[List[str]]) -> List[str]:
        allowed = {"a", "hk", "us", "fund"}
        result: List[str] = []
        for raw in (markets or list(DEFAULT_MARKETS)):
            market = str(raw or "").strip().lower()
            if market in allowed and market not in result:
                result.append(market)
        return result or list(DEFAULT_MARKETS)

    def get_closed_snapshot_dates(
        self,
        markets: Optional[List[str]] = None,
        user_id: str = None,
        start_date: str = "",
        end_date: str = "",
    ) -> List[str]:
        """获取在指定市场集合下判定为休市日的快照日期列表。"""
        normalized_markets = self._normalize_cleanup_markets(markets)
        conn = self.get_connection()
        cursor = conn.cursor()

        sql = "SELECT DISTINCT date FROM daily_snapshots WHERE 1=1"
        params: List[str] = []
        if user_id:
            sql += " AND user_id = ?"
            params.append(user_id)
        if start_date:
            sql += " AND date >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND date <= ?"
            params.append(end_date)
        sql += " ORDER BY date ASC"

        try:
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            result: List[str] = []
            for row in rows:
                date_str = str(row["date"])
                if is_markets_closed_on_date(normalized_markets, date_str):
                    result.append(date_str)
            return result
        finally:
            conn.close()

    def preview_cleanup_market_closed(
        self,
        markets: Optional[List[str]] = None,
        user_id: str = None,
        start_date: str = "",
        end_date: str = "",
    ) -> int:
        """预览休市日清理将影响的快照条数。"""
        return len(
            self.get_closed_snapshot_dates(
                markets=markets,
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
            )
        )

    def cleanup_market_closed_day_pnl(
        self,
        markets: Optional[List[str]] = None,
        user_id: str = None,
        start_date: str = "",
        end_date: str = "",
    ) -> int:
        """将判定为休市日的 day_pnl 批量清零。"""
        dates = self.get_closed_snapshot_dates(
            markets=markets,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )
        if not dates:
            return 0

        conn = self.get_connection()
        cursor = conn.cursor()
        cleaned = 0

        try:
            for date_str in dates:
                if user_id:
                    cursor.execute(
                        """
                        UPDATE daily_snapshots
                        SET day_pnl = 0, updated_at = datetime('now','localtime')
                        WHERE date = ? AND user_id = ?
                        """,
                        (date_str, user_id),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE daily_snapshots
                        SET day_pnl = 0, updated_at = datetime('now','localtime')
                        WHERE date = ?
                        """,
                        (date_str,),
                    )
                cleaned += int(cursor.rowcount or 0)
            conn.commit()
            return cleaned
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def fix_snapshot_day_pnl(self, dates: list, user_id: str = None) -> bool:
        """修复指定日期的 day_pnl 为 0。"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            for date in dates:
                if user_id:
                    cursor.execute(
                        """
                        UPDATE daily_snapshots
                        SET day_pnl = 0, updated_at = datetime('now','localtime')
                        WHERE date = ? AND user_id = ?
                        """,
                        (date, user_id),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE daily_snapshots
                        SET day_pnl = 0, updated_at = datetime('now','localtime')
                        WHERE date = ? AND (user_id IS NULL OR user_id = '')
                        """,
                        (date,),
                    )
                logger.info("Fixed day_pnl for date: %s", date)

            conn.commit()
            return True
        except Exception as exc:
            logger.error("Failed to fix snapshot day_pnl: %s", exc)
            conn.rollback()
            return False
        finally:
            conn.close()
