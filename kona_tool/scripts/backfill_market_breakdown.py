#!/usr/bin/env python3
"""
Backfill daily market breakdowns from historical daily snapshots.

Strategy:
1) Use realized pnl from same-day '减仓' transactions as exact per-market component.
2) Remaining floating residual is distributed by end-of-day cost exposure weights.
3) Unallocatable residual is written to market='unallocated' explicitly.
4) Rows are written as source='estimated' with confidence metadata.
"""

import argparse
import os
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("JWT_SECRET", "backfill_market_breakdown_temp_secret")

from core.db import DatabaseManager
from core.market_calendar import market_from_asset, is_trading_day
from core.parser import parse_code

PRIMARY_MARKETS = ("a", "hk", "us", "fund")
ALL_MARKETS = ("a", "hk", "us", "fund", "unallocated")
EPS = 1e-9


@dataclass
class Candidate:
    user_id: str
    date: str
    day_total: float
    breakdown: Dict[str, float]
    confidence: float
    meta_by_market: Dict[str, Any]


def _normalize_market_from_code(code: str) -> str:
    raw = str(code or "").strip()
    normalized = parse_code(raw, "").get("code") or raw
    market = str(market_from_asset(normalized) or "a").lower()
    return market if market in PRIMARY_MARKETS else "a"


def _fetch_user_ids(conn: sqlite3.Connection, start_date: str, end_date: str, user_id: str) -> List[str]:
    if user_id:
        return [user_id]
    cursor = conn.cursor()
    sql = """
        SELECT DISTINCT COALESCE(user_id, '') AS user_id
        FROM daily_snapshots
        WHERE 1=1
    """
    params: List[str] = []
    if start_date:
        sql += " AND date >= ?"
        params.append(start_date)
    if end_date:
        sql += " AND date <= ?"
        params.append(end_date)
    sql += " ORDER BY COALESCE(user_id, '') ASC"
    cursor.execute(sql, tuple(params))
    return [str(r["user_id"] or "") for r in cursor.fetchall()]


def _fetch_snapshot_rows(
    conn: sqlite3.Connection, uid: str, start_date: str, end_date: str
) -> List[sqlite3.Row]:
    cursor = conn.cursor()
    sql = """
        SELECT date, day_pnl
        FROM daily_snapshots
        WHERE COALESCE(user_id, '') = ?
    """
    params: List[str] = [uid]
    if start_date:
        sql += " AND date >= ?"
        params.append(start_date)
    if end_date:
        sql += " AND date <= ?"
        params.append(end_date)
    sql += " ORDER BY date ASC"
    cursor.execute(sql, tuple(params))
    return cursor.fetchall()


def _fetch_existing_sources(
    conn: sqlite3.Connection, uid: str, start_date: str, end_date: str
) -> Dict[str, set]:
    cursor = conn.cursor()
    sql = """
        SELECT date, source
        FROM daily_snapshot_market_breakdowns
        WHERE COALESCE(user_id, '') = ?
    """
    params: List[str] = [uid]
    if start_date:
        sql += " AND date >= ?"
        params.append(start_date)
    if end_date:
        sql += " AND date <= ?"
        params.append(end_date)
    cursor.execute(sql, tuple(params))
    by_date: Dict[str, set] = {}
    for row in cursor.fetchall():
        d = str(row["date"])
        by_date.setdefault(d, set()).add(str(row["source"] or "").lower())
    return by_date


def _fetch_transactions_until(
    conn: sqlite3.Connection, uid: str, end_date: str
) -> List[sqlite3.Row]:
    cursor = conn.cursor()
    sql = """
        SELECT id, time, code, type, price, qty, pnl, market, effective_date
        FROM transactions
        WHERE COALESCE(user_id, '') = ?
    """
    params: List[str] = [uid]
    if end_date:
        sql += " AND COALESCE(NULLIF(substr(effective_date, 1, 10), ''), substr(time, 1, 10)) <= ?"
        params.append(end_date)
    sql += " ORDER BY time ASC, id ASC"
    cursor.execute(sql, tuple(params))
    return cursor.fetchall()


def _apply_transaction(position_state: Dict[str, Dict[str, float]], tx_row: sqlite3.Row) -> None:
    code = str(tx_row["code"] or "")
    tx_type = str(tx_row["type"] or "")
    qty = float(tx_row["qty"] or 0.0)
    price = float(tx_row["price"] or 0.0)
    if not code or qty <= 0.0:
        return

    state = position_state.setdefault(code, {"qty": 0.0, "cost": 0.0})
    old_qty = float(state["qty"])
    old_cost = float(state["cost"])

    if tx_type == "加仓":
        new_qty = old_qty + qty
        if new_qty > EPS:
            state["cost"] = (old_qty * old_cost + qty * price) / new_qty
            state["qty"] = new_qty
        return

    if tx_type == "减仓":
        if old_qty <= EPS:
            return
        remain_qty = old_qty - qty
        if remain_qty <= EPS:
            state["qty"] = 0.0
            return
        state["qty"] = remain_qty


def _build_realized_by_date(transactions: List[sqlite3.Row]) -> Dict[str, Dict[str, float]]:
    result: Dict[str, Dict[str, float]] = {}
    for tx in transactions:
        if str(tx["type"] or "") != "减仓":
            continue
        date_str = str(tx["effective_date"] or "")[:10] or str(tx["time"] or "")[:10]
        if len(date_str) != 10:
            continue
        raw_market = str(tx["market"] or "").strip().lower()
        market = raw_market if raw_market in PRIMARY_MARKETS else _normalize_market_from_code(str(tx["code"] or ""))
        day = result.setdefault(date_str, {m: 0.0 for m in PRIMARY_MARKETS})
        day[market] += float(tx["pnl"] or 0.0)
    return result


def _cost_exposure_by_market(position_state: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    exposures = {m: 0.0 for m in PRIMARY_MARKETS}
    for code, state in position_state.items():
        qty = float(state.get("qty") or 0.0)
        cost = float(state.get("cost") or 0.0)
        if qty <= EPS:
            continue
        market = _normalize_market_from_code(code)
        exposures[market] += qty * cost
    return exposures


def _active_markets_on_date(date_str: str) -> List[str]:
    active: List[str] = []
    for market in PRIMARY_MARKETS:
        try:
            if bool(is_trading_day(market, date_str)):
                active.append(market)
        except Exception:
            # Keep backfill robust when calendar dependency is unavailable.
            active.append(market)
    return active


def _build_candidates_for_user(
    conn: sqlite3.Connection,
    uid: str,
    start_date: str,
    end_date: str,
) -> List[Candidate]:
    snapshots = _fetch_snapshot_rows(conn, uid, start_date, end_date)
    if not snapshots:
        return []

    existing_sources = _fetch_existing_sources(conn, uid, start_date, end_date)
    tx_rows = _fetch_transactions_until(conn, uid, end_date)
    realized_by_date = _build_realized_by_date(tx_rows)

    tx_idx = 0
    positions: Dict[str, Dict[str, float]] = {}
    candidates: List[Candidate] = []

    for snap in snapshots:
        date_str = str(snap["date"])
        while tx_idx < len(tx_rows):
            tx_date = str(tx_rows[tx_idx]["time"] or "")[:10]
            if not tx_date or tx_date > date_str:
                break
            _apply_transaction(positions, tx_rows[tx_idx])
            tx_idx += 1

        # Do not overwrite exact history.
        if "exact" in existing_sources.get(date_str, set()):
            continue

        day_total = round(float(snap["day_pnl"] or 0.0), 2)
        realized = realized_by_date.get(date_str, {m: 0.0 for m in PRIMARY_MARKETS})
        breakdown = {m: 0.0 for m in ALL_MARKETS}

        realized_sum = 0.0
        for market in PRIMARY_MARKETS:
            value = float(realized.get(market, 0.0) or 0.0)
            breakdown[market] += value
            realized_sum += value

        floating_residual = day_total - realized_sum
        exposures = _cost_exposure_by_market(positions)
        active_markets = _active_markets_on_date(date_str)
        weight_sum = sum(max(float(exposures[m]), 0.0) for m in active_markets)

        alloc_by_market = {m: 0.0 for m in PRIMARY_MARKETS}
        if abs(floating_residual) > EPS:
            if active_markets and weight_sum > EPS:
                for market in active_markets:
                    weight = max(float(exposures[market]), 0.0)
                    if weight > EPS:
                        alloc_by_market[market] = floating_residual * (weight / weight_sum)
                        breakdown[market] += alloc_by_market[market]
            else:
                breakdown["unallocated"] += floating_residual

        modeled_total = sum(breakdown[m] for m in PRIMARY_MARKETS) + breakdown["unallocated"]
        residual_after_modeled = day_total - modeled_total
        # Keep residual explicitly in unallocated instead of hidden forced allocation.
        breakdown["unallocated"] += residual_after_modeled

        # Confidence policy:
        # - has meaningful exposure and residual small -> 0.75
        # - otherwise -> 0.40
        if weight_sum > EPS and abs(breakdown["unallocated"]) <= max(1.0, abs(day_total) * 0.05):
            confidence = 0.75
        else:
            confidence = 0.40

        meta_by_market: Dict[str, Any] = {}
        for market in PRIMARY_MARKETS:
            meta_by_market[market] = {
                "method": "estimated",
                "realized_component": round(float(realized.get(market, 0.0) or 0.0), 6),
                "floating_allocated_component": round(float(alloc_by_market[market]), 6),
                "cost_exposure": round(float(exposures[market]), 6),
            }
        meta_by_market["unallocated"] = {
            "method": "estimated",
            "reason": "residual_after_weight_allocation",
            "floating_residual": round(float(floating_residual), 6),
            "value": round(float(breakdown["unallocated"]), 6),
            "weight_sum": round(float(weight_sum), 6),
            "active_markets": active_markets,
        }

        candidates.append(
            Candidate(
                user_id=uid,
                date=date_str,
                day_total=day_total,
                breakdown=breakdown,
                confidence=confidence,
                meta_by_market=meta_by_market,
            )
        )

    return candidates


def collect_candidates(
    db_manager: DatabaseManager,
    start_date: str = "",
    end_date: str = "",
    user_id: str = "",
) -> List[Candidate]:
    conn = db_manager.get_connection()
    try:
        user_ids = _fetch_user_ids(conn, start_date=start_date, end_date=end_date, user_id=user_id)
        all_candidates: List[Candidate] = []
        for uid in user_ids:
            all_candidates.extend(
                _build_candidates_for_user(
                    conn=conn,
                    uid=uid,
                    start_date=start_date,
                    end_date=end_date,
                )
            )
        return all_candidates
    finally:
        conn.close()


def apply_candidates(db_manager: DatabaseManager, candidates: List[Candidate]) -> int:
    updated = 0
    for item in candidates:
        ok = db_manager.save_daily_snapshot_market_breakdown(
            date_str=item.date,
            day_pnl_by_market=item.breakdown,
            total_day_pnl=item.day_total,
            user_id=item.user_id,
            source="estimated",
            confidence=float(item.confidence),
            meta_by_market=item.meta_by_market,
        )
        if ok:
            updated += 1
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill market breakdowns (a/hk/us/fund/unallocated) from daily snapshots."
    )
    parser.add_argument(
        "--db-path",
        default=os.getenv("KONA_DATABASE_PATH", str(ROOT / "portfolio.db")),
        help="SQLite database path (default: KONA_DATABASE_PATH or ./portfolio.db)",
    )
    parser.add_argument("--start-date", default="", help="Inclusive YYYY-MM-DD")
    parser.add_argument("--end-date", default="", help="Inclusive YYYY-MM-DD")
    parser.add_argument("--user-id", default="", help="Only process this user_id")
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=20,
        help="Show up to N sample rows",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply updates. Without this flag, script runs in dry-run mode.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Explicit dry-run mode (same as default when --apply is not set).",
    )
    args = parser.parse_args()

    db_manager = DatabaseManager(args.db_path)
    candidates = collect_candidates(
        db_manager=db_manager,
        start_date=args.start_date,
        end_date=args.end_date,
        user_id=args.user_id,
    )

    print(f"DB: {args.db_path}")
    print(f"Mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    print(
        f"Scope: user_id={args.user_id or '*'} start={args.start_date or '*'} end={args.end_date or '*'}"
    )
    print(f"Candidates: {len(candidates)}")
    if candidates:
        print("sample(user_id, date, total_day_pnl, a, hk, us, fund, unallocated, confidence):")
        for item in candidates[: max(0, args.sample_limit)]:
            b = item.breakdown
            print(
                "  "
                f"{item.user_id or '(empty)'} | {item.date} | {item.day_total:.2f} | "
                f"{b['a']:.2f} | {b['hk']:.2f} | {b['us']:.2f} | {b['fund']:.2f} | "
                f"{b['unallocated']:.2f} | {item.confidence:.2f}"
            )

    if not args.apply:
        return 0

    updated = apply_candidates(db_manager, candidates)
    print(f"Updated rows: {updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
