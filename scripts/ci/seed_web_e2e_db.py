#!/usr/bin/env python3
"""准备 Web e2e 本地后端数据库。"""

from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: seed_web_e2e_db.py <db_path>")

    db_path = Path(sys.argv[1]).expanduser().resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("KONA_DATABASE_PATH", str(db_path))
    os.environ.setdefault("JWT_SECRET", "web-e2e-secret")

    from core.auth import hash_password
    from core.db import DatabaseManager

    if db_path.exists():
        db_path.unlink()
    wal = db_path.with_name(f"{db_path.name}-wal")
    shm = db_path.with_name(f"{db_path.name}-shm")
    if wal.exists():
        wal.unlink()
    if shm.exists():
        shm.unlink()

    db = DatabaseManager(str(db_path))
    user = db.create_user(
        username="konae",
        password_hash=hash_password("qq111111"),
        user_id="u_web_e2e",
    )
    db.set_user_build_start_at(user["id"], "2026-03-01")
    db.add_cash_asset("测试钱包", 12888.0, user_id=user["id"])
    db.add_other_asset("测试黄金", 88.0, user_id=user["id"], icon="📦")
    db.add_asset(
        {
            "code": "sh600000",
            "name": "浦发银行",
            "qty": 100,
            "price": 10.5,
            "curr": "CNY",
            "asset_type": "a",
            "adjustment": 0.0,
        },
        user_id=user["id"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
