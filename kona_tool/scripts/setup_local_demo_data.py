#!/usr/bin/env python3
"""重建本地固定测试账号和联调样例数据。

只用于本地开发库：
- 固定 `konae / qq111111`
- 提权为管理员
- 补用户侧和后台常用样例数据
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
DEFAULT_DB_PATH = KONA_TOOL / "portfolio.db"

if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))

from core.auth import hash_password  # noqa: E402


PASSWORD = "qq111111"
PRIMARY_USER_ID = "u_today_buy"
PRIMARY_USERNAME = "konae"
SEEDED_USER_IDS = {
    PRIMARY_USER_ID,
    "u_demo_alpha",
    "u_demo_beta",
    "u_demo_disabled",
}
SEEDED_USERNAMES = {
    PRIMARY_USERNAME,
    "demo_alpha",
    "demo_beta",
    "demo_disabled",
}
SEED_NOTE = "local_demo_seed"
DEMO_INVITE_CODES = [
    ("KONA8A1B2C", "active"),
    ("KONA8D3E4F", "active"),
    ("KONA8G5H6J", "active"),
    ("KONA8K7L8M", "active"),
    ("KONA8N9P2Q", "active"),
    ("KONA8R3S4T", "active"),
    ("KONA8U5V6W", "used"),
    ("KONA8X7Y8Z", "revoked"),
]


@dataclass(frozen=True)
class DemoUser:
    user_id: str
    username: str
    nickname: str
    is_admin: int
    status: str
    register_method: str
    user_number: int
    created_at: str
    last_login: str
    last_active_at: str


def now_local() -> datetime:
    return datetime.now().astimezone()


def fmt_local(dt: datetime) -> str:
    return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")


def fmt_date(dt: datetime) -> str:
    return dt.astimezone().strftime("%Y-%m-%d")


def fmt_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def backup_db(db_path: Path) -> Path:
    stamp = now_local().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.with_name(f"{db_path.name}.{stamp}.bak")
    shutil.copy2(db_path, backup_path)
    return backup_path


def ensure_db_exists(db_path: Path) -> None:
    if not db_path.exists():
        raise FileNotFoundError(f"本地数据库不存在：{db_path}")


def seed_users(cursor: sqlite3.Cursor, now: datetime) -> None:
    users = [
        DemoUser(
            user_id=PRIMARY_USER_ID,
            username=PRIMARY_USERNAME,
            nickname="本地测试管理员",
            is_admin=1,
            status="active",
            register_method="local_demo",
            user_number=10001,
            created_at=fmt_local(now - timedelta(days=35)),
            last_login=fmt_local(now - timedelta(minutes=5)),
            last_active_at=fmt_local(now - timedelta(minutes=2)),
        ),
        DemoUser(
            user_id="u_demo_alpha",
            username="demo_alpha",
            nickname="示例用户甲",
            is_admin=0,
            status="active",
            register_method="invite",
            user_number=10002,
            created_at=fmt_local(now - timedelta(days=15)),
            last_login=fmt_local(now - timedelta(hours=3)),
            last_active_at=fmt_local(now - timedelta(hours=1)),
        ),
        DemoUser(
            user_id="u_demo_beta",
            username="demo_beta",
            nickname="示例用户乙",
            is_admin=0,
            status="active",
            register_method="phone",
            user_number=10003,
            created_at=fmt_local(now - timedelta(days=7)),
            last_login=fmt_local(now - timedelta(days=1, hours=2)),
            last_active_at=fmt_local(now - timedelta(days=1, minutes=20)),
        ),
        DemoUser(
            user_id="u_demo_disabled",
            username="demo_disabled",
            nickname="停用示例用户",
            is_admin=0,
            status="disabled",
            register_method="invite",
            user_number=10004,
            created_at=fmt_local(now - timedelta(days=60)),
            last_login=fmt_local(now - timedelta(days=10)),
            last_active_at=fmt_local(now - timedelta(days=10)),
        ),
    ]
    password_hash = hash_password(PASSWORD)
    for item in users:
        cursor.execute(
            """
            INSERT INTO users (
                id, username, password_hash,
                legacy_needs_password_setup, must_change_password,
                password_updated_at, nickname, register_method, user_number,
                is_admin, status, created_at, last_login, last_active_at,
                last_login_ip, last_login_region, last_active_ip, last_active_region
            ) VALUES (?, ?, ?, 0, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, '127.0.0.1', '本机', '127.0.0.1', '本机')
            ON CONFLICT(id) DO UPDATE SET
                username=excluded.username,
                password_hash=excluded.password_hash,
                legacy_needs_password_setup=0,
                must_change_password=0,
                password_updated_at=excluded.password_updated_at,
                nickname=excluded.nickname,
                register_method=excluded.register_method,
                user_number=excluded.user_number,
                is_admin=excluded.is_admin,
                status=excluded.status,
                created_at=excluded.created_at,
                last_login=excluded.last_login,
                last_active_at=excluded.last_active_at,
                last_login_ip=excluded.last_login_ip,
                last_login_region=excluded.last_login_region,
                last_active_ip=excluded.last_active_ip,
                last_active_region=excluded.last_active_region
            """,
            (
                item.user_id,
                item.username,
                password_hash,
                fmt_local(now),
                item.nickname,
                item.register_method,
                item.user_number,
                item.is_admin,
                item.status,
                item.created_at,
                item.last_login,
                item.last_active_at,
            ),
        )


def seed_activity(cursor: sqlite3.Cursor, now: datetime) -> None:
    cursor.execute("DELETE FROM user_daily_activity WHERE user_id IN (?, ?, ?, ?)", tuple(SEEDED_USER_IDS))
    user_days = {
        PRIMARY_USER_ID: [0, 1, 2, 3, 5, 8, 13, 21, 30],
        "u_demo_alpha": [0, 1, 2, 4, 7, 10],
        "u_demo_beta": [1, 3, 6],
        "u_demo_disabled": [10, 20, 30],
    }
    for user_id, offsets in user_days.items():
        for offset in offsets:
            day = now - timedelta(days=offset)
            cursor.execute(
                """
                INSERT OR REPLACE INTO user_daily_activity (
                    user_id, activity_date, first_seen_at, last_seen_at
                ) VALUES (?, ?, ?, ?)
                """,
                (user_id, fmt_date(day), fmt_local(day.replace(hour=9, minute=0, second=0)), fmt_local(day.replace(hour=21, minute=0, second=0))),
            )


def cleanup_seeded_rows(cursor: sqlite3.Cursor) -> None:
    placeholders = ", ".join("?" for _ in SEEDED_USER_IDS)
    for table in [
        "auth_refresh_tokens",
        "cash_assets",
        "other_assets",
        "liabilities",
        "portfolio",
        "transactions",
        "daily_snapshots",
        "daily_snapshot_market_breakdowns",
        "portfolio_adjustment_ledger",
        "portfolio_correction_logs",
        "portfolio_legacy_adjustment_states",
        "asset_adjustments",
        "ai_credit_ledger",
    ]:
        cursor.execute(f"DELETE FROM {table} WHERE user_id IN ({placeholders})", tuple(SEEDED_USER_IDS))
    for table in [
        "portfolio",
        "cash_assets",
        "other_assets",
        "liabilities",
        "transactions",
        "daily_snapshots",
        "daily_snapshot_market_breakdowns",
    ]:
        cursor.execute(f"DELETE FROM {table} WHERE user_id IS NULL OR TRIM(COALESCE(user_id, '')) = ''")
    cursor.execute(
        "DELETE FROM admin_audit_logs WHERE admin_user_id IN (?, ?) OR COALESCE(error, '') = ? OR COALESCE(request_body, '') LIKE ?",
        (PRIMARY_USER_ID, "u_demo_alpha", SEED_NOTE, f"%{SEED_NOTE}%"),
    )
    cursor.execute("DELETE FROM invite_codes WHERE batch_id = ?", (SEED_NOTE,))
    cursor.execute("DELETE FROM runtime_configs WHERE updated_by = ?", (PRIMARY_USER_ID,))
    cursor.execute("DELETE FROM price_alert_reports WHERE report_date IN ('2026-03-21', '2026-03-22')")
    cursor.execute("DELETE FROM provider_test_reports WHERE report_slot IN ('2026-03-22T00', '2026-03-22T08')")


def seed_sessions(cursor: sqlite3.Cursor, now: datetime) -> None:
    future = fmt_local(now + timedelta(days=30))
    issued = fmt_local(now - timedelta(hours=2))
    rows = [
        (PRIMARY_USER_ID, "localdemo-refresh-konae", "device-web-konae"),
        ("u_demo_alpha", "localdemo-refresh-alpha", "device-ios-alpha"),
    ]
    for user_id, token_hash, device_id in rows:
        cursor.execute(
            """
            INSERT INTO auth_refresh_tokens (
                user_id, token_hash, device_id, issued_at, expires_at, revoked_at, last_used_at
            ) VALUES (?, ?, ?, ?, ?, NULL, ?)
            """,
            (user_id, token_hash, device_id, issued, future, fmt_local(now - timedelta(minutes=30))),
        )


def seed_assets(cursor: sqlite3.Cursor, now: datetime) -> None:
    cash_assets = [
        ("招商银行", 128000.0, "CNY", "🏦"),
        ("港币账户", 35000.0, "HKD", "💴"),
        ("美元账户", 8200.0, "USD", "💵"),
    ]
    for name, amount, curr, icon in cash_assets:
        cursor.execute(
            """
            INSERT INTO cash_assets (name, amount, curr, user_id, created_at, updated_at, icon)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (name, amount, curr, PRIMARY_USER_ID, fmt_local(now - timedelta(days=3)), fmt_local(now), icon),
        )

    other_assets = [
        ("黄金积存金", 18000.0, "CNY", "🥇"),
        ("备用器材", 6000.0, "CNY", "📦"),
    ]
    for name, amount, curr, icon in other_assets:
        cursor.execute(
            """
            INSERT INTO other_assets (name, amount, curr, user_id, created_at, updated_at, icon)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (name, amount, curr, PRIMARY_USER_ID, fmt_local(now - timedelta(days=12)), fmt_local(now), icon),
        )

    liabilities = [
        ("招商信用卡", 6800.0, "CNY", "💳"),
        ("花呗", 3200.0, "CNY", "🧾"),
    ]
    for name, amount, curr, icon in liabilities:
        cursor.execute(
            """
            INSERT INTO liabilities (name, amount, curr, user_id, created_at, updated_at, icon)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (name, amount, curr, PRIMARY_USER_ID, fmt_local(now - timedelta(days=2)), fmt_local(now), icon),
        )

    portfolio_rows = [
        ("sh600519", "贵州茅台", 20.0, 1450.0, "CNY", 0.0, "a"),
        ("hk00700", "腾讯控股", 200.0, 310.0, "HKD", 0.0, "hk"),
        ("gb_aapl", "苹果", 15.0, 182.0, "USD", 0.0, "us"),
        ("f_110017", "易方达增强回报债券A", 10000.0, 1.053, "CNY", 0.0, "fund"),
    ]
    for code, name, qty, price, curr, adjustment, asset_type in portfolio_rows:
        cursor.execute(
            """
            INSERT INTO portfolio (
                code, name, qty, price, curr, adjustment, asset_type, user_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                code,
                name,
                qty,
                price,
                curr,
                adjustment,
                asset_type,
                PRIMARY_USER_ID,
                fmt_local(now - timedelta(days=25)),
                fmt_local(now),
            ),
        )

    tx_rows = [
        ("2026-02-18 09:35:00", "sh600519", "贵州茅台", "buy", 1450.0, 20.0, 29000.0, 0.0, "CNY", "a", "2026-02-18"),
        ("2026-03-02 10:20:00", "hk00700", "腾讯控股", "buy", 310.0, 200.0, 62000.0, 0.0, "HKD", "hk", "2026-03-02"),
        ("2026-03-10 22:15:00", "gb_aapl", "苹果", "buy", 182.0, 15.0, 2730.0, 0.0, "USD", "us", "2026-03-10"),
        ("2026-03-04 14:05:00", "f_110017", "易方达增强回报债券A", "buy", 1.053, 10000.0, 10530.0, 0.0, "CNY", "fund", "2026-03-05"),
    ]
    for row in tx_rows:
        cursor.execute(
            """
            INSERT INTO transactions (
                time, code, name, type, price, qty, amount, pnl,
                user_id, created_at, curr, market, effective_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            row[:8] + (PRIMARY_USER_ID, row[0], row[8], row[9], row[10]),
        )

    ledger_rows = [
        ("gb_aapl", "dividend", 28.5, "USD", "本地样例现金分红"),
        ("hk00700", "fee", -40.0, "HKD", "本地样例交易手续费"),
    ]
    for code, event_type, amount, curr, note in ledger_rows:
        cursor.execute(
            """
            INSERT INTO portfolio_adjustment_ledger (
                user_id, code, event_type, amount, curr, note, source, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'local_demo', ?, ?)
            """,
            (PRIMARY_USER_ID, code, event_type, amount, curr, note, fmt_local(now - timedelta(days=1)), fmt_local(now)),
        )


def seed_snapshots(cursor: sqlite3.Cursor) -> None:
    base_dates = [datetime(2026, 3, day, 18, 0, 0).astimezone() for day in range(1, 21)]
    day_pnls = [
        0.0, 5550.0, 3054.0, -6336.0, 3443.0,
        5088.0, 0.0, 0.0, -5774.0, 2266.0,
        10000.0, 2688.0, -2616.0, 0.0, 0.0,
        1527.0, 3638.0, -1850.0, -1251.0, -2772.0,
    ]
    total_invest = 394200.0
    total_cash = 390000.0
    total_other = 24000.0
    total_liability = 10000.0
    cumulative = 0.0
    for dt, day_pnl in zip(base_dates, day_pnls):
        cumulative += day_pnl
        total_asset = total_invest + total_cash + total_other - total_liability + cumulative
        cursor.execute(
            """
            INSERT INTO daily_snapshots (
                date, total_asset, total_invest, total_cash, total_other,
                total_liability, total_pnl, day_pnl, user_id, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fmt_date(dt),
                round(total_asset, 2),
                total_invest,
                total_cash,
                total_other,
                total_liability,
                round(cumulative, 2),
                round(day_pnl, 2),
                PRIMARY_USER_ID,
                fmt_local(dt),
            ),
        )
        market_map = {
            "a": round(day_pnl * 0.42, 2),
            "hk": round(day_pnl * 0.23, 2),
            "us": round(day_pnl * 0.19, 2),
            "fund": round(day_pnl - round(day_pnl * 0.42, 2) - round(day_pnl * 0.23, 2) - round(day_pnl * 0.19, 2), 2),
        }
        meta_json = json.dumps({"source": SEED_NOTE, "date": fmt_date(dt)}, ensure_ascii=False)
        for market, value in market_map.items():
            cursor.execute(
                """
                INSERT INTO daily_snapshot_market_breakdowns (
                    date, user_id, market, day_pnl, source, confidence, meta_json, updated_at
                ) VALUES (?, ?, ?, ?, 'exact', 1.0, ?, ?)
                """,
                (fmt_date(dt), PRIMARY_USER_ID, market, value, meta_json, fmt_local(dt)),
            )

    latest_snapshots = [
        ("u_demo_alpha", "2026-03-20", 182000.0, 126000.0, 52000.0, 8000.0, 4000.0, 42000.0, 1800.0),
        ("u_demo_beta", "2026-03-20", 96000.0, 68000.0, 22000.0, 12000.0, 6000.0, 18000.0, -600.0),
        ("u_demo_disabled", "2026-03-12", 12000.0, 8000.0, 5000.0, 1000.0, 2000.0, 3000.0, 0.0),
    ]
    for user_id, date_str, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl in latest_snapshots:
        cursor.execute(
            """
            INSERT INTO daily_snapshots (
                date, total_asset, total_invest, total_cash, total_other,
                total_liability, total_pnl, day_pnl, user_id, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                date_str,
                total_asset,
                total_invest,
                total_cash,
                total_other,
                total_liability,
                total_pnl,
                day_pnl,
                user_id,
                f"{date_str} 18:00:00",
            ),
        )


def seed_admin_side(cursor: sqlite3.Cursor, now: datetime) -> None:
    for code, status in DEMO_INVITE_CODES:
        used_by = "u_demo_alpha" if status == "used" else None
        used_at = fmt_local(now - timedelta(days=6)) if status == "used" else None
        cursor.execute(
            """
            INSERT INTO invite_codes (
                code, batch_id, status, created_by, created_at, used_by_user_id, used_at, note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (code, SEED_NOTE, status, PRIMARY_USER_ID, fmt_local(now - timedelta(days=8)), used_by, used_at, "本地后台样例邀请码"),
        )

    runtime_rows = [
        ("ops.invite_acquire.text", "本地联调用：扫码加微信获取邀请码。", PRIMARY_USER_ID),
        ("ops.invite_acquire.image_url", "https://example.com/local-invite-qrcode.png", PRIMARY_USER_ID),
        ("ops.user_group.text", "本地样例用户群：仅供联调展示。", PRIMARY_USER_ID),
        ("ops.app_update.latest_version", "12.0.1-local", PRIMARY_USER_ID),
    ]
    for key, value, updated_by in runtime_rows:
        cursor.execute(
            """
            INSERT INTO runtime_configs (key, value, updated_by, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value=excluded.value,
                updated_by=excluded.updated_by,
                updated_at=excluded.updated_at
            """,
            (key, value, updated_by, fmt_local(now)),
        )

    audits = [
        ("admin.users.update", "user", "u_demo_beta", "POST", "/api/admin/users/u_demo_beta/update", 200, "success", ""),
        ("admin.invites.generate", "invite", "KONA8A1B2C", "POST", "/api/admin/invites/generate", 200, "success", ""),
        ("admin.config.update", "config", "ops.invite_acquire.text", "POST", "/api/admin/config/update", 500, "failed", SEED_NOTE),
    ]
    for action, target_type, target_id, method, path, status_code, result, error in audits:
        cursor.execute(
            """
            INSERT INTO admin_audit_logs (
                admin_user_id, action, target_type, target_id, method, path,
                ip, request_body, status_code, result, error, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, '127.0.0.1', ?, ?, ?, ?, ?)
            """,
            (
                PRIMARY_USER_ID,
                action,
                target_type,
                target_id,
                method,
                path,
                json.dumps({"seed": SEED_NOTE}, ensure_ascii=False),
                status_code,
                result,
                error,
                fmt_local(now - timedelta(hours=2 if result == "success" else 1)),
            ),
        )

    cursor.execute(
        """
        INSERT INTO price_alert_reports (
            report_date, tested_at_utc, total_assets, alert_count, summary_json, items_json, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "2026-03-22",
            fmt_utc(now),
            4,
            1,
            json.dumps({"ok": 3, "alert": 1, "source": SEED_NOTE}, ensure_ascii=False),
            json.dumps(
                [
                    {
                        "code": "hk00700",
                        "name": "腾讯控股",
                        "market": "hk",
                        "message": "价格波动超出本地样例阈值",
                    }
                ],
                ensure_ascii=False,
            ),
            fmt_local(now),
        ),
    )
    cursor.execute(
        """
        INSERT INTO provider_test_reports (
            report_slot, tested_at_utc, summary_json, providers_json, updated_at
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            "2026-03-22T08",
            fmt_utc(now),
            json.dumps({"ok": 2, "failed": 1, "source": SEED_NOTE}, ensure_ascii=False),
            json.dumps(
                {
                    "tencent": {"ok": True, "latency_ms": 82},
                    "sina": {"ok": True, "latency_ms": 105},
                    "eastmoney": {"ok": False, "latency_ms": 0, "error": "本地样例超时"},
                },
                ensure_ascii=False,
            ),
            fmt_local(now),
        ),
    )


def summarize(cursor: sqlite3.Cursor) -> dict:
    summary: dict[str, int] = {}
    cursor.execute("SELECT COUNT(*) FROM users")
    summary["users"] = int(cursor.fetchone()[0])
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
    summary["admin_users"] = int(cursor.fetchone()[0])
    cursor.execute("SELECT COUNT(*) FROM portfolio WHERE user_id = ?", (PRIMARY_USER_ID,))
    summary["portfolio_assets"] = int(cursor.fetchone()[0])
    cursor.execute("SELECT COUNT(*) FROM cash_assets WHERE user_id = ?", (PRIMARY_USER_ID,))
    summary["cash_assets"] = int(cursor.fetchone()[0])
    cursor.execute("SELECT COUNT(*) FROM daily_snapshots WHERE user_id = ?", (PRIMARY_USER_ID,))
    summary["snapshots"] = int(cursor.fetchone()[0])
    cursor.execute("SELECT COUNT(*) FROM invite_codes WHERE batch_id = ?", (SEED_NOTE,))
    summary["invites"] = int(cursor.fetchone()[0])
    return summary


def run(db_path: Path, do_backup: bool) -> None:
    ensure_db_exists(db_path)
    backup_path = backup_db(db_path) if do_backup else None
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    now = now_local()
    try:
        cleanup_seeded_rows(cursor)
        seed_users(cursor, now)
        seed_activity(cursor, now)
        seed_sessions(cursor, now)
        seed_assets(cursor, now)
        seed_snapshots(cursor)
        seed_admin_side(cursor, now)
        conn.commit()
        payload = summarize(cursor)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print("本地样例数据已完成。")
    print(f"数据库: {db_path}")
    if backup_path:
        print(f"备份: {backup_path}")
    print(f"固定账号: {PRIMARY_USERNAME} / {PASSWORD}")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="重建本地固定测试账号和样例数据")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="本地数据库路径")
    parser.add_argument("--no-backup", action="store_true", help="跳过备份")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(Path(args.db).expanduser().resolve(), do_backup=not args.no_backup)
