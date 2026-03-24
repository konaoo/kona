#!/usr/bin/env python3
"""按 last_login_ip 回填 users.last_login_region（省-市）。"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# config.py 依赖 JWT_SECRET；脚本独立运行时提供默认值。
os.environ.setdefault("JWT_SECRET", "backfill_login_regions_temp_secret")

from core.ip_region import is_normalized_region, normalize_region_text, resolve_ip_region


@dataclass
class Candidate:
    user_id: str
    username: str
    ip: str
    old_region: str
    new_region: str


def _need_backfill(region: str) -> bool:
    raw = str(region or "").strip()
    if not raw:
        return True
    normalized = normalize_region_text(raw)
    if not normalized:
        return True
    if normalized != raw:
        return True
    return not is_normalized_region(raw)


def collect_candidates(
    conn: sqlite3.Connection,
    sleep_seconds: float = 0.05,
) -> tuple[List[Candidate], Dict[str, int]]:
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    user_cols = {str(row["name"]) for row in cursor.fetchall()}
    required_cols = {"last_login_ip", "last_login_region"}
    if not required_cols.issubset(user_cols):
        return [], {
            "total_with_ip": 0,
            "already_normalized": 0,
            "resolved": 0,
            "resolve_failed": 0,
            "skipped_same": 0,
            "missing_columns": 1,
        }
    cursor.execute(
        """
        SELECT id, username, COALESCE(last_login_ip, '') AS last_login_ip, COALESCE(last_login_region, '') AS last_login_region
        FROM users
        WHERE COALESCE(TRIM(last_login_ip), '') != ''
        ORDER BY COALESCE(last_login, created_at, '') DESC, id DESC
        """
    )
    rows = cursor.fetchall()

    ip_cache: Dict[str, str] = {}
    candidates: List[Candidate] = []
    stats = {
        "total_with_ip": 0,
        "already_normalized": 0,
        "resolved": 0,
        "resolve_failed": 0,
        "skipped_same": 0,
        "missing_columns": 0,
    }

    for row in rows:
        stats["total_with_ip"] += 1
        user_id = str(row["id"] or "")
        username = str(row["username"] or "")
        ip = str(row["last_login_ip"] or "").strip()
        old_region = str(row["last_login_region"] or "").strip()
        if not _need_backfill(old_region):
            stats["already_normalized"] += 1
            continue

        if ip in ip_cache:
            new_region = ip_cache[ip]
        else:
            new_region = resolve_ip_region(ip)
            ip_cache[ip] = new_region
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

        if not new_region:
            stats["resolve_failed"] += 1
            continue

        if new_region == old_region:
            stats["skipped_same"] += 1
            continue

        stats["resolved"] += 1
        candidates.append(
            Candidate(
                user_id=user_id,
                username=username,
                ip=ip,
                old_region=old_region,
                new_region=new_region,
            )
        )

    return candidates, stats


def apply_candidates(conn: sqlite3.Connection, candidates: List[Candidate]) -> int:
    if not candidates:
        return 0
    cursor = conn.cursor()
    updated = 0
    for item in candidates:
        cursor.execute(
            "UPDATE users SET last_login_region = ? WHERE id = ?",
            (item.new_region, item.user_id),
        )
        updated += int(cursor.rowcount or 0)
    conn.commit()
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill last_login_region from last_login_ip with normalized zh region.",
    )
    parser.add_argument(
        "--db-path",
        default=os.getenv("KONA_DATABASE_PATH", str(ROOT / "portfolio.db")),
        help="SQLite database path",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.05,
        help="Sleep seconds between uncached IP requests",
    )
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=20,
        help="Print at most N sample updates",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply updates. Default dry-run.",
    )
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)
    conn.row_factory = sqlite3.Row
    try:
        candidates, stats = collect_candidates(conn, sleep_seconds=max(0.0, args.sleep))
        print(f"DB: {args.db_path}")
        print(f"Mode: {'APPLY' if args.apply else 'DRY-RUN'}")
        print(
            "Stats:"
            f" total_with_ip={stats['total_with_ip']}"
            f" already_normalized={stats['already_normalized']}"
            f" resolved={stats['resolved']}"
            f" resolve_failed={stats['resolve_failed']}"
            f" skipped_same={stats['skipped_same']}"
            f" missing_columns={stats['missing_columns']}"
        )
        if stats["missing_columns"] > 0:
            print("users 表缺少 last_login_ip/last_login_region 字段，跳过回填。")
            return 0
        print(f"Candidates: {len(candidates)}")

        if candidates:
            print("Sample updates (username, ip, old -> new):")
            for item in candidates[: max(0, args.sample_limit)]:
                old_text = item.old_region or "(empty)"
                print(f"- {item.username} | {item.ip} | {old_text} -> {item.new_region}")

        if args.apply:
            updated = apply_candidates(conn, candidates)
            print(f"Updated rows: {updated}")
        else:
            print("Dry-run only. Use --apply to persist changes.")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
