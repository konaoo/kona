#!/usr/bin/env python3
"""
盘点当前库里的 legacy adjustment 残留情况。

只读，不写库。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
APP_DIR = SCRIPT_DIR.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from core.db import DatabaseManager  # noqa: E402
import config  # noqa: E402


def _format_user_label(user_id: str) -> str:
    return user_id or "本地默认用户"


def _print_single_report(report: dict) -> None:
    user_id = str(report.get("user_id") or "")
    print(f"用户: {_format_user_label(user_id)}")
    print(f"当前状态: {report.get('migration_status')}")
    print(f"已切忽略旧值: {'是' if report.get('legacy_adjustment_ignored') else '否'}")
    print(f"持仓数: {int(report.get('position_count') or 0)}")
    print(f"含旧值持仓数: {int(report.get('nonzero_legacy_position_count') or 0)}")
    print(f"旧值合计: {float(report.get('nonzero_legacy_adjustment_total') or 0.0):.6f}")
    print("明细:")
    positions = report.get("positions") or []
    if not positions:
        print("- 当前没有持仓")
        return
    for item in positions:
        code = str(item.get("code") or "")
        name = str(item.get("name") or "")
        legacy_adjustment = float(item.get("legacy_adjustment") or 0.0)
        ledger_adjustment = float(item.get("ledger_adjustment") or 0.0)
        realized_adjustment = float(item.get("realized_pnl_adjustment") or 0.0)
        print(
            "- "
            f"{code} {name} | 旧值={legacy_adjustment:.6f} | "
            f"收益事件={ledger_adjustment:.6f} | 已实现盈亏={realized_adjustment:.6f} | "
            f"交易数={int(item.get('tx_count') or 0)} | 修正数={int(item.get('correction_count') or 0)} | "
            f"{item.get('migration_hint')}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="盘点投资持仓 legacy adjustment 残留情况")
    parser.add_argument("--user-id", default="", help="只看指定 user_id")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    db = DatabaseManager(str(config.DATABASE_PATH))
    if args.user_id:
        payload = db.get_portfolio_legacy_adjustment_migration_report(args.user_id)
    else:
        reports = db.list_portfolio_legacy_adjustment_migration_reports()
        ready_count = sum(1 for item in reports if bool(item.get("ready_to_ignore_now")))
        payload = {
            "report_count": len(reports),
            "ready_to_ignore_count": ready_count,
            "review_required_count": max(0, len(reports) - ready_count),
            "reports": reports,
        }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.user_id:
        _print_single_report(payload)
        return 0

    reports = payload.get("reports") or []
    print(f"共盘点用户数: {int(payload.get('report_count') or 0)}")
    print(f"可直接切新口径: {int(payload.get('ready_to_ignore_count') or 0)}")
    print(f"仍需人工迁移: {int(payload.get('review_required_count') or 0)}")
    for report in reports:
        print("")
        _print_single_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
