#!/usr/bin/env python3
"""
生成并持久化价格异常巡检日报。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config
from core.admin.monitoring import (
    load_price_alerts_payload,
    save_price_alert_report_snapshot,
    set_admin_db,
)
from core.db import DatabaseManager


def _noop_admin_write_audit(*args, **kwargs):
    def decorator(fn):
        return fn

    return decorator


def main() -> int:
    db = DatabaseManager(str(config.DATABASE_PATH))
    set_admin_db(db)
    payload = load_price_alerts_payload()
    save_price_alert_report_snapshot(payload)
    print(
        json.dumps(
            {
                "tested_at_utc": payload.get("tested_at_utc"),
                "total_assets": int(payload.get("total_assets") or 0),
                "alert_count": int(payload.get("alert_count") or 0),
                "summary": payload.get("summary") or {},
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
