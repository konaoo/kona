#!/usr/bin/env python3
"""
Verify today's snapshot exists (Asia/Shanghai date).
On failure, sends alert email and exits non-zero.
"""
import os
import socket
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

from alert_sender import send_alert


DB_PATH = os.getenv("KONA_DATABASE_PATH", "/home/ec2-user/portfolio/kona_tool/portfolio.db")


def main() -> int:
    hostname = socket.gethostname()
    today_cn = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM daily_snapshots WHERE date = ?",
            (today_cn,),
        )
        count = int(cur.fetchone()[0])
        conn.close()
    except Exception as e:  # noqa: BLE001
        subject = f"[Kona][ALERT] Snapshot check error on {hostname}"
        body = (
            f"DB: {DB_PATH}\n"
            f"Date(Asia/Shanghai): {today_cn}\n"
            f"Error: {e}\n"
        )
        try:
            send_alert(subject, body)
        except Exception as send_err:  # noqa: BLE001
            print(f"failed to send alert email: {send_err}")
        print(body)
        return 1

    if count <= 0:
        subject = f"[Kona][ALERT] Snapshot missing on {hostname}"
        body = (
            f"DB: {DB_PATH}\n"
            f"Date(Asia/Shanghai): {today_cn}\n"
            "Result: no daily snapshot row found.\n"
        )
        try:
            send_alert(subject, body)
        except Exception as send_err:  # noqa: BLE001
            print(f"failed to send alert email: {send_err}")
        print(body)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
