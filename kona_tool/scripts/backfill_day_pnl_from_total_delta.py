#!/usr/bin/env python3
"""
Backfill trading-day day_pnl from total_pnl delta for suspicious zero rows.

Suspicious row criteria:
1) day_pnl == 0
2) date is not an all-markets-closed date
3) updated_at is same date and snapshot time is all-markets-closed
4) previous trading snapshot exists and total_pnl delta != 0
"""

import argparse
import os
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# scripts/* -> kona_tool/*
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# config.py requires JWT_SECRET; provide a local default for standalone script usage.
os.environ.setdefault("JWT_SECRET", "backfill_day_pnl_temp_secret")

from core.market_calendar import all_markets_closed, is_markets_closed_on_date

DEFAULT_MARKETS = ["a", "hk", "us", "fund"]
EPS = 1e-9


@dataclass
class Candidate:
    user_id: str
    date: str
    old_day_pnl: float
    new_day_pnl: float
    delta_total: float
    total_pnl: float
    updated_at: str


def _parse_utc_timestamp(raw: Optional[str]) -> Optional[datetime]:
    if not raw:
        return None
    value = str(raw).strip()
    if not value:
        return None
    try:
        return datetime.strptime(value[:19], "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=timezone.utc
        )
    except Exception:
        return None


def _is_suspicious_closed_snapshot(date_str: str, updated_at: Optional[str]) -> bool:
    if not updated_at:
        return False
    updated = str(updated_at).strip()
    if not updated or updated[:10] != date_str:
        return False
    ts = _parse_utc_timestamp(updated)
    if ts is None:
        return False
    try:
        return bool(all_markets_closed(DEFAULT_MARKETS, now=ts))
    except Exception:
        return False


def _in_scope(date_str: str, start_date: str, end_date: str) -> bool:
    if start_date and date_str < start_date:
        return False
    if end_date and date_str > end_date:
        return False
    return True


def collect_candidates(
    conn: sqlite3.Connection,
    start_date: str = "",
    end_date: str = "",
    user_id: str = "",
) -> List[Candidate]:
    cursor = conn.cursor()
    sql = """
        SELECT COALESCE(user_id, '') AS user_id, date, total_pnl, day_pnl, updated_at
        FROM daily_snapshots
        WHERE 1=1
    """
    params: List[str] = []
    if user_id:
        sql += " AND COALESCE(user_id, '') = ?"
        params.append(user_id)
    if end_date:
        sql += " AND date <= ?"
        params.append(end_date)
    sql += " ORDER BY COALESCE(user_id, '') ASC, date ASC"

    cursor.execute(sql, tuple(params))
    rows = cursor.fetchall()

    candidates: List[Candidate] = []
    prev_trading_total: Dict[str, Optional[float]] = {}
    for row in rows:
        uid = str(row["user_id"] or "")
        date_str = str(row["date"])
        total_pnl = float(row["total_pnl"] or 0.0)
        day_pnl = float(row["day_pnl"] or 0.0)
        updated_at = str(row["updated_at"] or "")

        try:
            date_closed = bool(is_markets_closed_on_date(DEFAULT_MARKETS, date_str))
        except Exception:
            # Keep script conservative when calendar check is unavailable.
            date_closed = True

        prev_total = prev_trading_total.get(uid)
        delta_total = None if prev_total is None else round(total_pnl - prev_total, 2)

        should_backfill = (
            _in_scope(date_str, start_date, end_date)
            and (not date_closed)
            and abs(day_pnl) <= EPS
            and prev_total is not None
            and delta_total is not None
            and abs(delta_total) > EPS
            and _is_suspicious_closed_snapshot(date_str, updated_at)
        )
        if should_backfill:
            candidates.append(
                Candidate(
                    user_id=uid,
                    date=date_str,
                    old_day_pnl=day_pnl,
                    new_day_pnl=float(delta_total),
                    delta_total=float(delta_total),
                    total_pnl=total_pnl,
                    updated_at=updated_at,
                )
            )

        if not date_closed:
            prev_trading_total[uid] = total_pnl

    return candidates


def apply_candidates(conn: sqlite3.Connection, candidates: List[Candidate]) -> int:
    if not candidates:
        return 0
    cursor = conn.cursor()
    updated = 0
    for item in candidates:
        cursor.execute(
            """
            UPDATE daily_snapshots
            SET day_pnl = ?, updated_at = CURRENT_TIMESTAMP
            WHERE date = ? AND COALESCE(user_id, '') = ?
            """,
            (item.new_day_pnl, item.date, item.user_id),
        )
        updated += int(cursor.rowcount or 0)
    conn.commit()
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill day_pnl from total_pnl delta for suspicious zero rows."
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

    conn = sqlite3.connect(args.db_path)
    conn.row_factory = sqlite3.Row
    try:
        candidates = collect_candidates(
            conn=conn,
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
            print("sample(user_id, date, old_day_pnl -> new_day_pnl, delta_total, total_pnl, updated_at):")
            for item in candidates[: max(0, args.sample_limit)]:
                print(
                    f"  {item.user_id or '(empty)'} | {item.date} | "
                    f"{item.old_day_pnl:.2f} -> {item.new_day_pnl:.2f} | "
                    f"delta={item.delta_total:.2f} | total={item.total_pnl:.2f} | {item.updated_at}"
                )

        if not args.apply:
            return 0

        updated = apply_candidates(conn, candidates)
        print(f"Updated rows: {updated}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
