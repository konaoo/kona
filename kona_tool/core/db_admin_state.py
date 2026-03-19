"""
认证令牌、邀请码、后台策略与运行时配置数据库能力。

这一层只做：
- refresh token
- 邀请码
- 后台审计日志
- 后台接口策略
- 运行时配置
- 巡检与行情测试报表
"""
import logging
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple


logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AdminStateDatabaseMixin:
    """给 DatabaseManager 提供后台状态与认证辅助相关方法。"""

    def _ensure_admin_api_policies_defaults(self, cursor) -> None:
        defaults = [
            ("upstream.price", "upstream", 1, None, "Price upstream switch"),
            ("upstream.rate", "upstream", 1, None, "Rate upstream switch"),
            ("upstream.news", "upstream", 1, None, "News upstream switch"),
            ("api.auth", "api_group", 1, 120, "Auth API group policy"),
            ("api.portfolio", "api_group", 1, 240, "Portfolio API group policy"),
            ("api.news", "api_group", 1, 120, "News API group policy"),
        ]
        for scope_key, scope_type, enabled, limit_per_min, note in defaults:
            cursor.execute(
                """
                INSERT INTO admin_api_policies
                (scope_key, scope_type, enabled, limit_per_min, note, updated_by)
                VALUES (?, ?, ?, ?, ?, 'system_init')
                ON CONFLICT(scope_key) DO UPDATE SET
                    scope_type = excluded.scope_type,
                    note = COALESCE(admin_api_policies.note, excluded.note)
                """,
                (scope_key, scope_type, enabled, limit_per_min, note),
            )

    def create_refresh_token(
        self,
        user_id: str,
        token_hash: str,
        expires_at: datetime,
        device_id: str = "",
    ) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        now_iso = _utc_now().isoformat()
        try:
            cursor.execute(
                """
                INSERT INTO auth_refresh_tokens (
                    user_id, token_hash, device_id, issued_at, expires_at, revoked_at, last_used_at
                ) VALUES (?, ?, ?, ?, ?, NULL, ?)
                """,
                (
                    user_id,
                    token_hash,
                    (device_id or "").strip()[:128],
                    now_iso,
                    expires_at.isoformat(),
                    now_iso,
                ),
            )
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_refresh_token(self, token_hash: str) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, user_id, token_hash, device_id, issued_at, expires_at, revoked_at, last_used_at
                FROM auth_refresh_tokens
                WHERE token_hash = ?
                LIMIT 1
                """,
                (token_hash,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def touch_refresh_token(self, token_hash: str) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE auth_refresh_tokens SET last_used_at = ? WHERE token_hash = ?",
                (_utc_now().isoformat(), token_hash),
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()

    def revoke_refresh_token(self, token_hash: str) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE auth_refresh_tokens SET revoked_at = ? WHERE token_hash = ? AND revoked_at IS NULL",
                (_utc_now().isoformat(), token_hash),
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()

    def revoke_all_refresh_tokens(self, user_id: str) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE auth_refresh_tokens
                SET revoked_at = ?
                WHERE user_id = ? AND revoked_at IS NULL
                """,
                (_utc_now().isoformat(), user_id),
            )
            conn.commit()
            return int(cursor.rowcount or 0)
        except Exception:
            conn.rollback()
            return 0
        finally:
            conn.close()

    def cleanup_expired_refresh_tokens(
        self,
        retention_days: int = 90,
        now: Optional[datetime] = None,
    ) -> int:
        keep_days = max(0, int(retention_days))
        now_utc = now or _utc_now()
        if now_utc.tzinfo is None:
            now_utc = now_utc.replace(tzinfo=timezone.utc)
        else:
            now_utc = now_utc.astimezone(timezone.utc)
        cutoff = (now_utc - timedelta(days=keep_days)).isoformat()
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                DELETE FROM auth_refresh_tokens
                WHERE expires_at < ?
                """,
                (cutoff,),
            )
            conn.commit()
            return int(cursor.rowcount or 0)
        except Exception:
            conn.rollback()
            return 0
        finally:
            conn.close()

    def get_admin_api_policy(self, scope_key: str) -> Optional[Dict[str, Any]]:
        key = str(scope_key or "").strip()
        if not key:
            return None
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, scope_key, scope_type, enabled, limit_per_min, note, updated_by, updated_at
                FROM admin_api_policies
                WHERE scope_key = ?
                LIMIT 1
                """,
                (key,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def list_admin_api_policies(self, scope_type: str = "all") -> List[Dict[str, Any]]:
        where = ""
        params: List[Any] = []
        scope_type_text = str(scope_type or "").strip().lower()
        if scope_type_text and scope_type_text != "all":
            where = "WHERE scope_type = ?"
            params.append(scope_type_text)
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"""
                SELECT id, scope_key, scope_type, enabled, limit_per_min, note, updated_by, updated_at
                FROM admin_api_policies
                {where}
                ORDER BY scope_type ASC, scope_key ASC
                """,
                tuple(params),
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def update_admin_api_policy(
        self,
        scope_key: str,
        enabled: Optional[bool] = None,
        limit_per_min: Optional[int] = None,
        note: Optional[str] = None,
        updated_by: str = "",
    ) -> Optional[Dict[str, Any]]:
        key = str(scope_key or "").strip()
        if not key:
            return None
        updates: List[str] = []
        params: List[Any] = []
        if enabled is not None:
            updates.append("enabled = ?")
            params.append(1 if bool(enabled) else 0)
        if limit_per_min is not None:
            updates.append("limit_per_min = ?")
            params.append(int(limit_per_min))
        if note is not None:
            updates.append("note = ?")
            params.append(str(note)[:500])
        updates.append("updated_by = ?")
        params.append(str(updated_by or "")[:64])
        updates.append("updated_at = datetime('now','localtime')")
        params.append(key)

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"""
                UPDATE admin_api_policies
                SET {', '.join(updates)}
                WHERE scope_key = ?
                """,
                tuple(params),
            )
            if cursor.rowcount <= 0:
                conn.rollback()
                return None
            conn.commit()
            cursor.execute(
                """
                SELECT id, scope_key, scope_type, enabled, limit_per_min, note, updated_by, updated_at
                FROM admin_api_policies
                WHERE scope_key = ?
                LIMIT 1
                """,
                (key,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception:
            conn.rollback()
            return None
        finally:
            conn.close()

    def add_admin_audit_log(
        self,
        admin_user_id: str,
        action: str,
        method: str,
        path: str,
        status_code: int,
        result: str,
        target_type: str = "",
        target_id: str = "",
        ip: str = "",
        request_body: str = "",
        error: str = "",
    ) -> bool:
        """记录后台审计日志。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO admin_audit_logs (
                    admin_user_id, action, target_type, target_id,
                    method, path, ip, request_body, status_code, result, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    admin_user_id,
                    action,
                    target_type,
                    target_id,
                    method,
                    path,
                    ip,
                    request_body,
                    status_code,
                    result,
                    error,
                ),
            )
            conn.commit()
            return True
        except Exception as exc:
            logger.error("Failed to add admin audit log: %s", exc)
            conn.rollback()
            return False
        finally:
            conn.close()

    def insert_invite_codes(
        self,
        codes: List[str],
        batch_id: str,
        created_by: str = "",
        note: str = "",
    ) -> int:
        if not codes:
            return 0
        conn = self.get_connection()
        cursor = conn.cursor()
        inserted = 0
        try:
            for code in codes:
                try:
                    cursor.execute(
                        """
                        INSERT INTO invite_codes (code, batch_id, status, created_by, note)
                        VALUES (?, ?, 'active', ?, ?)
                        """,
                        ((code or "").strip().upper(), batch_id, created_by, note),
                    )
                    inserted += 1
                except sqlite3.IntegrityError:
                    continue
            conn.commit()
            return inserted
        except Exception:
            conn.rollback()
            return 0
        finally:
            conn.close()

    def get_invite_code(self, code: str) -> Optional[Dict[str, Any]]:
        code_text = (code or "").strip().upper()
        if not code_text:
            return None
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT code, batch_id, status, created_by, created_at, used_by_user_id, used_at, note
                FROM invite_codes
                WHERE code = ?
                LIMIT 1
                """,
                (code_text,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def consume_invite_code(self, code: str, user_id: str) -> Tuple[bool, str]:
        code_text = (code or "").strip().upper()
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE invite_codes
                SET status = 'used', used_by_user_id = ?, used_at = datetime('now','localtime')
                WHERE code = ? AND status = 'active' AND used_by_user_id IS NULL
                """,
                (user_id, code_text),
            )
            if cursor.rowcount <= 0:
                conn.rollback()
                return False, "邀请码无效或已被使用"
            conn.commit()
            return True, ""
        except Exception:
            conn.rollback()
            return False, "邀请码无效或已被使用"
        finally:
            conn.close()

    def revoke_invite_code(self, code: str) -> bool:
        code_text = (code or "").strip().upper()
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE invite_codes SET status = 'revoked' WHERE code = ? AND status = 'active'",
                (code_text,),
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()

    def list_invite_codes(
        self,
        status: str = "all",
        batch_id: str = "",
        limit: int = 200,
        offset: int = 0,
        ordered_random: bool = False,
    ) -> Dict[str, Any]:
        where: List[str] = []
        params: List[Any] = []
        if status and status != "all":
            where.append("ic.status = ?")
            params.append(status)
        if batch_id:
            where.append("ic.batch_id = ?")
            params.append(batch_id)
        where_sql = f"WHERE {' AND '.join(where)}" if where else ""
        order_by = "ORDER BY RANDOM()" if ordered_random else "ORDER BY created_at DESC, code ASC"
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"""
                WITH filtered AS (
                    SELECT
                        ic.code,
                        ic.batch_id,
                        ic.status,
                        ic.created_by,
                        ic.created_at,
                        ic.used_by_user_id,
                        ic.used_at,
                        ic.note,
                        COALESCE(u.username, '') AS used_by_username,
                        u.user_number AS used_by_user_number
                    FROM invite_codes ic
                    LEFT JOIN users u ON u.id = ic.used_by_user_id
                    {where_sql}
                )
                SELECT
                    code,
                    batch_id,
                    status,
                    created_by,
                    created_at,
                    used_by_user_id,
                    used_at,
                    note,
                    used_by_username,
                    used_by_user_number,
                    COUNT(1) OVER() AS __total_count
                FROM filtered
                {order_by}
                LIMIT ? OFFSET ?
                """,
                tuple(params + [limit, offset]),
            )
            rows = cursor.fetchall()
            total = 0
            items: List[Dict[str, Any]] = []
            for row in rows:
                item = dict(row)
                if total <= 0:
                    total = int(item.get("__total_count") or 0)
                item.pop("__total_count", None)
                items.append(item)
            if not rows:
                cursor.execute(
                    f"SELECT COUNT(1) AS c FROM invite_codes ic {where_sql}",
                    tuple(params),
                )
                total_row = cursor.fetchone()
                total = int((total_row["c"] if total_row else 0) or 0)
            return {"items": items, "total": total, "limit": limit, "offset": offset}
        finally:
            conn.close()

    def get_runtime_config(self, key: str) -> Optional[str]:
        """读取运行时配置值。"""
        cfg_key = str(key or "").strip()
        if not cfg_key:
            return None
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT value
                FROM runtime_configs
                WHERE key = ?
                LIMIT 1
                """,
                (cfg_key,),
            )
            row = cursor.fetchone()
            return str(row["value"]) if row and row["value"] is not None else None
        finally:
            conn.close()

    def set_runtime_config(self, key: str, value: str, updated_by: str = "") -> None:
        """写入运行时配置值（持久化）。"""
        cfg_key = str(key or "").strip()
        if not cfg_key:
            raise ValueError("Missing runtime config key")
        cfg_value = str(value or "")
        updater = str(updated_by or "").strip()
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO runtime_configs (key, value, updated_by, updated_at)
                VALUES (?, ?, ?, datetime('now','localtime'))
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_by = excluded.updated_by,
                    updated_at = datetime('now','localtime')
                """,
                (cfg_key, cfg_value, updater),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def save_price_alert_report(
        self,
        report_date: str,
        tested_at_utc: str,
        total_assets: int,
        alert_count: int,
        summary: Dict[str, Any],
        items: List[Dict[str, Any]],
    ) -> None:
        report_date_text = str(report_date or "").strip()
        tested_at_text = str(tested_at_utc or "").strip()
        if not report_date_text or not tested_at_text:
            raise ValueError("Missing price alert report date or tested_at_utc")
        summary_json = json.dumps(summary or {}, ensure_ascii=False, separators=(",", ":"))
        items_json = json.dumps(items or [], ensure_ascii=False, separators=(",", ":"))
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO price_alert_reports (
                    report_date,
                    tested_at_utc,
                    total_assets,
                    alert_count,
                    summary_json,
                    items_json,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, datetime('now','localtime'))
                ON CONFLICT(report_date) DO UPDATE SET
                    tested_at_utc = excluded.tested_at_utc,
                    total_assets = excluded.total_assets,
                    alert_count = excluded.alert_count,
                    summary_json = excluded.summary_json,
                    items_json = excluded.items_json,
                    updated_at = datetime('now','localtime')
                """,
                (
                    report_date_text,
                    tested_at_text,
                    int(total_assets or 0),
                    int(alert_count or 0),
                    summary_json,
                    items_json,
                ),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def list_price_alert_reports(self, limit: int = 7) -> List[Dict[str, Any]]:
        try:
            safe_limit = max(1, min(int(limit or 7), 30))
        except Exception:
            safe_limit = 7
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT report_date, tested_at_utc, total_assets, alert_count, summary_json, updated_at
                FROM price_alert_reports
                ORDER BY report_date DESC
                LIMIT ?
                """,
                (safe_limit,),
            )
            rows = cursor.fetchall()
            items: List[Dict[str, Any]] = []
            for row in rows:
                summary_raw = str(row["summary_json"] or "{}").strip() or "{}"
                try:
                    summary = json.loads(summary_raw)
                except Exception:
                    summary = {}
                items.append(
                    {
                        "report_date": str(row["report_date"] or ""),
                        "tested_at_utc": str(row["tested_at_utc"] or ""),
                        "total_assets": int(row["total_assets"] or 0),
                        "alert_count": int(row["alert_count"] or 0),
                        "summary": summary if isinstance(summary, dict) else {},
                        "updated_at": str(row["updated_at"] or ""),
                    }
                )
            return items
        finally:
            conn.close()

    def get_latest_price_alert_report(self) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT report_date, tested_at_utc, total_assets, alert_count, summary_json, items_json, updated_at
                FROM price_alert_reports
                ORDER BY report_date DESC
                LIMIT 1
                """
            )
            row = cursor.fetchone()
            if not row:
                return None

            summary_raw = str(row["summary_json"] or "{}").strip() or "{}"
            items_raw = str(row["items_json"] or "[]").strip() or "[]"
            try:
                summary = json.loads(summary_raw)
            except Exception:
                summary = {}
            try:
                items = json.loads(items_raw)
            except Exception:
                items = []

            return {
                "report_date": str(row["report_date"] or ""),
                "tested_at_utc": str(row["tested_at_utc"] or ""),
                "total_assets": int(row["total_assets"] or 0),
                "alert_count": int(row["alert_count"] or 0),
                "summary": summary if isinstance(summary, dict) else {},
                "items": items if isinstance(items, list) else [],
                "updated_at": str(row["updated_at"] or ""),
            }
        finally:
            conn.close()

    def save_provider_test_report(
        self,
        report_slot: str,
        tested_at_utc: str,
        summary: Dict[str, Any],
        providers: Dict[str, Any],
    ) -> None:
        report_slot_text = str(report_slot or "").strip()
        tested_at_text = str(tested_at_utc or "").strip()
        if not report_slot_text or not tested_at_text:
            raise ValueError("Missing provider test report slot or tested_at_utc")
        summary_json = json.dumps(summary or {}, ensure_ascii=False, separators=(",", ":"))
        providers_json = json.dumps(providers or {}, ensure_ascii=False, separators=(",", ":"))
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO provider_test_reports (
                    report_slot,
                    tested_at_utc,
                    summary_json,
                    providers_json,
                    updated_at
                )
                VALUES (?, ?, ?, ?, datetime('now','localtime'))
                ON CONFLICT(report_slot) DO UPDATE SET
                    tested_at_utc = excluded.tested_at_utc,
                    summary_json = excluded.summary_json,
                    providers_json = excluded.providers_json,
                    updated_at = datetime('now','localtime')
                """,
                (report_slot_text, tested_at_text, summary_json, providers_json),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_latest_provider_test_report(self) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT report_slot, tested_at_utc, summary_json, providers_json, updated_at
                FROM provider_test_reports
                ORDER BY report_slot DESC
                LIMIT 1
                """
            )
            row = cursor.fetchone()
            if not row:
                return None

            summary_raw = str(row["summary_json"] or "{}").strip() or "{}"
            providers_raw = str(row["providers_json"] or "{}").strip() or "{}"
            try:
                summary = json.loads(summary_raw)
            except Exception:
                summary = {}
            try:
                providers = json.loads(providers_raw)
            except Exception:
                providers = {}

            return {
                "report_slot": str(row["report_slot"] or ""),
                "tested_at_utc": str(row["tested_at_utc"] or ""),
                "summary": summary if isinstance(summary, dict) else {},
                "providers": providers if isinstance(providers, dict) else {},
                "updated_at": str(row["updated_at"] or ""),
            }
        finally:
            conn.close()
