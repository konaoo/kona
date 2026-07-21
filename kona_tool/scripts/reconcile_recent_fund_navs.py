#!/usr/bin/env python3
"""回扫最近场外基金确认净值，只补漏行或错误明细。默认只检查。"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.db import DatabaseManager
from core.fund_nav_reconcile import FundNavRepair, nav_map_from_points, plan_fund_nav_repair, round_amount
from core.price import is_exchange_fund_code
from core.trend import get_asset_trend


SOURCE = "fund_nav_reconcile"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="回扫最近场外基金确认净值，默认只检查")
    parser.add_argument("--days", type=int, default=7, help="回扫最近已结束的自然日，默认 7")
    parser.add_argument("--apply", action="store_true", help="确认写入修复结果")
    parser.add_argument("--db-path", default=str(ROOT / "portfolio.db"), help="数据库路径")
    parser.add_argument("--user-id", default="", help="只处理指定用户")
    parser.add_argument("--ledger-id", type=int, help="只处理指定账本")
    return parser.parse_args()


def iter_dates(days: int) -> Iterable[str]:
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=max(1, int(days)) - 1)
    current = start
    while current <= end:
        yield current.isoformat()
        current += timedelta(days=1)


def load_ledgers_with_snapshots(
    db: DatabaseManager,
    *,
    start_date: str,
    end_date: str,
    user_id: str = "",
    ledger_id: int | None = None,
) -> list[tuple[str, int]]:
    conn = db.get_connection()
    try:
        where = ["s.date BETWEEN ? AND ?"]
        values: list[Any] = [start_date, end_date]
        if user_id:
            where.append("s.user_id = ?")
            values.append(user_id)
        if ledger_id is not None:
            where.append("s.ledger_id = ?")
            values.append(int(ledger_id))
        rows = conn.execute(
            "SELECT DISTINCT s.user_id, s.ledger_id FROM ledger_daily_snapshots s WHERE " + " AND ".join(where),
            values,
        ).fetchall()
        return [(str(row["user_id"]), int(row["ledger_id"])) for row in rows]
    finally:
        conn.close()


def load_fund_assets(
    db: DatabaseManager,
    *,
    user_id: str,
    ledger_id: int,
    start_date: str,
    end_date: str,
) -> Dict[str, Dict[str, str]]:
    """当前仍持有的基金 + 期间曾有快照的基金，避免漏掉刚卖出的历史数据。"""
    assets: Dict[str, Dict[str, str]] = {}
    for item in db.get_portfolio(user_id=user_id, ledger_id=ledger_id, include_closed=True):
        code = str(item.get("code") or "").strip()
        if _is_otc_fund(code):
            assets[code] = {"name": str(item.get("name") or code), "curr": str(item.get("curr") or "CNY").upper()}

    conn = db.get_connection()
    try:
        rows = conn.execute(
            """
            SELECT DISTINCT code, name, curr
            FROM ledger_daily_snapshot_asset_breakdowns
            WHERE user_id = ? AND ledger_id = ? AND date BETWEEN ? AND ? AND market = 'fund'
            """,
            (user_id, ledger_id, start_date, end_date),
        ).fetchall()
        for row in rows:
            code = str(row["code"] or "").strip()
            if _is_otc_fund(code):
                assets.setdefault(code, {"name": str(row["name"] or code), "curr": str(row["curr"] or "CNY").upper()})
    finally:
        conn.close()
    return assets


def _is_otc_fund(code: str) -> bool:
    normalized = str(code or "").strip().lower()
    return normalized.startswith(("f_", "ft_")) and not is_exchange_fund_code(normalized)


def load_existing_rows(db: DatabaseManager, *, user_id: str, ledger_id: int, date_str: str) -> Dict[str, Dict[str, Any]]:
    return {row["code"]: row for row in db.get_daily_snapshot_asset_breakdown_rows(date_str=date_str, user_id=user_id, ledger_id=ledger_id)}


def derive_historical_fx(
    *,
    db: DatabaseManager,
    user_id: str,
    ledger_id: int,
    code: str,
    curr: str,
    nav_by_date: Dict[str, float],
    target_date: str,
) -> float:
    """非人民币基金只从已保存的历史日基数倒推汇率，取不到就跳过，绝不猜。"""
    if str(curr or "CNY").upper() == "CNY":
        return 1.0
    conn = db.get_connection()
    try:
        rows = conn.execute(
            """
            SELECT date, day_base FROM ledger_daily_snapshot_asset_breakdowns
            WHERE user_id = ? AND ledger_id = ? AND code = ? AND day_base > 0
            ORDER BY ABS(julianday(date) - julianday(?)) ASC
            LIMIT 14
            """,
            (user_id, ledger_id, code, target_date),
        ).fetchall()
    finally:
        conn.close()

    for row in rows:
        row_date = str(row["date"] or "")
        previous_dates = [item for item in nav_by_date if item < row_date]
        if not previous_dates:
            continue
        qty = db.get_position_qty_as_of_effective_date(code, row_date, user_id=user_id, ledger_id=ledger_id)
        previous_nav = nav_by_date[max(previous_dates)]
        base = float(row["day_base"] or 0.0)
        if qty > 0 and previous_nav > 0 and base > 0:
            rate = base / (previous_nav * qty)
            if 0.01 < rate < 100:
                return rate
    return 0.0


def build_repairs(
    db: DatabaseManager,
    *,
    days: int,
    user_id: str = "",
    ledger_id: int | None = None,
) -> tuple[list[tuple[str, int, FundNavRepair]], list[str]]:
    dates = list(iter_dates(days))
    start_date, end_date = dates[0], dates[-1]
    repairs: list[tuple[str, int, FundNavRepair]] = []
    warnings: list[str] = []
    for uid, lid in load_ledgers_with_snapshots(db, start_date=start_date, end_date=end_date, user_id=user_id, ledger_id=ledger_id):
        assets = load_fund_assets(db, user_id=uid, ledger_id=lid, start_date=start_date, end_date=end_date)
        for code, asset in assets.items():
            history = nav_map_from_points(get_asset_trend(code, asset["name"], points=60, market_hint="fund").get("points") or [])
            if len(history) < 2:
                warnings.append(f"{uid}/{lid} {code}: 未拿到至少两个确认净值，跳过")
                continue
            for date_str in dates:
                existing = load_existing_rows(db, user_id=uid, ledger_id=lid, date_str=date_str).get(code)
                qty = db.get_position_qty_as_of_effective_date(code, date_str, user_id=uid, ledger_id=lid)
                fx_rate = derive_historical_fx(
                    db=db, user_id=uid, ledger_id=lid, code=code, curr=asset["curr"], nav_by_date=history, target_date=date_str
                )
                repair = plan_fund_nav_repair(
                    date_str=date_str, code=code, name=asset["name"], curr=asset["curr"], qty=qty,
                    nav_by_date=history, fx_rate=fx_rate, existing=existing,
                )
                if repair:
                    repairs.append((uid, lid, repair))
    return repairs, warnings


def backup_database(db_path: str) -> Path:
    source_path = Path(db_path).resolve()
    backup_dir = source_path.parent.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    target = backup_dir / f"portfolio-before-fund-nav-reconcile-{datetime.now().strftime('%Y%m%d-%H%M%S')}.db"
    source = sqlite3.connect(source_path)
    destination = sqlite3.connect(target)
    try:
        source.backup(destination)
    finally:
        destination.close()
        source.close()
    return target


def apply_repairs(db: DatabaseManager, repairs: list[tuple[str, int, FundNavRepair]]) -> None:
    changed_user_dates: set[tuple[str, str]] = set()
    market_deltas: Dict[tuple[str, int, str], float] = defaultdict(float)
    for uid, lid, repair in repairs:
        if not db.save_daily_snapshot_asset_breakdowns(
            date_str=repair.date_str,
            items=[{
                "code": repair.code, "name": repair.name, "market": "fund", "curr": repair.curr,
                "day_pnl": repair.day_pnl, "day_base": repair.day_base,
            }],
            user_id=uid, ledger_id=lid, snapshot_date=repair.date_str,
            source=SOURCE, confidence=1.0, replace_existing=False,
        ):
            raise RuntimeError(f"资产明细写入失败: {uid}/{lid}/{repair.date_str}/{repair.code}")
        old = repair.old_day_pnl if repair.old_day_pnl is not None else 0.0
        market_deltas[(uid, lid, repair.date_str)] += repair.day_pnl - old
        changed_user_dates.add((uid, repair.date_str))

    for (uid, lid, date_str), delta in market_deltas.items():
        current = db.get_daily_snapshot_market_breakdown_map(date_str, user_id=uid, ledger_id=lid)
        new_fund = round_amount(current.get("fund", 0.0) + delta)
        if not db.save_daily_snapshot_market_breakdown_row(
            date_str=date_str, market="fund", day_pnl=new_fund, user_id=uid, ledger_id=lid,
            snapshot_date=date_str, source=SOURCE, confidence=1.0,
        ):
            raise RuntimeError(f"基金市场汇总写入失败: {uid}/{lid}/{date_str}")
        if not db.sync_ledger_daily_snapshot_day_pnl_from_breakdown(date_str, user_id=uid, ledger_id=lid):
            raise RuntimeError(f"账本日收益同步失败: {uid}/{lid}/{date_str}")

    for uid, date_str in sorted(changed_user_dates):
        if not db.aggregate_daily_snapshot_market_breakdown_from_ledgers(user_id=uid, date_str=date_str, snapshot_date=date_str, source=SOURCE):
            raise RuntimeError(f"全局市场汇总失败: {uid}/{date_str}")
        if not db.aggregate_daily_snapshot_asset_breakdown_from_ledgers(user_id=uid, date_str=date_str, snapshot_date=date_str, source=SOURCE):
            raise RuntimeError(f"全局资产汇总失败: {uid}/{date_str}")
        if not db.sync_daily_snapshot_day_pnl_from_breakdown(date_str, user_id=uid):
            raise RuntimeError(f"全局日收益同步失败: {uid}/{date_str}")


def main() -> int:
    args = parse_args()
    db = DatabaseManager(args.db_path)
    repairs, warnings = build_repairs(db, days=args.days, user_id=args.user_id, ledger_id=args.ledger_id)
    for warning in warnings:
        print(f"跳过: {warning}")
    print(f"检查完成: 候选修复 {len(repairs)} 条，模式={'写入' if args.apply else '只检查'}")
    for uid, lid, repair in repairs:
        old = "缺失" if repair.old_day_pnl is None else f"{repair.old_day_pnl:+.2f}"
        print(f"{repair.date_str} {uid}/{lid} {repair.code}: {old} -> {repair.day_pnl:+.2f}")
    if not args.apply or not repairs:
        return 0
    backup = backup_database(args.db_path)
    print(f"已创建写前备份: {backup}")
    apply_repairs(db, repairs)
    print(f"已写入 {len(repairs)} 条基金历史净值修复")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
