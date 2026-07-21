"""场外基金历史净值对账的纯计算逻辑。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable


def round_amount(value: Any) -> float:
    try:
        return round(float(value or 0.0), 2)
    except (TypeError, ValueError):
        return 0.0


def nav_map_from_points(points: Iterable[Dict[str, Any]]) -> Dict[str, float]:
    """把公开历史净值标准化为日期到净值的映射。"""
    result: Dict[str, float] = {}
    for point in points or []:
        date_str = str((point or {}).get("date") or "").strip()[:10]
        try:
            # 净值通常有 3 到 4 位小数，不能像金额一样提前取两位。
            value = float((point or {}).get("value") or 0.0)
        except (TypeError, ValueError):
            value = 0.0
        if date_str and value > 0:
            result[date_str] = value
    return result


def previous_nav_date(nav_by_date: Dict[str, float], date_str: str) -> str | None:
    """返回目标日期之前最近一个已确认净值日。"""
    candidates = [item for item in nav_by_date if item < date_str and nav_by_date[item] > 0]
    return max(candidates) if candidates else None


@dataclass(frozen=True)
class FundNavRepair:
    date_str: str
    code: str
    name: str
    curr: str
    qty: float
    previous_nav: float
    current_nav: float
    fx_rate: float
    day_pnl: float
    day_base: float
    old_day_pnl: float | None
    old_day_base: float | None


def plan_fund_nav_repair(
    *,
    date_str: str,
    code: str,
    name: str,
    curr: str,
    qty: float,
    nav_by_date: Dict[str, float],
    fx_rate: float,
    existing: Dict[str, Any] | None,
) -> FundNavRepair | None:
    """仅在已拿到相邻两个确认净值、且结果需要修复时生成计划。"""
    try:
        current_nav = float(nav_by_date.get(date_str) or 0.0)
    except (TypeError, ValueError):
        current_nav = 0.0
    previous_date = previous_nav_date(nav_by_date, date_str)
    try:
        previous_nav = float(nav_by_date.get(previous_date) or 0.0) if previous_date else 0.0
    except (TypeError, ValueError):
        previous_nav = 0.0
    normalized_qty = float(qty or 0.0)
    normalized_fx = float(fx_rate or 0.0)
    if current_nav <= 0 or previous_nav <= 0 or normalized_qty <= 0 or normalized_fx <= 0:
        return None

    day_pnl = round_amount((current_nav - previous_nav) * normalized_qty * normalized_fx)
    day_base = round_amount(previous_nav * normalized_qty * normalized_fx)
    old_day_pnl = round_amount(existing.get("day_pnl")) if existing else None
    old_day_base = round_amount(existing.get("day_base")) if existing else None

    # 没有明细行时，连零收益也要落一行，页面才能明确展示为 0 而不是“漏了”。
    if existing and abs(old_day_pnl - day_pnl) < 0.01 and abs(old_day_base - day_base) < 0.01:
        return None

    return FundNavRepair(
        date_str=date_str,
        code=str(code or ""),
        name=str(name or code or ""),
        curr=str(curr or "CNY").upper(),
        qty=normalized_qty,
        previous_nav=previous_nav,
        current_nav=current_nav,
        fx_rate=normalized_fx,
        day_pnl=day_pnl,
        day_base=day_base,
        old_day_pnl=old_day_pnl,
        old_day_base=old_day_base,
    )
