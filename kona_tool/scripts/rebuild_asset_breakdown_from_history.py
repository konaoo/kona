#!/usr/bin/env python3
"""
按历史价格重建指定用户的逐资产日收益明细。

这个脚本只干一件事：
- 对指定日期范围，按真实历史持仓 + 历史价格 + 历史交易重算逐资产 day_pnl；
- 可选同步 asset breakdown / market breakdown / daily_snapshots.day_pnl；
- 默认先 dry-run，支持输出可审阅 SQL。

适用场景：
- 某几天 historical day_pnl 是 backfill 估算值；
- 页面要求“点开格子后，每只资产都能对得上”；
- 需要最小范围修线上历史数据。
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("JWT_SECRET", "rebuild_asset_breakdown_from_history_temp_secret")

from core.analysis_asset_breakdown_service import AnalysisAssetBreakdownService, _parse_iso_date
from core.db import DatabaseManager
from core.price import batch_get_prices, get_forex_rates


@dataclass
class CandidateDay:
    date_str: str
    stored_total: float
    rebuilt_total: float
    market_totals: Dict[str, float]
    items: List[Dict[str, Any]]


def _round_amount(value: Any) -> float:
    try:
        return round(float(value or 0.0), 2)
    except Exception:
        return 0.0


def _sql_text(value: Any) -> str:
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def _fetch_snapshot_total(
    db: DatabaseManager,
    *,
    user_id: str,
    date_str: str,
    ledger_id: int | None,
) -> float:
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        if ledger_id is None:
            cursor.execute(
                """
                SELECT day_pnl
                FROM daily_snapshots
                WHERE date = ? AND COALESCE(user_id, '') = ?
                """,
                (date_str, user_id or ""),
            )
        else:
            cursor.execute(
                """
                SELECT day_pnl
                FROM ledger_daily_snapshots
                WHERE date = ? AND COALESCE(user_id, '') = ? AND ledger_id = ?
                """,
                (date_str, user_id or "", int(ledger_id)),
            )
        row = cursor.fetchone()
        return _round_amount(row["day_pnl"]) if row else 0.0
    finally:
        conn.close()


def _iter_dates(start_date: str, end_date: str) -> Iterable[str]:
    current = _parse_iso_date(start_date)
    end = _parse_iso_date(end_date)
    if current is None or end is None:
        return []
    values: List[str] = []
    while current <= end:
        values.append(current.strftime("%Y-%m-%d"))
        current = current.fromordinal(current.toordinal() + 1)
    return values


def _build_candidates(
    *,
    db: DatabaseManager,
    user_id: str,
    ledger_id: int | None,
    start_date: str,
    end_date: str,
) -> List[CandidateDay]:
    service = AnalysisAssetBreakdownService(
        db=db,
        price_batch_getter=batch_get_prices,
        rates_getter=get_forex_rates,
    )
    result: List[CandidateDay] = []

    for date_str in _iter_dates(start_date, end_date):
        target = _parse_iso_date(date_str)
        if target is None:
            continue
        context = service._build_period_context(target, target, user_id=user_id, ledger_id=ledger_id)
        items = service._build_historical_day_items(target, context=context)
        if not items:
            continue

        market_totals: Dict[str, float] = {}
        normalized_items: List[Dict[str, Any]] = []
        for item in items:
            pnl = _round_amount(item.get("pnl"))
            base = _round_amount(item.get("base"))
            market = str(item.get("market") or "a").strip().lower() or "a"
            market_totals[market] = _round_amount(market_totals.get(market, 0.0) + pnl)
            normalized_items.append(
                {
                    "code": str(item.get("code") or ""),
                    "name": str(item.get("name") or item.get("code") or ""),
                    "market": market,
                    "curr": str(item.get("curr") or "CNY").strip().upper(),
                    "day_pnl": pnl,
                    "day_base": base,
                }
            )

        rebuilt_total = _round_amount(sum(float(item.get("day_pnl") or 0.0) for item in normalized_items))
        stored_total = _fetch_snapshot_total(
            db,
            user_id=user_id,
            date_str=date_str,
            ledger_id=ledger_id,
        )
        result.append(
            CandidateDay(
                date_str=date_str,
                stored_total=stored_total,
                rebuilt_total=rebuilt_total,
                market_totals=market_totals,
                items=normalized_items,
            )
        )
    return result


def _print_candidates(candidates: List[CandidateDay]) -> None:
    print(f"候选日期数: {len(candidates)}")
    for item in candidates:
        delta = _round_amount(item.rebuilt_total - item.stored_total)
        print(
            f"{item.date_str} | 现存总额={item.stored_total:.2f} | "
            f"重算总额={item.rebuilt_total:.2f} | 差额={delta:.2f} | "
            f"市场={ {k: round(v, 2) for k, v in sorted(item.market_totals.items())} }"
        )


def _emit_sql(
    *,
    candidates: List[CandidateDay],
    user_id: str,
    ledger_id: int | None,
    source: str,
) -> str:
    lines: List[str] = ["BEGIN;"]
    uid_sql = _sql_text(user_id or "")

    for day in candidates:
        date_sql = _sql_text(day.date_str)
        snapshot_date_sql = date_sql
        source_sql = _sql_text(source)

        lines.append(f"-- {day.date_str}")
        lines.append(
            f"DELETE FROM daily_snapshot_asset_breakdowns WHERE date = {date_sql} AND COALESCE(user_id, '') = {uid_sql};"
        )
        if ledger_id is not None:
            lines.append(
                "DELETE FROM ledger_daily_snapshot_asset_breakdowns "
                f"WHERE date = {date_sql} AND COALESCE(user_id, '') = {uid_sql} AND ledger_id = {int(ledger_id)};"
            )

        for asset in day.items:
            lines.append(
                "INSERT INTO daily_snapshot_asset_breakdowns "
                "(date, user_id, code, name, market, curr, day_pnl, day_base, snapshot_date, source, confidence, updated_at) "
                f"VALUES ({date_sql}, {uid_sql}, {_sql_text(asset['code'])}, {_sql_text(asset['name'])}, "
                f"{_sql_text(asset['market'])}, {_sql_text(asset['curr'])}, {asset['day_pnl']:.2f}, {asset['day_base']:.2f}, "
                f"{snapshot_date_sql}, {source_sql}, 1.0, datetime('now','localtime')) "
                "ON CONFLICT(date, user_id, code) DO UPDATE SET "
                "name = excluded.name, market = excluded.market, curr = excluded.curr, "
                "day_pnl = excluded.day_pnl, day_base = excluded.day_base, snapshot_date = excluded.snapshot_date, "
                "source = excluded.source, confidence = excluded.confidence, updated_at = datetime('now','localtime');"
            )
            if ledger_id is not None:
                lines.append(
                    "INSERT INTO ledger_daily_snapshot_asset_breakdowns "
                    "(user_id, ledger_id, date, code, name, market, curr, day_pnl, day_base, snapshot_date, source, confidence, updated_at) "
                    f"VALUES ({uid_sql}, {int(ledger_id)}, {date_sql}, {_sql_text(asset['code'])}, {_sql_text(asset['name'])}, "
                    f"{_sql_text(asset['market'])}, {_sql_text(asset['curr'])}, {asset['day_pnl']:.2f}, {asset['day_base']:.2f}, "
                    f"{snapshot_date_sql}, {source_sql}, 1.0, datetime('now','localtime')) "
                    "ON CONFLICT(user_id, ledger_id, date, code) DO UPDATE SET "
                    "name = excluded.name, market = excluded.market, curr = excluded.curr, "
                    "day_pnl = excluded.day_pnl, day_base = excluded.day_base, snapshot_date = excluded.snapshot_date, "
                    "source = excluded.source, confidence = excluded.confidence, updated_at = datetime('now','localtime');"
                )

        for market in ("a", "hk", "us", "fund", "unallocated"):
            day_pnl = _round_amount(day.market_totals.get(market, 0.0))
            lines.append(
                "INSERT INTO daily_snapshot_market_breakdowns "
                "(date, user_id, market, day_pnl, snapshot_date, source, confidence, meta_json, updated_at) "
                f"VALUES ({date_sql}, {uid_sql}, {_sql_text(market)}, {day_pnl:.2f}, {snapshot_date_sql}, {source_sql}, 1.0, NULL, datetime('now','localtime')) "
                "ON CONFLICT(date, user_id, market) DO UPDATE SET "
                "day_pnl = excluded.day_pnl, snapshot_date = excluded.snapshot_date, source = excluded.source, "
                "confidence = excluded.confidence, meta_json = excluded.meta_json, updated_at = datetime('now','localtime');"
            )
            if ledger_id is not None:
                lines.append(
                    "INSERT INTO ledger_daily_snapshot_market_breakdowns "
                    "(user_id, ledger_id, date, snapshot_date, market, day_pnl, source, confidence, meta_json, updated_at) "
                    f"VALUES ({uid_sql}, {int(ledger_id)}, {date_sql}, {snapshot_date_sql}, {_sql_text(market)}, {day_pnl:.2f}, {source_sql}, 1.0, NULL, datetime('now','localtime')) "
                    "ON CONFLICT(user_id, ledger_id, date, market) DO UPDATE SET "
                    "snapshot_date = excluded.snapshot_date, day_pnl = excluded.day_pnl, source = excluded.source, "
                    "confidence = excluded.confidence, meta_json = excluded.meta_json, updated_at = datetime('now','localtime');"
                )

        lines.append(
            "UPDATE daily_snapshots SET day_pnl = "
            f"{day.rebuilt_total:.2f}, updated_at = datetime('now','localtime') "
            f"WHERE date = {date_sql} AND COALESCE(user_id, '') = {uid_sql};"
        )
        if ledger_id is not None:
            lines.append(
                "UPDATE ledger_daily_snapshots SET day_pnl = "
                f"{day.rebuilt_total:.2f}, created_at = datetime('now','localtime') "
                f"WHERE date = {date_sql} AND COALESCE(user_id, '') = {uid_sql} AND ledger_id = {int(ledger_id)};"
            )

    lines.append("COMMIT;")
    return "\n".join(lines) + "\n"


def _apply_candidates(
    *,
    db: DatabaseManager,
    candidates: List[CandidateDay],
    user_id: str,
    ledger_id: int | None,
    source: str,
) -> None:
    for day in candidates:
        ok = db.save_daily_snapshot_asset_breakdowns(
            date_str=day.date_str,
            items=day.items,
            user_id=user_id,
            snapshot_date=day.date_str,
            source=source,
            confidence=1.0,
            replace_existing=True,
        )
        if not ok:
            raise RuntimeError(f"写入全局逐资产明细失败: {day.date_str}")
        if ledger_id is not None:
            ok = db.save_daily_snapshot_asset_breakdowns(
                date_str=day.date_str,
                items=day.items,
                user_id=user_id,
                snapshot_date=day.date_str,
                source=source,
                confidence=1.0,
                replace_existing=True,
                ledger_id=ledger_id,
            )
            if not ok:
                raise RuntimeError(f"写入账本逐资产明细失败: {day.date_str}")

        ok = db.save_daily_snapshot_market_breakdown(
            date_str=day.date_str,
            day_pnl_by_market=day.market_totals,
            total_day_pnl=day.rebuilt_total,
            user_id=user_id,
            snapshot_date=day.date_str,
            source=source,
            confidence=1.0,
        )
        if not ok:
            raise RuntimeError(f"写入全局分市场失败: {day.date_str}")
        if not db.sync_daily_snapshot_day_pnl_from_breakdown(day.date_str, user_id=user_id):
            raise RuntimeError(f"回写全局 day_pnl 失败: {day.date_str}")

        if ledger_id is not None:
            ok = db.save_ledger_daily_snapshot_market_breakdown(
                user_id=user_id,
                ledger_id=ledger_id,
                date_str=day.date_str,
                day_pnl_by_market=day.market_totals,
                total_day_pnl=day.rebuilt_total,
                snapshot_date=day.date_str,
                source=source,
                confidence=1.0,
            )
            if not ok:
                raise RuntimeError(f"写入账本分市场失败: {day.date_str}")
            if not db.sync_ledger_daily_snapshot_day_pnl_from_breakdown(
                date_str=day.date_str,
                user_id=user_id,
                ledger_id=ledger_id,
            ):
                raise RuntimeError(f"回写账本 day_pnl 失败: {day.date_str}")


def main() -> int:
    parser = argparse.ArgumentParser(description="按历史价格重建逐资产日收益")
    parser.add_argument("--db-path", required=True, help="SQLite 路径")
    parser.add_argument("--user-id", required=True, help="用户 ID")
    parser.add_argument("--start-date", required=True, help="开始日期 YYYY-MM-DD")
    parser.add_argument("--end-date", required=True, help="结束日期 YYYY-MM-DD")
    parser.add_argument("--ledger-id", type=int, default=None, help="可选账本 ID")
    parser.add_argument("--source", default="manual_fix", help="写库 source")
    parser.add_argument("--sql-out", default="", help="输出 SQL 文件路径")
    parser.add_argument("--apply", action="store_true", help="直接改当前 db-path")
    args = parser.parse_args()

    db = DatabaseManager(args.db_path)
    candidates = _build_candidates(
        db=db,
        user_id=str(args.user_id or ""),
        ledger_id=args.ledger_id,
        start_date=args.start_date,
        end_date=args.end_date,
    )
    _print_candidates(candidates)

    if not candidates:
        print("没有可重建的候选日期。")
        return 0

    if args.sql_out:
        sql_text = _emit_sql(
            candidates=candidates,
            user_id=str(args.user_id or ""),
            ledger_id=args.ledger_id,
            source=str(args.source or "manual_fix"),
        )
        Path(args.sql_out).write_text(sql_text, encoding="utf-8")
        print(f"已输出 SQL: {args.sql_out}")

    if not args.apply:
        print("当前是 dry-run，未写库。")
        return 0

    _apply_candidates(
        db=db,
        candidates=candidates,
        user_id=str(args.user_id or ""),
        ledger_id=args.ledger_id,
        source=str(args.source or "manual_fix"),
    )
    print("已写库完成。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
