"""
分析页概览、收益日历与排行数据库能力。

这一层只做：
- 分析页概览（pnl overview）
- 收益日历
- 分市场收益日历
- 盈亏排行
"""
import logging
import sys
from datetime import datetime, timedelta
import datetime as dt
from typing import Any, Dict, List, Optional, Tuple

try:
    from .market_calendar import all_markets_closed, is_markets_closed_on_date
except ImportError:  # 兼容被单文件动态加载的测试场景
    from core.market_calendar import all_markets_closed, is_markets_closed_on_date

logger = logging.getLogger(__name__)
DEFAULT_MARKETS = ("a", "hk", "us", "fund")
MARKET_BREAKDOWN_MARKETS = ("a", "hk", "us", "fund", "unallocated")


def _is_weekend_date(date_str: str) -> bool:
    try:
        return dt.datetime.strptime(date_str, "%Y-%m-%d").weekday() >= 5
    except Exception:
        return False


def _is_market_closed_date(date_str: str, markets: Tuple[str, ...] = DEFAULT_MARKETS) -> bool:
    """
    兼容旧调用方保留这个导出。

    第一轮收益审计修复后，历史日收益不再依赖“休市日强制归零”来猜值，
    但 db.py/部分单测仍会 import 这个函数做兼容 patch。
    """
    try:
        return is_markets_closed_on_date(markets, date_str)
    except Exception:
        return _is_weekend_date(date_str)


def _get_db_module():
    """
    获取 db.py 对应的模块对象，用于测试里 patch datetime / 休市判断时仍可生效。

    典型情况：
    - 线上/正常运行：模块名是 core.db 或 kona_tool.core.db
    - 单测里动态加载 core/db.py：模块名可能是 db_module（见 test_calendar_weekend.py）
    """
    direct = sys.modules.get("core.db") or sys.modules.get("kona_tool.core.db")
    if direct is not None:
        return direct

    # 兜底：寻找“文件路径指向 core/db.py”的模块（兼容动态加载的模块名）。
    for mod in list(sys.modules.values()):
        if mod is None:
            continue
        path = getattr(mod, "__file__", "") or ""
        normalized = str(path).replace("\\", "/")
        if normalized.endswith("/core/db.py") or normalized.endswith("/kona_tool/core/db.py"):
            return mod
    return None


def _get_datetime_now() -> datetime:
    db_module = _get_db_module()
    if db_module is not None:
        dt_ref = getattr(db_module, "datetime", None)
        if dt_ref is not None and hasattr(dt_ref, "now"):
            try:
                return dt_ref.now()
            except Exception:
                pass
    return datetime.now()


def _get_is_market_closed_date(date_str: str, markets: Tuple[str, ...] = DEFAULT_MARKETS) -> bool:
    """
    兼容旧测试和旧调用方保留这个 wrapper。
    """
    return _is_market_closed_date(date_str, markets)


def _round_pnl(value: Any) -> float:
    try:
        return round(float(value or 0.0), 2)
    except Exception:
        return 0.0


def _build_months_by_year(date_values: List[str], now: datetime) -> Dict[int, set]:
    months_by_year: Dict[int, set] = {}
    for date_str in date_values:
        parts = str(date_str or "").split("-")
        if len(parts) != 3:
            continue
        y = int(parts[0])
        m = int(parts[1])
        months_by_year.setdefault(y, set()).add(m)
    months_by_year.setdefault(now.year, set()).add(now.month)
    return months_by_year


class AnalysisDatabaseMixin:
    """给 DatabaseManager 提供分析页相关方法。"""

    @staticmethod
    def _resolve_period_start_base(normalized_rows: List[Dict[str, Any]], prev_invest: float) -> float:
        if prev_invest > 0:
            return prev_invest
        if normalized_rows:
            return float(normalized_rows[0].get("total_invest") or 0.0)
        return 0.0

    def _normalize_snapshot_rows_legacy(self, rows: List[Any]) -> List[Dict[str, Any]]:
        normalized = []
        for row in rows:
            pnl = float(row["day_pnl"]) if row["day_pnl"] is not None else 0.0
            normalized.append(
                {
                    "date": str(row["date"]),
                    "pnl": _round_pnl(pnl),
                    "total_invest": float(row["total_invest"] or 0.0),
                }
            )
        return normalized

    def _fetch_all_calendar_dates(
        self,
        cursor: Any,
        *,
        user_condition: str,
        user_param: tuple,
    ) -> List[str]:
        cursor.execute(
            f"""
            SELECT date
            FROM daily_snapshots
            WHERE {user_condition}
            ORDER BY date ASC
            """,
            user_param,
        )
        return [str(row["date"]) for row in cursor.fetchall() if row["date"]]

    def _build_effective_pnl_series(
        self,
        cursor: Any,
        *,
        user_condition: str,
        user_param: tuple,
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        cursor.execute(
            f"""
            SELECT date, total_pnl, day_pnl, total_invest, updated_at
            FROM daily_snapshots
            WHERE date >= ? AND date <= ? AND {user_condition}
            ORDER BY date ASC
            """,
            (start_date, end_date) + user_param,
        )
        legacy_rows = self._normalize_snapshot_rows_legacy(cursor.fetchall())
        return legacy_rows

    def _get_ledger_pnl_overview(self, period: str, user_id: str, ledger_id: int) -> Dict[str, Any]:
        """获取指定账本的盈亏概览（查 ledger_daily_snapshots）。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            today = _get_datetime_now()
            today_str = today.strftime("%Y-%m-%d")

            if period == "day":
                cursor.execute(
                    "SELECT day_pnl, total_cost FROM ledger_daily_snapshots WHERE date = ? AND user_id = ? AND ledger_id = ? LIMIT 1",
                    (today_str, user_id, ledger_id),
                )
                row = cursor.fetchone()
                if row:
                    pnl = _round_pnl(row["day_pnl"])
                    base = float(row["total_cost"] or 0)
                    return {"pnl": pnl, "pnl_rate": round(pnl / base * 100, 2) if base else 0, "base_value": base}
                return {"pnl": 0, "pnl_rate": 0, "base_value": 0}

            # month/year/all: sum day_pnl over period
            if period == "month":
                start = today.strftime("%Y-%m-01")
            elif period == "year":
                start = today.strftime("%Y-01-01")
            else:
                start = "0001-01-01"

            cursor.execute(
                """SELECT COALESCE(SUM(day_pnl), 0) as total_pnl FROM ledger_daily_snapshots
                   WHERE date >= ? AND date <= ? AND user_id = ? AND ledger_id = ?""",
                (start, today_str, user_id, ledger_id),
            )
            row = cursor.fetchone()
            pnl = _round_pnl(row["total_pnl"] if row else 0)

            # Get base from last snapshot before period
            cursor.execute(
                """SELECT total_cost FROM ledger_daily_snapshots
                   WHERE date < ? AND user_id = ? AND ledger_id = ?
                   ORDER BY date DESC LIMIT 1""",
                (start, user_id, ledger_id),
            )
            prev = cursor.fetchone()
            base = float(prev["total_cost"] or 0) if prev else 0
            if not base:
                cursor.execute(
                    """SELECT total_cost FROM ledger_daily_snapshots
                       WHERE date >= ? AND user_id = ? AND ledger_id = ?
                       ORDER BY date ASC LIMIT 1""",
                    (start, user_id, ledger_id),
                )
                first = cursor.fetchone()
                base = float(first["total_cost"] or 0) if first else 0
            base = base or 1
            return {"pnl": pnl, "pnl_rate": round(pnl / base * 100, 2), "base_value": base}
        except Exception as exc:
            logger.error("Failed to get ledger pnl overview: %s", exc)
            return {"pnl": 0, "pnl_rate": 0, "base_value": 0}
        finally:
            conn.close()

    def get_pnl_overview(self, period: str = "day", user_id: str = None, ledger_id: int | None = None) -> Dict[str, Any]:
        """
        获取盈亏概览数据。

        Args:
            period: day|month|year|all
            user_id: 用户ID
            ledger_id: 账本ID，非空时查 ledger_daily_snapshots
        """
        if ledger_id is not None:
            return self._get_ledger_pnl_overview(period, user_id or "", ledger_id)

        conn = self.get_connection()
        cursor = conn.cursor()

        user_condition = "user_id = ?" if user_id else "(user_id IS NULL OR user_id = '')"
        user_param = (user_id,) if user_id else ()

        try:
            today = _get_datetime_now()
            today_str = today.strftime("%Y-%m-%d")

            def _fetch_prev_snapshot(date_str: str):
                cursor.execute(
                    f"""
                    SELECT date, total_pnl, total_invest FROM daily_snapshots
                    WHERE date < ? AND {user_condition}
                    ORDER BY date DESC
                    LIMIT 1
                    """,
                    (date_str,) + user_param,
                )
                return cursor.fetchone()

            if period == "day":
                cursor.execute(
                    f"""
                    SELECT date, day_pnl, total_invest FROM daily_snapshots
                    WHERE date = ? AND {user_condition}
                    LIMIT 1
                    """,
                    (today_str,) + user_param,
                )
                row = cursor.fetchone()
                if row:
                    pnl = float(row["day_pnl"]) if row["day_pnl"] else 0
                    base = float(row["total_invest"]) if row["total_invest"] else 1
                    return {
                        "pnl": pnl,
                        "pnl_rate": round(pnl / base * 100, 2) if base else 0,
                        "base_value": base,
                    }
                return {"pnl": 0, "pnl_rate": 0, "base_value": 0}

            if period == "month":
                month_start = today.strftime("%Y-%m-01")
                normalized_rows = self._build_effective_pnl_series(
                    cursor,
                    user_condition=user_condition,
                    user_param=user_param,
                    start_date=month_start,
                    end_date=today_str,
                )
                prev = _fetch_prev_snapshot(month_start)
                prev_invest = float(prev["total_invest"] or 0) if prev else 0.0
                if normalized_rows:
                    pnl = _round_pnl(sum(float(row["pnl"] or 0.0) for row in normalized_rows))
                    base = self._resolve_period_start_base(normalized_rows, prev_invest) or 1
                    return {
                        "pnl": pnl,
                        "pnl_rate": round(pnl / base * 100, 2) if base else 0,
                        "base_value": base,
                    }
                return {"pnl": 0, "pnl_rate": 0, "base_value": 0}

            if period == "year":
                year_start = today.strftime("%Y-01-01")
                normalized_rows = self._build_effective_pnl_series(
                    cursor,
                    user_condition=user_condition,
                    user_param=user_param,
                    start_date=year_start,
                    end_date=today_str,
                )
                prev = _fetch_prev_snapshot(year_start)
                prev_invest = float(prev["total_invest"] or 0) if prev else 0.0
                if normalized_rows:
                    pnl = _round_pnl(sum(float(row["pnl"] or 0.0) for row in normalized_rows))
                    base = self._resolve_period_start_base(normalized_rows, prev_invest) or 1
                    return {
                        "pnl": pnl,
                        "pnl_rate": round(pnl / base * 100, 2) if base else 0,
                        "base_value": base,
                    }
                return {"pnl": 0, "pnl_rate": 0, "base_value": 0}

            normalized_rows = self._build_effective_pnl_series(
                cursor,
                user_condition=user_condition,
                user_param=user_param,
                start_date="0001-01-01",
                end_date=today_str,
            )
            if normalized_rows:
                pnl = _round_pnl(sum(float(row["pnl"] or 0.0) for row in normalized_rows))
                base = self._resolve_period_start_base(normalized_rows, 0.0) or 1
                return {
                    "pnl": pnl,
                    "pnl_rate": round(pnl / base * 100, 2) if base else 0,
                    "base_value": base,
                }
            return {"pnl": 0, "pnl_rate": 0, "base_value": 0}

        except Exception as exc:
            logger.error("Failed to get pnl overview: %s", exc)
            return {"pnl": 0, "pnl_rate": 0, "base_value": 0}
        finally:
            conn.close()

    def _get_ledger_calendar_data(
        self,
        time_type: str,
        user_id: str,
        ledger_id: int,
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> Dict[str, Any]:
        """获取指定账本的收益日历数据（查 ledger_daily_snapshots）。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            now = _get_datetime_now()
            today_str = now.strftime("%Y-%m-%d")

            # Fetch all dates for selectable
            cursor.execute(
                "SELECT date FROM ledger_daily_snapshots WHERE user_id = ? AND ledger_id = ? ORDER BY date ASC",
                (user_id, ledger_id),
            )
            all_dates = [str(row["date"]) for row in cursor.fetchall() if row["date"]]
            months_by_year = _build_months_by_year(all_dates, now)
            selectable_years = sorted(months_by_year.keys())
            selectable_months_by_year = {str(y): sorted(list(months_by_year[y])) for y in selectable_years}
            selectable = {
                "day": {"years": selectable_years, "months_by_year": selectable_months_by_year},
                "month": {"years": selectable_years},
            }

            latest_year = selectable_years[-1] if selectable_years else None
            latest_month = max(months_by_year[latest_year]) if latest_year is not None else None
            period: Dict[str, Any] = {"time_type": time_type}
            items = []
            total_pnl = 0.0
            rate_base = 0.0

            def _fetch_prev_cost(date_str: str) -> float:
                cursor.execute(
                    "SELECT total_cost FROM ledger_daily_snapshots WHERE date < ? AND user_id = ? AND ledger_id = ? ORDER BY date DESC LIMIT 1",
                    (date_str, user_id, ledger_id),
                )
                row = cursor.fetchone()
                return float(row["total_cost"] or 0.0) if row else 0.0

            def _fetch_rows(start_date: str, end_date: str) -> List[Dict[str, Any]]:
                cursor.execute(
                    "SELECT date, day_pnl, total_cost FROM ledger_daily_snapshots WHERE date >= ? AND date <= ? AND user_id = ? AND ledger_id = ? ORDER BY date ASC",
                    (start_date, end_date, user_id, ledger_id),
                )
                return [{"date": str(r["date"]), "pnl": _round_pnl(r["day_pnl"]), "total_cost": float(r["total_cost"] or 0)} for r in cursor.fetchall()]

            def _resolve_base(rows, prev_cost):
                if prev_cost > 0:
                    return prev_cost
                if rows:
                    return float(rows[0].get("total_cost") or 0.0)
                return 0.0

            if time_type == "day":
                if not selectable_years:
                    period.update({"year": now.year, "month": now.month})
                    return {"items": [], "total_pnl": 0.0, "total_rate": 0.0, "title": f"{now.year}年{now.month}月累计", "period": period, "selectable": selectable}

                target_year = year
                target_month = month
                if target_year is None and target_month is None:
                    if now.year in months_by_year and now.month in months_by_year[now.year]:
                        target_year, target_month = now.year, now.month
                    else:
                        target_year, target_month = latest_year, latest_month
                else:
                    target_year = target_year or now.year
                    target_month = target_month or now.month
                period.update({"year": int(target_year), "month": int(target_month)})

                if target_year not in months_by_year or target_month not in months_by_year[target_year]:
                    return {"error": "Selected period has no snapshot data", "code": "INVALID_CALENDAR_PERIOD", "items": [], "total_pnl": 0.0, "total_rate": 0.0, "title": f"{target_year}年{target_month}月累计", "period": period, "selectable": selectable}

                month_start = f"{target_year:04d}-{target_month:02d}-01"
                if target_month == 12:
                    next_m = dt.datetime(target_year + 1, 1, 1)
                else:
                    next_m = dt.datetime(target_year, target_month + 1, 1)
                month_end = (next_m - timedelta(days=1)).strftime("%Y-%m-%d")
                if target_year == now.year and target_month == now.month:
                    month_end = min(month_end, today_str)

                rows = _fetch_rows(month_start, month_end)
                total_pnl = _round_pnl(sum(float(r["pnl"] or 0) for r in rows))
                for r in rows:
                    day = int(str(r["date"]).split("-")[2])
                    items.append({"label": f"{target_month}-{day}", "pnl": r["pnl"]})
                rate_base = _resolve_base(rows, _fetch_prev_cost(month_start))
                title = f"{target_year}年{target_month}月累计"

            elif time_type == "month":
                if not selectable_years:
                    period.update({"year": now.year})
                    return {"items": [], "total_pnl": 0.0, "total_rate": 0.0, "title": f"{now.year}年累计", "period": period, "selectable": selectable}

                target_year = year or (now.year if now.year in months_by_year else latest_year)
                period.update({"year": int(target_year)})
                if target_year not in months_by_year:
                    return {"error": "Selected period has no snapshot data", "code": "INVALID_CALENDAR_PERIOD", "items": [], "total_pnl": 0.0, "total_rate": 0.0, "title": f"{target_year}年累计", "period": period, "selectable": selectable}

                year_start = f"{target_year:04d}-01-01"
                year_end = today_str if target_year == now.year else f"{target_year:04d}-12-31"
                rows = _fetch_rows(year_start, year_end)
                month_totals: Dict[int, float] = {}
                for r in rows:
                    m = int(str(r["date"]).split("-")[1])
                    month_totals[m] = _round_pnl(month_totals.get(m, 0.0) + float(r["pnl"] or 0))
                month_limit = now.month if target_year == now.year else 12
                for m in range(1, month_limit + 1):
                    pnl = float(month_totals.get(m, 0.0) or 0.0)
                    items.append({"label": f"{m}月", "pnl": pnl})
                    total_pnl = _round_pnl(total_pnl + pnl)
                rate_base = _resolve_base(rows, _fetch_prev_cost(year_start))
                title = f"{target_year}年累计"

            elif time_type == "year":
                period = {"time_type": "year"}
                rows = _fetch_rows("0001-01-01", today_str)
                if rows:
                    year_totals: Dict[int, float] = {}
                    for r in rows:
                        y = int(str(r["date"]).split("-")[0])
                        year_totals[y] = _round_pnl(year_totals.get(y, 0.0) + float(r["pnl"] or 0))
                    start_year = int(str(rows[0]["date"]).split("-")[0])
                    for y in range(start_year, now.year + 1):
                        pnl = float(year_totals.get(y, 0.0) or 0.0)
                        items.append({"label": str(y), "pnl": pnl})
                        total_pnl = _round_pnl(total_pnl + pnl)
                rate_base = _resolve_base(rows, 0.0)
                title = "总累计"
            else:
                return {"error": "Invalid time type", "code": "INVALID_CALENDAR_PERIOD", "items": [], "total_pnl": 0.0, "total_rate": 0.0, "title": "", "period": period, "selectable": selectable}

            total_rate = round(total_pnl / rate_base * 100, 2) if rate_base else 0.0
            return {"items": items, "total_pnl": total_pnl, "total_rate": total_rate, "title": title, "period": period, "selectable": selectable}
        except Exception as exc:
            logger.error("Failed to get ledger calendar data: %s", exc)
            return {"items": [], "total_pnl": 0.0, "total_rate": 0.0, "title": "", "period": {"time_type": time_type}, "selectable": {"day": {"years": [], "months_by_year": {}}, "month": {"years": []}}}
        finally:
            conn.close()

    def get_calendar_data(
        self,
        time_type: str = "day",
        user_id: str = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
        ledger_id: int | None = None,
    ) -> Dict[str, Any]:
        """获取收益日历数据。"""
        if ledger_id is not None:
            return self._get_ledger_calendar_data(time_type, user_id or "", ledger_id, year, month)

        conn = self.get_connection()
        cursor = conn.cursor()

        user_condition = "user_id = ?" if user_id else "(user_id IS NULL OR user_id = '')"
        user_param = (user_id,) if user_id else ()

        try:
            now = _get_datetime_now()
            today_str = now.strftime("%Y-%m-%d")
            items = []
            total_pnl = 0.0
            rate_base = 0.0

            def _fetch_prev_invest(date_str: str) -> float:
                cursor.execute(
                    f"""
                    SELECT total_invest
                    FROM daily_snapshots
                    WHERE date < ? AND {user_condition}
                    ORDER BY date DESC
                    LIMIT 1
                    """,
                    (date_str,) + user_param,
                )
                row = cursor.fetchone()
                return float(row["total_invest"] or 0.0) if row else 0.0

            all_dates = self._fetch_all_calendar_dates(
                cursor,
                user_condition=user_condition,
                user_param=user_param,
            )
            months_by_year = _build_months_by_year(all_dates, now)

            selectable_years = sorted(months_by_year.keys())
            selectable_months_by_year = {str(y): sorted(list(months_by_year[y])) for y in selectable_years}
            selectable = {
                "day": {"years": selectable_years, "months_by_year": selectable_months_by_year},
                "month": {"years": selectable_years},
            }

            latest_year = selectable_years[-1] if selectable_years else None
            latest_month = max(months_by_year[latest_year]) if latest_year is not None else None

            period: Dict[str, Any] = {"time_type": time_type}

            if time_type == "day":
                if not selectable_years:
                    period.update({"year": now.year, "month": now.month})
                    return {
                        "items": [],
                        "total_pnl": 0.0,
                        "total_rate": 0.0,
                        "title": f"{now.year}年{now.month}月累计",
                        "period": period,
                        "selectable": selectable,
                    }

                target_year = year
                target_month = month
                if target_year is None and target_month is None:
                    if now.year in months_by_year and now.month in months_by_year[now.year]:
                        target_year = now.year
                        target_month = now.month
                    else:
                        target_year = latest_year
                        target_month = latest_month
                else:
                    if target_year is None:
                        target_year = now.year
                    if target_month is None:
                        target_month = now.month

                period.update({"year": int(target_year), "month": int(target_month)})

                if target_year not in months_by_year or target_month not in months_by_year[target_year]:
                    return {
                        "error": "Selected period has no snapshot data",
                        "code": "INVALID_CALENDAR_PERIOD",
                        "items": [],
                        "total_pnl": 0.0,
                        "total_rate": 0.0,
                        "title": f"{target_year}年{target_month}月累计",
                        "period": period,
                        "selectable": selectable,
                    }

                month_start = f"{target_year:04d}-{target_month:02d}-01"
                if target_month == 12:
                    next_month = dt.datetime(target_year + 1, 1, 1)
                else:
                    next_month = dt.datetime(target_year, target_month + 1, 1)
                month_end = (next_month - timedelta(days=1)).strftime("%Y-%m-%d")
                if target_year == now.year and target_month == now.month:
                    month_end = min(month_end, today_str)

                normalized_rows = self._build_effective_pnl_series(
                    cursor,
                    user_condition=user_condition,
                    user_param=user_param,
                    start_date=month_start,
                    end_date=month_end,
                )
                total_pnl = _round_pnl(sum(float(row["pnl"] or 0.0) for row in normalized_rows))
                for row in normalized_rows:
                    day = int(str(row["date"]).split("-")[2])
                    items.append({"label": f"{target_month}-{day}", "pnl": row["pnl"]})
                period_base = self._resolve_period_start_base(
                    normalized_rows,
                    _fetch_prev_invest(month_start),
                )
                rate_base = period_base
                title = f"{target_year}年{target_month}月累计"

            elif time_type == "month":
                if not selectable_years:
                    period.update({"year": now.year})
                    return {
                        "items": [],
                        "total_pnl": 0.0,
                        "total_rate": 0.0,
                        "title": f"{now.year}年累计",
                        "period": period,
                        "selectable": selectable,
                    }

                target_year = year or (now.year if now.year in months_by_year else latest_year)
                period.update({"year": int(target_year)})

                if target_year not in months_by_year:
                    return {
                        "error": "Selected period has no snapshot data",
                        "code": "INVALID_CALENDAR_PERIOD",
                        "items": [],
                        "total_pnl": 0.0,
                        "total_rate": 0.0,
                        "title": f"{target_year}年累计",
                        "period": period,
                        "selectable": selectable,
                    }

                year_start = f"{target_year:04d}-01-01"
                year_end = today_str if target_year == now.year else f"{target_year:04d}-12-31"
                normalized_rows = self._build_effective_pnl_series(
                    cursor,
                    user_condition=user_condition,
                    user_param=user_param,
                    start_date=year_start,
                    end_date=year_end,
                )
                month_totals: Dict[int, float] = {}
                for row in normalized_rows:
                    m = int(str(row["date"]).split("-")[1])
                    month_totals[m] = _round_pnl(month_totals.get(m, 0.0) + float(row["pnl"] or 0.0))
                month_limit = now.month if target_year == now.year else 12

                for m in range(1, month_limit + 1):
                    pnl = float(month_totals.get(m, 0.0) or 0.0)
                    items.append({"label": f"{m}月", "pnl": pnl})
                    total_pnl = _round_pnl(total_pnl + pnl)
                period_base = self._resolve_period_start_base(
                    normalized_rows,
                    _fetch_prev_invest(year_start),
                )
                rate_base = period_base
                title = f"{target_year}年累计"

            elif time_type == "year":
                period = {"time_type": "year"}
                normalized_rows = self._build_effective_pnl_series(
                    cursor,
                    user_condition=user_condition,
                    user_param=user_param,
                    start_date="0001-01-01",
                    end_date=today_str,
                )
                if normalized_rows:
                    year_totals: Dict[int, float] = {}
                    for row in normalized_rows:
                        y = int(str(row["date"]).split("-")[0])
                        year_totals[y] = _round_pnl(year_totals.get(y, 0.0) + float(row["pnl"] or 0.0))
                    start_year = int(str(normalized_rows[0]["date"]).split("-")[0])
                    for y in range(start_year, now.year + 1):
                        pnl = float(year_totals.get(y, 0.0) or 0.0)
                        items.append({"label": str(y), "pnl": pnl})
                        total_pnl = _round_pnl(total_pnl + pnl)
                period_base = self._resolve_period_start_base(normalized_rows, 0.0)
                rate_base = period_base
                title = "总累计"
            else:
                return {
                    "error": "Invalid time type",
                    "code": "INVALID_CALENDAR_PERIOD",
                    "items": [],
                    "total_pnl": 0.0,
                    "total_rate": 0.0,
                    "title": "",
                    "period": period,
                    "selectable": selectable,
                }

            total_rate = round(total_pnl / rate_base * 100, 2) if rate_base else 0.0
            return {
                "items": items,
                "total_pnl": total_pnl,
                "total_rate": total_rate,
                "title": title,
                "period": period,
                "selectable": selectable,
            }

        except Exception as exc:
            logger.error("Failed to get calendar data: %s", exc)
            return {
                "items": [],
                "total_pnl": 0.0,
                "total_rate": 0.0,
                "title": "",
                "period": {"time_type": time_type},
                "selectable": {"day": {"years": [], "months_by_year": {}}, "month": {"years": []}},
            }
        finally:
            conn.close()

    def get_market_breakdown_calendar_data(
        self,
        time_type: str = "day",
        user_id: str = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
        ledger_id: int | None = None,
    ) -> Dict[str, Any]:
        """获取按市场拆分的收益日历数据。"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if time_type != "day":
            return {
                "error": "Invalid calendar type",
                "code": "INVALID_CALENDAR_PERIOD",
                "time_type": "day",
                "year": int(year or 0),
                "month": int(month or 0),
                "items": [],
            }

        user_condition = "user_id = ?" if user_id else "(user_id IS NULL OR user_id = '')"
        user_param = (user_id,) if user_id else ()
        use_ledger_tables = ledger_id is not None and bool(user_id)

        try:
            now = _get_datetime_now()
            if use_ledger_tables:
                cursor.execute(
                    """
                    SELECT date
                    FROM ledger_daily_snapshots
                    WHERE user_id = ? AND ledger_id = ?
                    ORDER BY date ASC
                    """,
                    (str(user_id or ""), int(ledger_id)),
                )
                all_dates = [str(row["date"]) for row in cursor.fetchall() if row["date"]]
            else:
                all_dates = self._fetch_all_calendar_dates(
                    cursor,
                    user_condition=user_condition,
                    user_param=user_param,
                )

            if not all_dates:
                return {
                    "time_type": "day",
                    "year": int(year or now.year),
                    "month": int(month or now.month),
                    "items": [],
                }

            months_by_year = _build_months_by_year(all_dates, now)

            selectable_years = sorted(months_by_year.keys())
            latest_year = selectable_years[-1]
            latest_month = max(months_by_year[latest_year])

            target_year = year
            target_month = month
            if target_year is None and target_month is None:
                if now.year in months_by_year and now.month in months_by_year[now.year]:
                    target_year = now.year
                    target_month = now.month
                else:
                    target_year = latest_year
                    target_month = latest_month
            else:
                if target_year is None:
                    target_year = now.year
                if target_month is None:
                    target_month = now.month

            if target_year not in months_by_year or target_month not in months_by_year[target_year]:
                return {
                    "error": "Selected period has no snapshot data",
                    "code": "INVALID_CALENDAR_PERIOD",
                    "time_type": "day",
                    "year": int(target_year),
                    "month": int(target_month),
                    "items": [],
                }

            month_start = f"{target_year:04d}-{target_month:02d}-01"
            if target_month == 12:
                next_month = dt.datetime(target_year + 1, 1, 1)
            else:
                next_month = dt.datetime(target_year, target_month + 1, 1)
            month_end = (next_month - timedelta(days=1)).strftime("%Y-%m-%d")
            if target_year == now.year and target_month == now.month:
                month_end = min(month_end, now.strftime("%Y-%m-%d"))

            if use_ledger_tables:
                cursor.execute(
                    """
                    SELECT date, day_pnl
                    FROM ledger_daily_snapshots
                    WHERE date >= ? AND date <= ? AND user_id = ? AND ledger_id = ?
                    ORDER BY date ASC
                    """,
                    (month_start, month_end, str(user_id or ""), int(ledger_id)),
                )
                effective_series = [
                    {"date": str(row["date"]), "pnl": _round_pnl(row["day_pnl"])}
                    for row in cursor.fetchall()
                ]
                cursor.execute(
                    """
                    SELECT date, market, day_pnl, source
                    FROM ledger_daily_snapshot_market_breakdowns
                    WHERE date >= ? AND date <= ? AND user_id = ? AND ledger_id = ?
                    ORDER BY date ASC
                    """,
                    (month_start, month_end, str(user_id or ""), int(ledger_id)),
                )
            else:
                effective_series = self._build_effective_pnl_series(
                    cursor,
                    user_condition=user_condition,
                    user_param=user_param,
                    start_date=month_start,
                    end_date=month_end,
                )
                cursor.execute(
                    f"""
                    SELECT date, market, day_pnl, source
                    FROM daily_snapshot_market_breakdowns
                    WHERE date >= ? AND date <= ? AND {user_condition}
                    ORDER BY date ASC
                    """,
                    (month_start, month_end) + user_param,
                )
            breakdown_rows = cursor.fetchall()

            by_date: Dict[str, Dict[str, Any]] = {}
            for row in breakdown_rows:
                d = str(row["date"])
                data = by_date.setdefault(
                    d,
                    {"markets": {m: None for m in MARKET_BREAKDOWN_MARKETS}, "sources": set()},
                )
                market = str(row["market"] or "").lower()
                if market not in data["markets"]:
                    continue
                data["markets"][market] = round(float(row["day_pnl"] or 0.0), 2)
                source = str(row["source"] or "").strip().lower() or "estimated"
                data["sources"].add(source)

            effective_total_by_date = {
                str(row["date"]): _round_pnl(row["pnl"])
                for row in effective_series
            }
            items: List[Dict[str, Any]] = []
            all_period_dates = sorted(set(effective_total_by_date.keys()) | set(by_date.keys()))
            for date_str in all_period_dates:
                day_total = effective_total_by_date.get(date_str, 0.0)
                breakdown = by_date.get(date_str)
                if not breakdown:
                    markets = {m: None for m in MARKET_BREAKDOWN_MARKETS}
                    source = "missing"
                else:
                    markets = {}
                    for market in MARKET_BREAKDOWN_MARKETS:
                        value = breakdown["markets"].get(market)
                        markets[market] = None if value is None else round(float(value), 2)
                    source_set = breakdown["sources"]
                    source = "exact" if source_set == {"exact"} else "estimated"
                items.append({"date": date_str, "markets": markets, "total_pnl": day_total, "source": source})

            return {
                "time_type": "day",
                "year": int(target_year),
                "month": int(target_month),
                "items": items,
            }
        except Exception as exc:
            logger.error("Failed to get market breakdown calendar data: %s", exc)
            return {"time_type": "day", "year": int(year or 0), "month": int(month or 0), "items": []}
        finally:
            conn.close()

    def get_rank_data(self, rank_type: str = "gain", market: str = "all", user_id: str = None, ledger_id: int | None = None) -> List[Dict[str, Any]]:
        """获取盈亏排行数据。"""
        conn = self.get_connection()
        cursor = conn.cursor()

        user_condition = "p.user_id = ?" if user_id else "(p.user_id IS NULL OR p.user_id = '')"
        user_param = (user_id,) if user_id else ()
        ledger_condition = " AND p.ledger_id = ?" if ledger_id is not None else ""
        ledger_param = (ledger_id,) if ledger_id is not None else ()

        try:
            if market == "all":
                cursor.execute(
                    f"""
                    SELECT p.code, p.name, p.qty, p.price, p.curr, p.adjustment, l.name as ledger_name 
                    FROM portfolio p LEFT JOIN investment_ledgers l ON p.ledger_id = l.id
                    WHERE {user_condition}{ledger_condition} AND p.qty > 0
                    """,
                    user_param + ledger_param,
                )
            elif market == "a":
                cursor.execute(
                    f"""
                    SELECT p.code, p.name, p.qty, p.price, p.curr, p.adjustment, l.name as ledger_name 
                    FROM portfolio p LEFT JOIN investment_ledgers l ON p.ledger_id = l.id
                    WHERE (p.code LIKE 'sh%' OR p.code LIKE 'sz%' OR p.code LIKE 'bj%') AND {user_condition}{ledger_condition} AND p.qty > 0
                    """,
                    user_param + ledger_param,
                )
            elif market == "us":
                cursor.execute(
                    f"""
                    SELECT p.code, p.name, p.qty, p.price, p.curr, p.adjustment, l.name as ledger_name 
                    FROM portfolio p LEFT JOIN investment_ledgers l ON p.ledger_id = l.id
                    WHERE p.code LIKE 'gb_%' AND {user_condition}{ledger_condition} AND p.qty > 0
                    """,
                    user_param + ledger_param,
                )
            elif market == "hk":
                cursor.execute(
                    f"""
                    SELECT p.code, p.name, p.qty, p.price, p.curr, p.adjustment, l.name as ledger_name 
                    FROM portfolio p LEFT JOIN investment_ledgers l ON p.ledger_id = l.id
                    WHERE p.code LIKE 'hk%' AND {user_condition}{ledger_condition} AND p.qty > 0
                    """,
                    user_param + ledger_param,
                )
            elif market == "fund":
                cursor.execute(
                    f"""
                    SELECT p.code, p.name, p.qty, p.price, p.curr, p.adjustment, l.name as ledger_name 
                    FROM portfolio p LEFT JOIN investment_ledgers l ON p.ledger_id = l.id
                    WHERE (p.code LIKE 'f_%' OR p.code LIKE 'ft_%') AND {user_condition}{ledger_condition} AND p.qty > 0
                    """,
                    user_param + ledger_param,
                )
            else:
                return []

            rows = cursor.fetchall()
            include_legacy_adjustment = True
            should_ignore_legacy = getattr(self, "_is_portfolio_legacy_adjustment_ignored", None)
            if callable(should_ignore_legacy):
                include_legacy_adjustment = not should_ignore_legacy(cursor, user_id)
            ledger_sums = {}
            realized_sums = {}
            fetch_ledger_sums = getattr(self, "_fetch_portfolio_adjustment_ledger_sums", None)
            if callable(fetch_ledger_sums):
                ledger_sums = fetch_ledger_sums(
                    cursor,
                    [row["code"] for row in rows],
                    user_id,
                    ledger_id=ledger_id,
                )
            fetch_realized_sums = getattr(self, "_fetch_portfolio_realized_pnl_sums", None)
            if callable(fetch_realized_sums):
                realized_sums = fetch_realized_sums(
                    cursor,
                    [row["code"] for row in rows],
                    user_id,
                    ledger_id=ledger_id,
                )

            data = []
            for row in rows:
                code = str(row["code"] or "")
                legacy_adjustment = (
                    float(row["adjustment"] or 0.0)
                    if include_legacy_adjustment
                    else 0.0
                )
                ledger_adjustment = float(ledger_sums.get(code, 0.0))
                realized_pnl_adjustment = float(realized_sums.get(code, 0.0))
                data.append(
                    {
                        "code": code,
                        "name": row["name"],
                        "qty": float(row["qty"]),
                        "cost_price": float(row["price"]),
                        "curr": row["curr"],
                        "adjustment": legacy_adjustment + ledger_adjustment + realized_pnl_adjustment,
                        "adjustment_total": legacy_adjustment + ledger_adjustment + realized_pnl_adjustment,
                        "legacy_adjustment": legacy_adjustment,
                        "ledger_adjustment": ledger_adjustment,
                        "realized_pnl_adjustment": realized_pnl_adjustment,
                        "legacy_adjustment_ignored": not include_legacy_adjustment,
                        "market": self._detect_market(code),
                        "ledger_name": row["ledger_name"] if row and "ledger_name" in row.keys() else None,
                    }
                )

            return data
        except Exception as exc:
            logger.error("Failed to get rank data: %s", exc)
            return []
        finally:
            conn.close()

    def _detect_market(self, code: str) -> str:
        if code.startswith("sh") or code.startswith("sz") or code.startswith("bj"):
            return "a"
        if code.startswith("hk"):
            return "hk"
        if code.startswith("gb_"):
            return "us"
        if code.startswith("f_") or code.startswith("ft_"):
            return "fund"
        return "other"
