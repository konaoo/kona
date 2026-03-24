"""
管理后台：快照 / 备份恢复 / 数据归属迁移路由。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

import config
from flask import jsonify, request

from core.admin import common as admin_common
from core.auth import admin_required
from core.snapshot import take_snapshot


def _parse_cleanup_markets(data: Dict[str, Any]) -> List[str]:
    raw = data.get("markets", ["a", "hk", "us", "fund"])
    if isinstance(raw, str):
        values = [part.strip() for part in raw.split(",")]
    elif isinstance(raw, list):
        values = [str(item).strip() for item in raw]
    else:
        values = []
    allowed = {"a", "hk", "us", "fund"}
    result: List[str] = []
    for value in values:
        market = value.lower()
        if market in allowed and market not in result:
            result.append(market)
    return result or ["a", "hk", "us", "fund"]


def register_admin_data_routes(bp, db, admin_write_audit) -> None:
    @bp.route("/data/snapshots", methods=["GET"])
    @admin_required
    def admin_data_snapshots():
        user_id = request.args.get("user_id", "").strip()
        start_date = request.args.get("start_date", "").strip()
        end_date = request.args.get("end_date", "").strip()
        limit = max(1, min(request.args.get("limit", 100, type=int), 500))
        offset = max(0, request.args.get("offset", 0, type=int))

        where = []
        params: List[Any] = []
        if user_id:
            where.append("ds.user_id = ?")
            params.append(user_id)
        if start_date:
            where.append("ds.date >= ?")
            params.append(start_date)
        if end_date:
            where.append("ds.date <= ?")
            params.append(end_date)
        where_sql = f"WHERE {' AND '.join(where)}" if where else ""

        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"""
                SELECT
                    ds.id,
                    ds.date,
                    ds.user_id,
                    COALESCE(u.username, '') AS username,
                    u.user_number AS user_number,
                    ds.total_asset,
                    ds.total_invest,
                    ds.total_cash,
                    ds.total_other,
                    ds.total_liability,
                    ds.total_pnl,
                    ds.day_pnl,
                    ds.updated_at
                FROM daily_snapshots ds
                LEFT JOIN users u ON u.id = ds.user_id
                {where_sql}
                ORDER BY ds.date DESC, ds.user_id ASC
                LIMIT ? OFFSET ?
                """,
                tuple(params + [limit, offset]),
            )
            items = [dict(row) for row in cursor.fetchall()]
            return jsonify({"items": items, "limit": limit, "offset": offset})
        finally:
            conn.close()

    @bp.route("/data/snapshot/trigger", methods=["POST"])
    @admin_write_audit(action="admin.data.snapshot.trigger", target_type="snapshot")
    @admin_required
    def admin_data_snapshot_trigger():
        success = take_snapshot()
        if success:
            return jsonify({"status": "ok", "message": "Snapshot taken successfully"})
        return jsonify({"error": "Failed to take snapshot"}), 500

    @bp.route("/data/snapshot/health", methods=["GET"])
    @admin_required
    def admin_data_snapshot_health():
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            now = datetime.now()
            today_str = now.strftime("%Y-%m-%d")
            yesterday_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")

            cursor.execute(
                """
                SELECT
                    ds.user_id,
                    COALESCE(u.username, '') AS username,
                    COUNT(*) AS total_snapshots,
                    MIN(ds.date) AS earliest_date,
                    MAX(ds.date) AS latest_date,
                    MAX(ds.updated_at) AS last_updated_at
                FROM daily_snapshots ds
                LEFT JOIN users u ON u.id = ds.user_id
                GROUP BY ds.user_id
                ORDER BY total_snapshots DESC
                """
            )
            user_rows = cursor.fetchall()

            users = []
            max_gap_days = 0
            for row in user_rows:
                latest = str(row["latest_date"] or "")
                if latest:
                    try:
                        latest_dt = datetime.strptime(latest, "%Y-%m-%d")
                        gap_days = (now - latest_dt).days
                    except ValueError:
                        gap_days = -1
                else:
                    gap_days = -1

                has_today = latest == today_str
                has_yesterday = latest == yesterday_str

                if gap_days > max_gap_days:
                    max_gap_days = gap_days

                users.append(
                    {
                        "user_id": row["user_id"],
                        "username": row["username"],
                        "total_snapshots": int(row["total_snapshots"] or 0),
                        "earliest_date": str(row["earliest_date"] or ""),
                        "latest_date": latest,
                        "last_updated_at": str(row["last_updated_at"] or ""),
                        "gap_days": gap_days,
                        "has_today": has_today,
                        "status": "ok" if has_today else ("recent" if has_yesterday else "stale"),
                    }
                )

            cursor.execute(
                "SELECT COUNT(DISTINCT user_id) AS c FROM daily_snapshots WHERE date = ?",
                (today_str,),
            )
            row = cursor.fetchone()
            today_count = int(row["c"] if row else 0)

            cursor.execute("SELECT COUNT(DISTINCT user_id) AS c FROM daily_snapshots")
            row = cursor.fetchone()
            total_users = int(row["c"] if row else 0)

            if max_gap_days <= 0:
                cron_status = "healthy"
            elif max_gap_days <= 1:
                cron_status = "recent"
            elif max_gap_days <= 3:
                cron_status = "warning"
            else:
                cron_status = "critical"

            return jsonify(
                {
                    "status": cron_status,
                    "server_time": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "today": today_str,
                    "today_snapshot_users": today_count,
                    "total_users": total_users,
                    "max_gap_days": max_gap_days,
                    "users": users,
                }
            )
        finally:
            conn.close()

    @bp.route("/data/snapshot/cleanup_weekend", methods=["POST"])
    @admin_write_audit(action="admin.data.snapshot.cleanup_weekend", target_type="snapshot")
    @admin_required
    def admin_data_snapshot_cleanup_weekend():
        data = admin_common.json_body()
        user_id = str(data.get("user_id", "")).strip()
        start_date = str(data.get("start_date", "")).strip()
        end_date = str(data.get("end_date", "")).strip()

        sql = """
            UPDATE daily_snapshots
            SET day_pnl = 0, updated_at = datetime('now','localtime')
            WHERE CAST(strftime('%w', date) AS INTEGER) IN (0, 6)
        """
        params: List[Any] = []
        if user_id:
            sql += " AND user_id = ?"
            params.append(user_id)
        if start_date:
            sql += " AND date >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND date <= ?"
            params.append(end_date)

        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, tuple(params))
            cleaned = cursor.rowcount
            conn.commit()
            return jsonify({"status": "ok", "cleaned": cleaned})
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @bp.route("/data/snapshot/cleanup_weekend/preview", methods=["POST"])
    @admin_required
    def admin_data_snapshot_cleanup_weekend_preview():
        data = admin_common.json_body()
        user_id = str(data.get("user_id", "")).strip()
        start_date = str(data.get("start_date", "")).strip()
        end_date = str(data.get("end_date", "")).strip()
        sql = """
            SELECT COUNT(1) AS c
            FROM daily_snapshots
            WHERE CAST(strftime('%w', date) AS INTEGER) IN (0, 6)
        """
        params: List[Any] = []
        if user_id:
            sql += " AND user_id = ?"
            params.append(user_id)
        if start_date:
            sql += " AND date >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND date <= ?"
            params.append(end_date)
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, tuple(params))
            row = cursor.fetchone()
            return jsonify({"status": "ok", "affected": int((row["c"] if row else 0) or 0)})
        finally:
            conn.close()

    @bp.route("/data/snapshot/cleanup_market_closed/preview", methods=["POST"])
    @admin_required
    def admin_data_snapshot_cleanup_market_closed_preview():
        data = admin_common.json_body()
        user_id = str(data.get("user_id", "")).strip()
        start_date = str(data.get("start_date", "")).strip()
        end_date = str(data.get("end_date", "")).strip()
        markets = _parse_cleanup_markets(data)
        affected = db.preview_cleanup_market_closed(
            markets=markets,
            user_id=user_id or None,
            start_date=start_date,
            end_date=end_date,
        )
        return jsonify({"status": "ok", "affected": int(affected or 0), "markets": markets})

    @bp.route("/data/snapshot/cleanup_market_closed", methods=["POST"])
    @admin_write_audit(action="admin.data.snapshot.cleanup_market_closed", target_type="snapshot")
    @admin_required
    def admin_data_snapshot_cleanup_market_closed():
        data = admin_common.json_body()
        user_id = str(data.get("user_id", "")).strip()
        start_date = str(data.get("start_date", "")).strip()
        end_date = str(data.get("end_date", "")).strip()
        markets = _parse_cleanup_markets(data)
        cleaned = db.cleanup_market_closed_day_pnl(
            markets=markets,
            user_id=user_id or None,
            start_date=start_date,
            end_date=end_date,
        )
        return jsonify({"status": "ok", "cleaned": int(cleaned or 0), "markets": markets})

    @bp.route("/data/backup", methods=["POST"])
    @admin_write_audit(action="admin.data.backup", target_type="backup")
    @admin_required
    def admin_data_backup():
        data = admin_common.json_body()
        backup_dir = str(data.get("backup_dir", "")).strip() or str(config.BASE_DIR / "archive" / "backups")
        try:
            retention_days = int(data.get("retention_days", 14))
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid retention_days"}), 400
        if retention_days < 1:
            return jsonify({"error": "retention_days must be >= 1"}), 400

        script = admin_common.load_script_module(
            config.BASE_DIR / "scripts" / "backup_portfolio_db.py",
            "backup_portfolio_db",
        )
        backup_file = script.create_backup(str(config.DATABASE_PATH), backup_dir)
        deleted = script.prune_old_backups(backup_dir, retention_days)

        return jsonify(
            {
                "status": "ok",
                "backup_file": backup_file,
                "backup_dir": backup_dir,
                "retention_days": retention_days,
                "deleted_count": len(deleted),
                "deleted": deleted,
            }
        )

    @bp.route("/data/backup/latest", methods=["GET"])
    @admin_required
    def admin_data_backup_latest():
        backup_dir = request.args.get("backup_dir", "").strip() or str(config.BASE_DIR / "archive" / "backups")
        script = admin_common.load_script_module(
            config.BASE_DIR / "scripts" / "restore_portfolio_db.py",
            "restore_portfolio_db",
        )
        try:
            latest = script.find_latest_backup(backup_dir)
            latest_path = Path(latest)
            return jsonify(
                {
                    "status": "ok",
                    "backup_file": latest,
                    "backup_dir": backup_dir,
                    "modified_at": datetime.fromtimestamp(
                        latest_path.stat().st_mtime,
                        timezone.utc,
                    ).isoformat(),
                    "size_bytes": latest_path.stat().st_size,
                }
            )
        except FileNotFoundError:
            return jsonify({"status": "ok", "backup_file": "", "backup_dir": backup_dir})

    @bp.route("/data/restore", methods=["POST"])
    @admin_write_audit(action="admin.data.restore", target_type="backup")
    @admin_required
    def admin_data_restore():
        data = admin_common.json_body()
        backup_dir = str(data.get("backup_dir", "")).strip() or str(config.BASE_DIR / "archive" / "backups")
        backup_file = str(data.get("backup_file", "")).strip()

        script = admin_common.load_script_module(
            config.BASE_DIR / "scripts" / "restore_portfolio_db.py",
            "restore_portfolio_db",
        )
        try:
            if not backup_file:
                backup_file = script.find_latest_backup(backup_dir)
            result = script.restore_backup(str(config.DATABASE_PATH), backup_file)
            return jsonify(result)
        except FileNotFoundError as exc:
            return jsonify({"error": str(exc)}), 404

    @bp.route("/data/rebind/preview", methods=["GET"])
    @admin_required
    def admin_data_rebind_preview():
        target_user_id = request.args.get("target_user_id", "").strip()
        if not target_user_id:
            return jsonify({"error": "Missing target_user_id"}), 400
        payload = db.preview_rebind_to_user(target_user_id)
        if payload.get("error"):
            return jsonify(payload), 404
        return jsonify(payload)

    @bp.route("/data/rebind/execute", methods=["POST"])
    @admin_write_audit(action="admin.data.rebind.execute", target_type="user")
    @admin_required
    def admin_data_rebind_execute():
        data = admin_common.json_body()
        target_user_id = str(data.get("target_user_id", "")).strip()
        if not target_user_id:
            return jsonify({"error": "Missing target_user_id"}), 400
        payload = db.execute_rebind_to_user(target_user_id)
        if payload.get("error"):
            return jsonify(payload), 400
        return jsonify({"status": "ok", "result": payload})
