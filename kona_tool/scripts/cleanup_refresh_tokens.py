#!/usr/bin/env python3
"""Cleanup expired refresh tokens with a retention window."""

from __future__ import annotations

import argparse
import os

os.environ.setdefault("JWT_SECRET", "cleanup_refresh_tokens_only_secret")

import config
from core.db import DatabaseManager


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Delete refresh tokens that expired beyond retention days",
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=getattr(config, "AUTH_REFRESH_TOKEN_RETENTION_DAYS", 90),
        help="Keep expired records within this many days for audit/troubleshooting",
    )
    args = parser.parse_args()

    if args.retention_days < 0:
        raise SystemExit("retention-days must be >= 0")

    db = DatabaseManager(str(config.DATABASE_PATH))
    deleted = db.cleanup_expired_refresh_tokens(retention_days=args.retention_days)
    print(f"deleted={deleted}")
    print(f"retention_days={args.retention_days}")
    print(f"database={config.DATABASE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
