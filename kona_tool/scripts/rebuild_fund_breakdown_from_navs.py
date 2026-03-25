#!/usr/bin/env python3
"""
按历史净值重建指定用户的 fund 分市场收益。

这个脚本的目标很克制：
1. 只重建 fund 市场；
2. 不碰 A/HK/US；
3. 默认只改 fund 行；
4. 可选同步 daily_snapshots / ledger_daily_snapshots 的 day_pnl。

适用场景：
- 已确认场外基金 / 海外基金历史净值可信；
- 已知 fund 分市场被 repair / manual_restore 之类的临时脚本写偏；
- 需要用更可信的历史净值重建 fund 桶。

JSON 结构示例：
{
  "funds": {
    "f_110018": {
      "currency": "CNY",
      "navs": {
        "2026-03-02": 1.392,
        "2026-03-03": 1.389
      }
    },
    "ft_LU1116320737": {
      "currency": "USD",
      "navs": {
        "2026-03-02": 9.52,
        "2026-03-03": 9.30
      }
    }
  },
  "fx": {
    "USD": {
      "2026-03-03": 7.24
    }
  }
}
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("JWT_SECRET", "rebuild_fund_breakdown_from_navs_temp_secret")

import app as app_module


@dataclass
class FundNavConfig:
    code: str
    currency: str
    navs: Dict[str, float]


def _normalize_nav_map(raw: Any) -> Dict[str, float]:
    navs: Dict[str, float] = {}
    if not isinstance(raw, dict):
        return navs
    for date_str, value in raw.items():
        date_key = str(date_str or "").strip()
        if not date_key:
            continue
        try:
            nav = float(value)
        except Exception:
            continue
        if nav <= 0:
            continue
        navs[date_key] = nav
    return navs


def _load_nav_payload(path: Path) -> Tuple[List[FundNavConfig], Dict[str, Dict[str, float]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("funds"), dict):
        funds_raw = payload.get("funds") or {}
        fx_raw = payload.get("fx") or {}
    else:
        funds_raw = payload or {}
        fx_raw = {}

    funds: List[FundNavConfig] = []
    for code, item in funds_raw.items():
        code_str = str(code or "").strip()
        if not code_str:
            continue
        if isinstance(item, dict) and "navs" in item:
            navs = _normalize_nav_map(item.get("navs"))
            currency = str(item.get("currency") or "").strip().upper()
        else:
            navs = _normalize_nav_map(item)
            currency = ""
        if not navs:
            continue
        funds.append(FundNavConfig(code=code_str, currency=currency, navs=navs))

    fx_map: Dict[str, Dict[str, float]] = {}
    if isinstance(fx_raw, dict):
        for currency, item in fx_raw.items():
            currency_key = str(currency or "").strip().upper()
            if not currency_key:
                continue
            fx_map[currency_key] = _normalize_nav_map(item)
    return funds, fx_map


def _load_positions(user_id: str, ledger_id: int | None) -> Dict[str, Dict[str, Any]]:
    conn = app_module.db.get_connection()
    cursor = conn.cursor()
    try:
        sql = """
            SELECT code, name, qty, curr, asset_type, ledger_id
            FROM portfolio
            WHERE COALESCE(user_id,'') = ?
        """
        params: List[Any] = [str(user_id or "")]
        if ledger_id is not None:
            sql += " AND ledger_id = ?"
            params.append(int(ledger_id))
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        result: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            result[str(row["code"] or "").strip()] = {
                "name": str(row["name"] or "").strip(),
                "qty": float(row["qty"] or 0.0),
                "curr": str(row["curr"] or "CNY").strip().upper(),
                "asset_type": str(row["asset_type"] or "").strip().lower(),
                "ledger_id": int(row["ledger_id"] or 0),
            }
        return result
    finally:
        conn.close()


def _pick_previous_nav_date(sorted_dates: List[str], target_date: str) -> str | None:
    prev_date: str | None = None
    for date_str in sorted_dates:
        if date_str >= target_date:
            break
        prev_date = date_str
    return prev_date


def _load_existing_breakdowns(user_id: str, date_str: str, ledger_id: int | None = None) -> Dict[str, Dict[str, Any]]:
    conn = app_module.db.get_connection()
    cursor = conn.cursor()
    try:
        if ledger_id is None:
            cursor.execute(
                """
                SELECT market, day_pnl, source, snapshot_date
                FROM daily_snapshot_market_breakdowns
                WHERE date = ? AND COALESCE(user_id,'') = ?
                """,
                (str(date_str or ""), str(user_id or "")),
            )
        else:
            cursor.execute(
                """
                SELECT market, day_pnl, source, snapshot_date
                FROM ledger_daily_snapshot_market_breakdowns
                WHERE date = ? AND COALESCE(user_id,'') = ? AND ledger_id = ?
                """,
                (str(date_str or ""), str(user_id or ""), int(ledger_id)),
            )
        rows = {}
        for row in cursor.fetchall():
            rows[str(row["market"] or "").strip().lower()] = {
                "day_pnl": round(float(row["day_pnl"] or 0.0), 2),
                "source": str(row["source"] or "").strip(),
                "snapshot_date": str(row["snapshot_date"] or "").strip(),
            }
        return rows
    finally:
        conn.close()


def _has_complete_breakdowns(user_id: str, date_str: str, ledger_id: int | None = None) -> bool:
    rows = _load_existing_breakdowns(user_id=user_id, date_str=date_str, ledger_id=ledger_id)
    return all(market in rows for market in ("a", "hk", "us", "fund", "unallocated"))


def _fx_rate_for(currency: str, date_str: str, fx_map: Dict[str, Dict[str, float]]) -> float:
    currency_key = str(currency or "CNY").strip().upper()
    if currency_key in ("", "CNY"):
        return 1.0
    per_day = fx_map.get(currency_key) or {}
    rate = per_day.get(str(date_str or ""))
    if rate is None or rate <= 0:
        raise ValueError(f"缺少 {currency_key} 在 {date_str} 的汇率")
    return float(rate)


def _iter_target_dates(funds: Iterable[FundNavConfig], start_date: str, end_date: str) -> List[str]:
    dates = set()
    for fund in funds:
        for date_str in fund.navs.keys():
            if str(start_date) <= date_str <= str(end_date):
                dates.add(date_str)
    return sorted(dates)


def build_fund_totals(
    *,
    user_id: str,
    ledger_id: int | None,
    funds: List[FundNavConfig],
    fx_map: Dict[str, Dict[str, float]],
    start_date: str,
    end_date: str,
) -> Dict[str, Dict[str, Any]]:
    positions = _load_positions(user_id=user_id, ledger_id=ledger_id)
    result: Dict[str, Dict[str, Any]] = {}

    for fund in funds:
        position = positions.get(fund.code)
        if not position:
            raise ValueError(f"持仓里找不到基金 {fund.code}")
        sorted_dates = sorted(fund.navs.keys())
        currency = fund.currency or str(position.get("curr") or "CNY").strip().upper()

        for date_str in _iter_target_dates([fund], start_date, end_date):
            prev_date = _pick_previous_nav_date(sorted_dates, date_str)
            if not prev_date:
                continue
            nav_today = float(fund.navs[date_str])
            nav_prev = float(fund.navs[prev_date])
            qty = float(
                app_module.db.get_position_qty_as_of_effective_date(
                    fund.code,
                    date_str,
                    user_id=user_id,
                    ledger_id=ledger_id,
                )
            )
            if qty <= 0:
                continue
            rate = _fx_rate_for(currency, date_str, fx_map)
            pnl = round((nav_today - nav_prev) * qty * rate, 2)
            bucket = result.setdefault(date_str, {"fund_total": 0.0, "details": []})
            bucket["fund_total"] = round(float(bucket["fund_total"]) + pnl, 2)
            bucket["details"].append(
                {
                    "code": fund.code,
                    "currency": currency,
                    "nav_today": nav_today,
                    "nav_prev": nav_prev,
                    "qty": round(qty, 6),
                    "fx_rate": round(rate, 6),
                    "day_pnl": pnl,
                }
            )
    return result


def _snapshot_exists(*, user_id: str, date_str: str, ledger_id: int | None = None) -> bool:
    conn = app_module.db.get_connection()
    cursor = conn.cursor()
    try:
        if ledger_id is None:
            cursor.execute(
                """
                SELECT 1
                FROM daily_snapshots
                WHERE date = ? AND COALESCE(user_id,'') = ?
                LIMIT 1
                """,
                (str(date_str or ""), str(user_id or "")),
            )
        else:
            cursor.execute(
                """
                SELECT 1
                FROM ledger_daily_snapshots
                WHERE date = ? AND COALESCE(user_id,'') = ? AND ledger_id = ?
                LIMIT 1
                """,
                (str(date_str or ""), str(user_id or ""), int(ledger_id)),
            )
        return cursor.fetchone() is not None
    finally:
        conn.close()


def apply_fund_repair(
    *,
    user_id: str,
    ledger_id: int | None,
    per_date: Dict[str, Dict[str, Any]],
    source: str,
    apply: bool,
    sync_day_pnl: bool,
) -> None:
    for date_str in sorted(per_date.keys()):
        payload = per_date[date_str]
        new_fund = round(float(payload.get("fund_total") or 0.0), 2)
        meta_json = json.dumps({"details": payload.get("details") or []}, ensure_ascii=False)
        existing_global = _load_existing_breakdowns(user_id=user_id, date_str=date_str)
        old_fund = round(float((existing_global.get("fund") or {}).get("day_pnl") or 0.0), 2)
        delta = round(new_fund - old_fund, 2)
        print(f"{date_str} fund: {old_fund:+.2f} -> {new_fund:+.2f} (delta {delta:+.2f})")

        if not apply:
            continue

        if _snapshot_exists(user_id=user_id, date_str=date_str):
            ok = app_module.db.save_daily_snapshot_market_breakdown_row(
                date_str=date_str,
                market="fund",
                day_pnl=new_fund,
                user_id=user_id,
                snapshot_date=date_str,
                source=source,
                confidence=1.0,
                meta_json=meta_json,
            )
            if not ok:
                raise RuntimeError(f"全局 fund 行写入失败: {date_str}")
            if sync_day_pnl:
                if not app_module.db.sync_daily_snapshot_day_pnl_from_breakdown(date_str, user_id=user_id):
                    raise RuntimeError(f"全局 day_pnl 同步失败: {date_str}")

        if ledger_id is None:
            continue

        if _snapshot_exists(user_id=user_id, date_str=date_str, ledger_id=ledger_id):
            ok = app_module.db.save_daily_snapshot_market_breakdown_row(
                date_str=date_str,
                market="fund",
                day_pnl=new_fund,
                user_id=user_id,
                ledger_id=ledger_id,
                snapshot_date=date_str,
                source=source,
                confidence=1.0,
                meta_json=meta_json,
            )
            if not ok:
                raise RuntimeError(f"账本 fund 行写入失败: {date_str}")
            if sync_day_pnl and _has_complete_breakdowns(user_id=user_id, date_str=date_str, ledger_id=ledger_id):
                if not app_module.db.sync_ledger_daily_snapshot_day_pnl_from_breakdown(
                    date_str=date_str,
                    user_id=user_id,
                    ledger_id=ledger_id,
                ):
                    raise RuntimeError(f"账本 day_pnl 同步失败: {date_str}")
            elif sync_day_pnl:
                print(f"  WARN {date_str} ledger breakdown 不完整，跳过账本 day_pnl 同步")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="按历史净值重建 fund 分市场收益")
    parser.add_argument("--db-path", help="数据库路径，默认使用 KONA_DATABASE_PATH 或 portfolio.db")
    parser.add_argument("--user-id", required=True, help="目标用户 ID")
    parser.add_argument("--ledger-id", type=int, help="可选：同步修复指定账本")
    parser.add_argument("--start-date", required=True, help="开始日期，格式 YYYY-MM-DD")
    parser.add_argument("--end-date", required=True, help="结束日期，格式 YYYY-MM-DD")
    parser.add_argument("--nav-file", required=True, help="历史净值 JSON 文件路径")
    parser.add_argument("--apply", action="store_true", help="真正写库；默认只 dry-run")
    parser.add_argument(
        "--sync-day-pnl",
        action="store_true",
        help="写 fund 行后，同步更新 daily_snapshots / ledger_daily_snapshots 的 day_pnl",
    )
    parser.add_argument("--source", default="manual_fix", help="写库 source，默认 manual_fix")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.db_path:
        os.environ["KONA_DATABASE_PATH"] = str(args.db_path)
        app_module.db.db_path = str(args.db_path)

    funds, fx_map = _load_nav_payload(Path(args.nav_file))
    if not funds:
        raise SystemExit("净值文件里没有有效基金数据")

    per_date = build_fund_totals(
        user_id=args.user_id,
        ledger_id=args.ledger_id,
        funds=funds,
        fx_map=fx_map,
        start_date=args.start_date,
        end_date=args.end_date,
    )
    if not per_date:
        raise SystemExit("没有生成任何 fund 日收益，请检查日期和净值数据")

    apply_fund_repair(
        user_id=args.user_id,
        ledger_id=args.ledger_id,
        per_date=per_date,
        source=str(args.source or "manual_fix"),
        apply=bool(args.apply),
        sync_day_pnl=bool(args.sync_day_pnl),
    )
    if not args.apply:
        print("\n(dry run，带 --apply 才会写库)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
