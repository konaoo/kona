#!/usr/bin/env python3
"""Generate initial invite codes and export to CSV."""

from __future__ import annotations

import argparse
import csv
import os
import secrets
from datetime import datetime
from pathlib import Path

os.environ.setdefault("JWT_SECRET", "bootstrap_invite_only_secret")

import config
from core.db import DatabaseManager


def make_code(length: int = 10) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_unique_codes(db: DatabaseManager, count: int, batch_id: str) -> list[str]:
    collected: list[str] = []
    rounds = 0
    while len(collected) < count and rounds < 12:
        rounds += 1
        need = count - len(collected)
        pool = []
        seen = set()
        while len(pool) < need * 2:
            c = make_code(10)
            if c in seen:
                continue
            seen.add(c)
            pool.append(c)
        inserted = db.insert_invite_codes(pool, batch_id=batch_id, created_by="bootstrap", note="initial batch")
        collected.extend(pool[:inserted])
    return collected[:count]


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate initial invite codes")
    parser.add_argument("--count", type=int, default=1000, help="Number of invite codes")
    parser.add_argument("--batch-id", default="", help="Batch id (default auto)")
    parser.add_argument("--output", default="", help="CSV output path")
    args = parser.parse_args()

    if args.count < 1 or args.count > 10000:
        raise SystemExit("count must be between 1 and 10000")

    batch_id = args.batch_id.strip() or datetime.now().strftime("initial-%Y%m%d-%H%M%S")
    output = args.output.strip()
    if not output:
        out_dir = config.BASE_DIR / "archive" / "invites"
        out_dir.mkdir(parents=True, exist_ok=True)
        output = str(out_dir / f"{batch_id}.csv")

    db = DatabaseManager(str(config.DATABASE_PATH))
    codes = generate_unique_codes(db, args.count, batch_id=batch_id)

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["code", "batch_id"])
        for code in codes:
            writer.writerow([code, batch_id])

    print(f"batch_id={batch_id}")
    print(f"requested={args.count} generated={len(codes)}")
    print(f"csv={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
