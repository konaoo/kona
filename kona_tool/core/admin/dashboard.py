"""
管理后台概览 / 用户统计 / 用户持仓 helper。
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List

from core.admin.common import has_local_anonymous_user, iso_utc, real_user_where, to_cny
from core.admin.constants import ADMIN_PORTFOLIO_CACHE_TTL_SECONDS
from core.asset_type import asset_type_label
from core.price import batch_get_prices, get_forex_rates
from core.utils import safe_float


def get_user_ops_metrics(cursor) -> Dict[str, Any]:
    now_local = datetime.now()
    today_start = datetime(now_local.year, now_local.month, now_local.day, 0, 0, 0)
    tomorrow_start = today_start + timedelta(days=1)
    start_7d = today_start - timedelta(days=6)
    start_30d = today_start - timedelta(days=29)
    cutoff_1d = now_local - timedelta(days=1)
    cutoff_7d = now_local - timedelta(days=7)
    cutoff_30d = now_local - timedelta(days=30)

    cursor.execute(
        f"""
        SELECT
            COUNT(*) AS user_total,
            SUM(CASE WHEN COALESCE(u.created_at, '') >= ? AND COALESCE(u.created_at, '') < ? THEN 1 ELSE 0 END) AS new_today,
            SUM(CASE WHEN COALESCE(u.created_at, '') >= ? AND COALESCE(u.created_at, '') < ? THEN 1 ELSE 0 END) AS new_7d,
            SUM(CASE WHEN COALESCE(u.created_at, '') >= ? AND COALESCE(u.created_at, '') < ? THEN 1 ELSE 0 END) AS new_30d,
            SUM(CASE WHEN u.last_active_at IS NULL OR TRIM(u.last_active_at) = '' THEN 1 ELSE 0 END) AS never_login,
            SUM(CASE WHEN u.last_active_at IS NOT NULL AND TRIM(u.last_active_at) != '' AND u.last_active_at >= ? THEN 1 ELSE 0 END) AS within_1d,
            SUM(CASE WHEN u.last_active_at IS NOT NULL AND TRIM(u.last_active_at) != '' AND u.last_active_at < ? AND u.last_active_at >= ? THEN 1 ELSE 0 END) AS within_7d,
            SUM(CASE WHEN u.last_active_at IS NOT NULL AND TRIM(u.last_active_at) != '' AND u.last_active_at < ? AND u.last_active_at >= ? THEN 1 ELSE 0 END) AS within_30d,
            SUM(CASE WHEN u.last_active_at IS NOT NULL AND TRIM(u.last_active_at) != '' AND u.last_active_at < ? THEN 1 ELSE 0 END) AS over_30d
        FROM users u
        WHERE {real_user_where('u')}
        """,
        (
            today_start.strftime("%Y-%m-%d %H:%M:%S"),
            tomorrow_start.strftime("%Y-%m-%d %H:%M:%S"),
            start_7d.strftime("%Y-%m-%d %H:%M:%S"),
            tomorrow_start.strftime("%Y-%m-%d %H:%M:%S"),
            start_30d.strftime("%Y-%m-%d %H:%M:%S"),
            tomorrow_start.strftime("%Y-%m-%d %H:%M:%S"),
            cutoff_1d.strftime("%Y-%m-%d %H:%M:%S"),
            cutoff_1d.strftime("%Y-%m-%d %H:%M:%S"),
            cutoff_7d.strftime("%Y-%m-%d %H:%M:%S"),
            cutoff_7d.strftime("%Y-%m-%d %H:%M:%S"),
            cutoff_30d.strftime("%Y-%m-%d %H:%M:%S"),
            cutoff_30d.strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    row = cursor.fetchone() or {}
    cursor.execute(
        f"""
        SELECT
            SUM(CASE WHEN uda.activity_date = ? THEN 1 ELSE 0 END) AS dau,
            SUM(CASE WHEN uda.activity_date >= ? AND uda.activity_date <= ? THEN 1 ELSE 0 END) AS wau,
            SUM(CASE WHEN uda.activity_date >= ? AND uda.activity_date <= ? THEN 1 ELSE 0 END) AS mau
        FROM (
            SELECT DISTINCT uda.user_id, uda.activity_date
            FROM user_daily_activity uda
            INNER JOIN users u ON u.id = uda.user_id
            WHERE {real_user_where('u')}
              AND uda.activity_date >= ?
              AND uda.activity_date <= ?
        ) uda
        """,
        (
            today_start.strftime("%Y-%m-%d"),
            start_7d.strftime("%Y-%m-%d"),
            today_start.strftime("%Y-%m-%d"),
            start_30d.strftime("%Y-%m-%d"),
            today_start.strftime("%Y-%m-%d"),
            start_30d.strftime("%Y-%m-%d"),
            today_start.strftime("%Y-%m-%d"),
        ),
    )
    active_row = cursor.fetchone() or {}
    metrics = {
        "user_total": int(row["user_total"] or 0),
        "new_today": int(row["new_today"] or 0),
        "new_7d": int(row["new_7d"] or 0),
        "new_30d": int(row["new_30d"] or 0),
        "dau": int(active_row["dau"] or 0),
        "wau": int(active_row["wau"] or 0),
        "mau": int(active_row["mau"] or 0),
        "last_login_distribution": {
            "within_1d": int(row["within_1d"] or 0),
            "within_7d": int(row["within_7d"] or 0),
            "within_30d": int(row["within_30d"] or 0),
            "over_30d": int(row["over_30d"] or 0),
            "never_login": int(row["never_login"] or 0),
        },
    }
    if has_local_anonymous_user(cursor):
        metrics["user_total"] += 1
        metrics["last_login_distribution"]["never_login"] += 1
    return metrics


def get_user_retention_rows(cursor, days: int = 60) -> List[Dict[str, Any]]:
    window_days = max(1, int(days))
    today_local = datetime.now()
    today_start = datetime(today_local.year, today_local.month, today_local.day, 0, 0, 0)
    tomorrow_start = today_start + timedelta(days=1)
    start_day = today_start - timedelta(days=window_days - 1)

    cursor.execute(
        f"""
        SELECT
            SUBSTR(u.created_at, 1, 10) AS cohort_date,
            COUNT(*) AS new_users,
            SUM(
                CASE
                    WHEN EXISTS(
                        SELECT 1
                        FROM user_daily_activity uda
                        WHERE uda.user_id = u.id
                          AND uda.activity_date = DATE(SUBSTR(u.created_at, 1, 10), '+1 day')
                    )
                    THEN 1 ELSE 0
                END
            ) AS retained_1d_count,
            SUM(
                CASE
                    WHEN EXISTS(
                        SELECT 1
                        FROM user_daily_activity uda
                        WHERE uda.user_id = u.id
                          AND uda.activity_date = DATE(SUBSTR(u.created_at, 1, 10), '+3 day')
                    )
                    THEN 1 ELSE 0
                END
            ) AS retained_3d_count,
            SUM(
                CASE
                    WHEN EXISTS(
                        SELECT 1
                        FROM user_daily_activity uda
                        WHERE uda.user_id = u.id
                          AND uda.activity_date = DATE(SUBSTR(u.created_at, 1, 10), '+7 day')
                    )
                    THEN 1 ELSE 0
                END
            ) AS retained_7d_count,
            SUM(
                CASE
                    WHEN EXISTS(
                        SELECT 1
                        FROM user_daily_activity uda
                        WHERE uda.user_id = u.id
                          AND uda.activity_date = DATE(SUBSTR(u.created_at, 1, 10), '+14 day')
                    )
                    THEN 1 ELSE 0
                END
            ) AS retained_14d_count,
            SUM(
                CASE
                    WHEN EXISTS(
                        SELECT 1
                        FROM user_daily_activity uda
                        WHERE uda.user_id = u.id
                          AND uda.activity_date = DATE(SUBSTR(u.created_at, 1, 10), '+30 day')
                    )
                    THEN 1 ELSE 0
                END
            ) AS retained_30d_count
        FROM users u
        WHERE {real_user_where('u')}
          AND COALESCE(u.created_at, '') >= ?
          AND COALESCE(u.created_at, '') < ?
        GROUP BY SUBSTR(u.created_at, 1, 10)
        """,
        (
            start_day.strftime("%Y-%m-%d %H:%M:%S"),
            tomorrow_start.strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    cohort_rows = cursor.fetchall()

    cohort_map: Dict[str, Dict[str, int]] = {}
    for row in cohort_rows:
        cohort_date = str((row["cohort_date"] if row else "") or "")
        if not cohort_date:
            continue
        cohort_map[cohort_date] = {
            "new_users": int(row["new_users"] or 0),
            "retained_1d_count": int(row["retained_1d_count"] or 0),
            "retained_3d_count": int(row["retained_3d_count"] or 0),
            "retained_7d_count": int(row["retained_7d_count"] or 0),
            "retained_14d_count": int(row["retained_14d_count"] or 0),
            "retained_30d_count": int(row["retained_30d_count"] or 0),
        }

    cursor.execute(
        f"""
        SELECT
            uda.activity_date AS active_date,
            COUNT(DISTINCT uda.user_id) AS active_users
        FROM user_daily_activity uda
        INNER JOIN users u ON u.id = uda.user_id
        WHERE {real_user_where('u')}
          AND uda.activity_date >= ?
          AND uda.activity_date <= ?
        GROUP BY uda.activity_date
        """,
        (
            start_day.strftime("%Y-%m-%d"),
            today_start.strftime("%Y-%m-%d"),
        ),
    )
    active_rows = cursor.fetchall()
    active_map = {
        str((row["active_date"] if row else "") or ""): int(row["active_users"] or 0)
        for row in active_rows
        if str((row["active_date"] if row else "") or "")
    }

    cursor.execute(
        f"""
        SELECT
            uda.activity_date AS cohort_date,
            COUNT(DISTINCT uda.user_id) AS active_users,
            COUNT(
                DISTINCT CASE
                    WHEN EXISTS(
                        SELECT 1
                        FROM user_daily_activity next_uda
                        WHERE next_uda.user_id = uda.user_id
                          AND next_uda.activity_date = DATE(uda.activity_date, '+1 day')
                    ) THEN uda.user_id
                END
            ) AS retained_1d_count,
            COUNT(
                DISTINCT CASE
                    WHEN EXISTS(
                        SELECT 1
                        FROM user_daily_activity next_uda
                        WHERE next_uda.user_id = uda.user_id
                          AND next_uda.activity_date = DATE(uda.activity_date, '+3 day')
                    ) THEN uda.user_id
                END
            ) AS retained_3d_count,
            COUNT(
                DISTINCT CASE
                    WHEN EXISTS(
                        SELECT 1
                        FROM user_daily_activity next_uda
                        WHERE next_uda.user_id = uda.user_id
                          AND next_uda.activity_date = DATE(uda.activity_date, '+7 day')
                    ) THEN uda.user_id
                END
            ) AS retained_7d_count,
            COUNT(
                DISTINCT CASE
                    WHEN EXISTS(
                        SELECT 1
                        FROM user_daily_activity next_uda
                        WHERE next_uda.user_id = uda.user_id
                          AND next_uda.activity_date = DATE(uda.activity_date, '+14 day')
                    ) THEN uda.user_id
                END
            ) AS retained_14d_count
        FROM user_daily_activity uda
        INNER JOIN users u ON u.id = uda.user_id
        WHERE {real_user_where('u')}
          AND uda.activity_date >= ?
          AND uda.activity_date <= ?
        GROUP BY uda.activity_date
        """,
        (
            start_day.strftime("%Y-%m-%d"),
            today_start.strftime("%Y-%m-%d"),
        ),
    )
    active_cohort_rows = cursor.fetchall()
    active_cohort_map: Dict[str, Dict[str, int]] = {}
    for row in active_cohort_rows:
        cohort_date = str((row["cohort_date"] if row else "") or "")
        if not cohort_date:
            continue
        active_cohort_map[cohort_date] = {
            "active_users": int(row["active_users"] or 0),
            "retained_1d_count": int(row["retained_1d_count"] or 0),
            "retained_3d_count": int(row["retained_3d_count"] or 0),
            "retained_7d_count": int(row["retained_7d_count"] or 0),
            "retained_14d_count": int(row["retained_14d_count"] or 0),
        }

    def _safe_rate(retained: int, new_users: int, age_days: int, threshold: int):
        if new_users <= 0 or age_days < threshold:
            return None
        return round(retained / new_users, 4)

    def _safe_active_rate(retained: int, active_users: int, age_days: int, threshold: int):
        if active_users <= 0 or age_days < threshold:
            return None
        return round(retained / active_users, 4)

    today = date.today()
    result: List[Dict[str, Any]] = []
    for i in range(window_days):
        current = today - timedelta(days=i)
        date_str = current.isoformat()
        cohort = cohort_map.get(date_str, {})
        active_cohort = active_cohort_map.get(date_str, {})
        new_users = int(cohort.get("new_users", 0) or 0)
        active_users = int(active_map.get(date_str, 0) or 0)
        age_days = i
        result.append(
            {
                "date": date_str,
                "new_users": new_users,
                "active_users": active_users,
                "retention_1d": _safe_rate(int(cohort.get("retained_1d_count", 0) or 0), new_users, age_days, 1),
                "retention_3d": _safe_rate(int(cohort.get("retained_3d_count", 0) or 0), new_users, age_days, 3),
                "retention_7d": _safe_rate(int(cohort.get("retained_7d_count", 0) or 0), new_users, age_days, 7),
                "retention_14d": _safe_rate(int(cohort.get("retained_14d_count", 0) or 0), new_users, age_days, 14),
                "retention_30d": _safe_rate(int(cohort.get("retained_30d_count", 0) or 0), new_users, age_days, 30),
                "active_retention_1d": _safe_active_rate(int(active_cohort.get("retained_1d_count", 0) or 0), active_users, age_days, 1),
                "active_retention_3d": _safe_active_rate(int(active_cohort.get("retained_3d_count", 0) or 0), active_users, age_days, 3),
                "active_retention_7d": _safe_active_rate(int(active_cohort.get("retained_7d_count", 0) or 0), active_users, age_days, 7),
                "active_retention_14d": _safe_active_rate(int(active_cohort.get("retained_14d_count", 0) or 0), active_users, age_days, 14),
            }
        )
    return result


def sort_retention_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(rows, key=lambda item: str(item.get("date") or ""))


def build_mini_bars(
    rows: List[Dict[str, Any]],
    key: str,
    *,
    points: int = 7,
    min_height: int = 24,
) -> List[Dict[str, Any]]:
    series = sort_retention_rows(rows)
    if points > 0:
        series = series[-points:]

    values = [int(item.get(key) or 0) for item in series]
    max_value = max(values) if values else 1
    max_value = max(max_value, 1)

    bars: List[Dict[str, Any]] = []
    for idx, item in enumerate(series):
        value = int(item.get(key) or 0)
        height_pct = max(min_height, round((value / max_value) * 100))
        bars.append(
            {
                "date": str(item.get("date") or ""),
                "value": value,
                "height": f"{height_pct}%",
                "is_latest": idx == len(series) - 1,
            }
        )
    return bars


def build_trend_text(
    rows: List[Dict[str, Any]],
    key: str,
    *,
    unit: str,
    empty_text: str,
    single_text: str,
) -> str:
    series = sort_retention_rows(rows)
    if not series:
        return empty_text
    if len(series) == 1:
        return single_text
    current = int(series[-1].get(key) or 0)
    previous = int(series[-2].get(key) or 0)
    diff = current - previous
    if diff == 0:
        return "较昨日持平"
    return f"较昨日 +{diff}{unit}" if diff > 0 else f"较昨日 {diff}{unit}"


def recent_admin_audits(cursor, limit: int = 20) -> List[Dict[str, Any]]:
    cursor.execute(
        """
        SELECT
            a.id,
            a.admin_user_id,
            COALESCE(u.username, '') AS admin_username,
            a.action,
            a.target_type,
            a.target_id,
            a.method,
            a.path,
            a.status_code,
            a.result,
            a.error,
            a.created_at
        FROM admin_audit_logs a
        LEFT JOIN users u ON u.id = a.admin_user_id
        ORDER BY a.id DESC
        LIMIT ?
        """,
        (limit,),
    )
    return [dict(row) for row in cursor.fetchall()]


def get_active_session_count(cursor, user_id: str) -> int:
    cursor.execute(
        """
        SELECT COUNT(1) AS c
        FROM auth_refresh_tokens
        WHERE user_id = ?
          AND revoked_at IS NULL
          AND DATETIME(expires_at) > DATETIME('now')
        """,
        (user_id,),
    )
    row = cursor.fetchone()
    return int((row["c"] if row else 0) or 0)


def build_admin_portfolio_payload(db, user_id: str) -> Dict[str, Any]:
    portfolio = db.get_portfolio("all", user_id)
    cash_assets = db.get_cash_assets(user_id)
    other_assets = db.get_other_assets(user_id)
    liabilities = db.get_liabilities(user_id)
    rates = get_forex_rates() or {}

    codes = [str(item.get("code", "")).strip() for item in portfolio if str(item.get("code", "")).strip()]
    latest_prices = batch_get_prices(codes) if codes else {}

    items: List[Dict[str, Any]] = []
    for item in portfolio:
        code = str(item.get("code", ""))
        name = str(item.get("name", ""))
        qty = float(item.get("qty") or 0.0)
        cost_price = float(item.get("price") or 0.0)
        adjustment = float(item.get("adjustment") or 0.0)
        curr = str(item.get("curr", "") or "CNY")
        asset_type = str(item.get("asset_type", "") or "a")

        latest = latest_prices.get(code, (0, 0, 0, 0))
        latest_price = safe_float(latest[0] if isinstance(latest, tuple) and len(latest) > 0 else 0)
        yclose = safe_float(latest[1] if isinstance(latest, tuple) and len(latest) > 1 else 0)
        if latest_price > 0:
            effective_price = latest_price
        elif yclose > 0:
            effective_price = yclose
        elif cost_price > 0:
            effective_price = cost_price
        else:
            effective_price = 0.0

        cost_amount = cost_price * qty
        current_amount = effective_price * qty
        pnl_amount = current_amount - cost_amount + adjustment
        cost_amount_abs = abs(cost_amount)
        pnl_rate = (pnl_amount / cost_amount_abs * 100.0) if cost_amount_abs > 0 else 0.0

        items.append(
            {
                "code": code,
                "name": name,
                "qty": qty,
                "price": cost_price,
                "curr": curr,
                "asset_type": asset_type,
                "latest_price": round(float(effective_price), 6),
                "pnl_cny": round(float(to_cny(pnl_amount, curr, rates)), 2),
                "pnl_rate": round(float(pnl_rate), 4),
                "type_label": asset_type_label(asset_type),
            }
        )

    cash_cny = round(sum(to_cny(item.get("amount", 0), item.get("curr", "CNY"), rates) for item in cash_assets), 2)
    other_cny = round(sum(to_cny(item.get("amount", 0), item.get("curr", "CNY"), rates) for item in other_assets), 2)
    liability_cny = round(sum(to_cny(item.get("amount", 0), item.get("curr", "CNY"), rates) for item in liabilities), 2)

    now_utc = datetime.now(timezone.utc)
    expires_utc = now_utc + timedelta(seconds=ADMIN_PORTFOLIO_CACHE_TTL_SECONDS)
    cached_at = iso_utc(now_utc)
    expires_at = iso_utc(expires_utc)
    return {
        "user_id": user_id,
        "total": len(items),
        "summary": {
            "cash_cny": cash_cny,
            "other_cny": other_cny,
            "liability_cny": liability_cny,
            "as_of": cached_at,
        },
        "items": items,
        "cache": {
            "cached_at": cached_at,
            "expires_at": expires_at,
        },
    }
