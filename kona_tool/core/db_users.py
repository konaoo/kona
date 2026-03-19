"""
用户、登录状态与重绑迁移数据库能力。

这一层只做：
- 用户查询与资料更新
- 登录 / 活跃打点
- 密码初始化与后台重置
- 用户表兼容迁移 / 日活回填
- 数据重绑预览与执行
"""
import logging
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class UserDatabaseMixin:
    """给 DatabaseManager 提供用户与登录状态相关方法。"""

    def _normalize_username_seed(self, seed: str) -> str:
        normalized = (seed or "").strip().lower()
        if "@" in normalized:
            normalized = normalized.split("@", 1)[0]
        normalized = re.sub(r"[^a-z0-9_]", "_", normalized)
        normalized = re.sub(r"_+", "_", normalized).strip("_")
        if not normalized:
            normalized = "user"
        if not normalized[0].isalpha():
            normalized = f"u_{normalized}"
        if len(normalized) < 4:
            normalized = (normalized + "user")[:4]
        return normalized[:24]

    def _next_unique_username(self, base: str, used: set) -> str:
        candidate = base
        idx = 1
        while candidate in used:
            suffix = f"_{idx}"
            candidate = f"{base[:24-len(suffix)]}{suffix}"
            idx += 1
        used.add(candidate)
        return candidate

    def _ensure_users_schema(self, cursor) -> None:
        cursor.execute("PRAGMA table_info(users)")
        cols = [row[1] for row in cursor.fetchall()]
        if not cols:
            return

        rebuild_required_cols = {
            "id",
            "username",
            "password_hash",
            "legacy_needs_password_setup",
            "nickname",
            "avatar",
            "register_method",
            "phone",
            "user_number",
            "is_admin",
            "status",
            "created_at",
            "build_start_at",
            "last_login",
            "last_login_ip",
            "last_login_region",
            "last_active_ip",
            "last_active_region",
            "last_active_at",
        }
        needs_rebuild = ("email" in cols) or any(c not in cols for c in rebuild_required_cols)
        if needs_rebuild:
            cursor.execute("SELECT * FROM users")
            rows = [dict(r) for r in cursor.fetchall()]
            cursor.execute("DROP TABLE IF EXISTS users_new")
            cursor.execute(
                """
                CREATE TABLE users_new (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT,
                    legacy_needs_password_setup INTEGER NOT NULL DEFAULT 0,
                    must_change_password INTEGER NOT NULL DEFAULT 0,
                    password_updated_at TIMESTAMP,
                    password_reset_at TIMESTAMP,
                    password_reset_by TEXT,
                    nickname TEXT,
                    avatar TEXT,
                    register_method TEXT,
                    phone TEXT,
                    user_number INTEGER,
                    is_admin INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT datetime('now','localtime'),
                    build_start_at TIMESTAMP,
                    last_login TIMESTAMP,
                    last_login_ip TEXT,
                    last_login_region TEXT,
                    last_active_ip TEXT,
                    last_active_region TEXT,
                    last_active_at TIMESTAMP
                )
                """
            )
            used = set()
            for idx, row in enumerate(rows, start=1):
                user_id = str(row.get("id") or uuid.uuid4().hex)
                seed = row.get("username") or row.get("email") or user_id
                base = self._normalize_username_seed(str(seed))
                username = self._next_unique_username(base, used)
                password_hash = row.get("password_hash")
                legacy_flag = 1 if not password_hash else int(
                    row.get("legacy_needs_password_setup") or 0
                )
                cursor.execute(
                    """
                    INSERT INTO users_new (
                        id, username, password_hash, legacy_needs_password_setup,
                        must_change_password, password_updated_at, password_reset_at, password_reset_by,
                        nickname, avatar, register_method, phone,
                        user_number, is_admin, status, created_at, build_start_at, last_login, last_login_ip,
                        last_login_region, last_active_ip, last_active_region, last_active_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        username,
                        password_hash,
                        legacy_flag,
                        int(row.get("must_change_password") or 0),
                        row.get("password_updated_at"),
                        row.get("password_reset_at"),
                        row.get("password_reset_by"),
                        row.get("nickname"),
                        row.get("avatar"),
                        row.get("register_method") or "legacy_email_otp",
                        row.get("phone"),
                        row.get("user_number") or (9999 + idx),
                        int(row.get("is_admin") or 0),
                        row.get("status") or "active",
                        row.get("created_at"),
                        row.get("build_start_at"),
                        row.get("last_login"),
                        row.get("last_login_ip"),
                        row.get("last_login_region"),
                        row.get("last_active_ip"),
                        row.get("last_active_region"),
                        row.get("last_active_at"),
                    ),
                )
            cursor.execute("DROP TABLE users")
            cursor.execute("ALTER TABLE users_new RENAME TO users")
        else:
            def _ensure_column(column: str, col_def: str) -> None:
                cursor.execute("PRAGMA table_info(users)")
                current_cols = [row[1] for row in cursor.fetchall()]
                if column not in current_cols:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {col_def}")

            _ensure_column("password_hash", "password_hash TEXT")
            _ensure_column(
                "legacy_needs_password_setup",
                "legacy_needs_password_setup INTEGER NOT NULL DEFAULT 0",
            )
            _ensure_column(
                "must_change_password",
                "must_change_password INTEGER NOT NULL DEFAULT 0",
            )
            _ensure_column("password_updated_at", "password_updated_at TIMESTAMP")
            _ensure_column("password_reset_at", "password_reset_at TIMESTAMP")
            _ensure_column("password_reset_by", "password_reset_by TEXT")
            _ensure_column("nickname", "nickname TEXT")
            _ensure_column("avatar", "avatar TEXT")
            _ensure_column("register_method", "register_method TEXT")
            _ensure_column("phone", "phone TEXT")
            _ensure_column("user_number", "user_number INTEGER")
            _ensure_column("is_admin", "is_admin INTEGER NOT NULL DEFAULT 0")
            _ensure_column("status", "status TEXT NOT NULL DEFAULT 'active'")
            _ensure_column("created_at", "created_at TIMESTAMP DEFAULT datetime('now','localtime')")
            _ensure_column("build_start_at", "build_start_at TIMESTAMP")
            _ensure_column("last_login", "last_login TIMESTAMP")
            _ensure_column("last_login_ip", "last_login_ip TEXT")
            _ensure_column("last_login_region", "last_login_region TEXT")
            _ensure_column("last_active_ip", "last_active_ip TEXT")
            _ensure_column("last_active_region", "last_active_region TEXT")
            _ensure_column("last_active_at", "last_active_at TIMESTAMP")

        cursor.execute("UPDATE users SET is_admin = 0 WHERE is_admin IS NULL")
        cursor.execute("UPDATE users SET status = 'active' WHERE status IS NULL OR status = ''")
        cursor.execute("UPDATE users SET must_change_password = 0 WHERE must_change_password IS NULL")
        cursor.execute(
            "UPDATE users SET legacy_needs_password_setup = 1 "
            "WHERE COALESCE(password_hash, '') = ''"
        )
        cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username_unique ON users(username)"
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_last_active_at ON users(last_active_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_status ON users(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_user_number ON users(user_number)")

    def _backfill_user_daily_activity(self, cursor) -> None:
        """
        用库里已经明确存在的日期回填日活。
        这里只回填能确定的日期，不伪造中间历史。
        """
        cursor.execute(
            """
            INSERT OR IGNORE INTO user_daily_activity (user_id, activity_date)
            SELECT id, SUBSTR(created_at, 1, 10)
            FROM users
            WHERE id IS NOT NULL
              AND TRIM(COALESCE(id, '')) != ''
              AND created_at IS NOT NULL
              AND TRIM(COALESCE(created_at, '')) != ''
            """
        )
        cursor.execute(
            """
            INSERT OR IGNORE INTO user_daily_activity (user_id, activity_date)
            SELECT id, SUBSTR(last_login, 1, 10)
            FROM users
            WHERE id IS NOT NULL
              AND TRIM(COALESCE(id, '')) != ''
              AND last_login IS NOT NULL
              AND TRIM(COALESCE(last_login, '')) != ''
            """
        )
        cursor.execute(
            """
            INSERT OR IGNORE INTO user_daily_activity (user_id, activity_date)
            SELECT id, SUBSTR(last_active_at, 1, 10)
            FROM users
            WHERE id IS NOT NULL
              AND TRIM(COALESCE(id, '')) != ''
              AND last_active_at IS NOT NULL
              AND TRIM(COALESCE(last_active_at, '')) != ''
            """
        )

    def get_user_auth_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户的后台权限信息。"""
        if not user_id:
            return None
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                '''
                SELECT id, username, is_admin, status, must_change_password
                FROM users
                WHERE id = ?
                LIMIT 1
                ''',
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                'id': row['id'],
                'username': row['username'],
                'is_admin': bool(row['is_admin']),
                'status': row['status'] or 'active',
                'must_change_password': bool(row['must_change_password']),
            }
        finally:
            conn.close()

    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        if not user_id:
            return None
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                '''
                SELECT id, username, nickname, avatar, register_method, phone,
                       user_number, is_admin, created_at, build_start_at, last_login, legacy_needs_password_setup,
                       must_change_password
                FROM users
                WHERE id = ?
                LIMIT 1
                ''',
                (user_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        username_text = (username or "").strip().lower()
        if not username_text:
            return None
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                '''
                SELECT id, username, password_hash, legacy_needs_password_setup,
                       must_change_password, password_reset_at, password_reset_by,
                       nickname, avatar, register_method, phone, user_number,
                       is_admin, status, created_at, build_start_at, last_login
                FROM users
                WHERE username = ?
                LIMIT 1
                ''',
                (username_text,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        if not user_id:
            return None
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, username, password_hash, legacy_needs_password_setup,
                       must_change_password, password_reset_at, password_reset_by,
                       nickname, avatar, register_method, phone, user_number,
                       is_admin, status, created_at, build_start_at, last_login
                FROM users
                WHERE id = ?
                LIMIT 1
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def create_user(
        self,
        username: str,
        password_hash: str,
        register_method: str = "password_invite",
        is_admin: bool = False,
        user_id: str = "",
    ) -> Dict[str, Any]:
        username_text = (username or "").strip().lower()
        resolved_user_id = user_id or uuid.uuid4().hex
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT MAX(user_number) AS max_num FROM users")
            row = cursor.fetchone()
            max_num = int(row["max_num"] or 9999) if row else 9999
            user_number = max_num + 1
            cursor.execute(
                """
                INSERT INTO users (
                    id, username, password_hash, legacy_needs_password_setup,
                    password_updated_at, register_method, user_number, is_admin
                ) VALUES (?, ?, ?, 0, datetime('now','localtime'), ?, ?, ?)
                """,
                (
                    resolved_user_id,
                    username_text,
                    password_hash,
                    register_method,
                    user_number,
                    1 if is_admin else 0,
                ),
            )
            conn.commit()
            return {
                "id": resolved_user_id,
                "username": username_text,
                "user_number": user_number,
                "is_admin": bool(is_admin),
            }
        except Exception as exc:
            logger.error("Failed to create user: %s", exc)
            conn.rollback()
            raise
        finally:
            conn.close()

    def set_user_build_start_at(self, user_id: str, build_start_at: Optional[str]) -> bool:
        if not user_id:
            return False
        normalized = str(build_start_at or "").strip() or None
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE users SET build_start_at = ? WHERE id = ?",
                (normalized, user_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def update_last_login(
        self,
        user_id: str,
        login_ip: Optional[str] = None,
        login_region: Optional[str] = None,
    ) -> None:
        if not user_id:
            return
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            updates = ["last_login = datetime('now','localtime')", "last_active_at = datetime('now','localtime')"]
            params: List[Any] = []
            if login_ip is not None:
                updates.append("last_login_ip = ?")
                params.append(str(login_ip).strip()[:64])
            if login_region is not None:
                updates.append("last_login_region = ?")
                params.append(str(login_region).strip()[:120])
            if login_ip is not None:
                updates.append("last_active_ip = ?")
                params.append(str(login_ip).strip()[:64])
            if login_region is not None:
                updates.append("last_active_region = ?")
                params.append(str(login_region).strip()[:120])
            params.append(user_id)
            cursor.execute(
                f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
                tuple(params),
            )
            self._record_user_daily_activity_with_cursor(cursor, user_id)
            conn.commit()
        finally:
            conn.close()

    def update_last_active(
        self,
        user_id: str,
        active_ip: Optional[str] = None,
        active_region: Optional[str] = None,
    ) -> None:
        if not user_id:
            return
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            updates = ["last_active_at = datetime('now','localtime')"]
            params: List[Any] = []
            if active_ip is not None:
                updates.append("last_active_ip = ?")
                params.append(str(active_ip).strip()[:64])
            if active_region is not None:
                updates.append("last_active_region = ?")
                params.append(str(active_region).strip()[:120])
            params.append(user_id)
            cursor.execute(
                f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
                tuple(params),
            )
            self._record_user_daily_activity_with_cursor(cursor, user_id)
            conn.commit()
        finally:
            conn.close()

    def _record_user_daily_activity_with_cursor(
        self,
        cursor,
        user_id: str,
        activity_at: Optional[datetime] = None,
    ) -> None:
        uid = str(user_id or "").strip()
        if not uid:
            return
        target = activity_at or datetime.now()
        activity_date = target.strftime("%Y-%m-%d")
        activity_ts = target.strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            """
            INSERT INTO user_daily_activity (user_id, activity_date, first_seen_at, last_seen_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, activity_date) DO UPDATE SET
                last_seen_at = excluded.last_seen_at
            """,
            (uid, activity_date, activity_ts, activity_ts),
        )

    def record_user_daily_activity(
        self,
        user_id: str,
        activity_at: Optional[datetime] = None,
    ) -> None:
        uid = str(user_id or "").strip()
        if not uid:
            return
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            self._record_user_daily_activity_with_cursor(cursor, uid, activity_at=activity_at)
            conn.commit()
        finally:
            conn.close()

    def delete_user(self, user_id: str) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()

    def update_user_profile(self, user_id: str, nickname: Any = None, avatar: Any = None) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        updates: List[str] = []
        params: List[Any] = []
        if nickname is not None:
            updates.append("nickname = ?")
            params.append(str(nickname).strip())
        if avatar is not None:
            updates.append("avatar = ?")
            params.append(avatar)
        if not updates:
            return False
        params.append(user_id)
        try:
            cursor.execute(
                f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
                tuple(params),
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()

    def set_user_password(self, user_id: str, password_hash: str) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE users
                SET password_hash = ?,
                    legacy_needs_password_setup = 0,
                    must_change_password = 0,
                    password_reset_at = NULL,
                    password_reset_by = NULL,
                    password_updated_at = datetime('now','localtime')
                WHERE id = ?
                """,
                (password_hash, user_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()

    def set_user_must_change_password(
        self,
        user_id: str,
        must_change_password: bool,
        reset_by: str = "",
    ) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if must_change_password:
                cursor.execute(
                    """
                    UPDATE users
                    SET must_change_password = 1,
                        password_reset_at = datetime('now','localtime'),
                        password_reset_by = ?
                    WHERE id = ?
                    """,
                    (reset_by, user_id),
                )
            else:
                cursor.execute(
                    """
                    UPDATE users
                    SET must_change_password = 0,
                        password_reset_at = NULL,
                        password_reset_by = NULL
                    WHERE id = ?
                    """,
                    (user_id,),
                )
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()

    def admin_reset_user_password(
        self,
        user_id: str,
        password_hash: str,
        admin_user_id: str,
        force_change: bool = True,
    ) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE users
                SET password_hash = ?,
                    legacy_needs_password_setup = 0,
                    must_change_password = ?,
                    password_reset_at = datetime('now','localtime'),
                    password_reset_by = ?,
                    password_updated_at = datetime('now','localtime')
                WHERE id = ?
                """,
                (
                    password_hash,
                    1 if force_change else 0,
                    admin_user_id,
                    user_id,
                ),
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()

    def bootstrap_credentials(self, user_id: str, username: str, password_hash: str) -> Tuple[bool, str]:
        conn = self.get_connection()
        cursor = conn.cursor()
        username_text = (username or "").strip().lower()
        try:
            cursor.execute("SELECT id FROM users WHERE username = ? AND id != ?", (username_text, user_id))
            if cursor.fetchone():
                return False, "用户名已存在"
            cursor.execute(
                """
                UPDATE users
                SET username = ?, password_hash = ?, legacy_needs_password_setup = 0, password_updated_at = datetime('now','localtime')
                WHERE id = ? AND (legacy_needs_password_setup = 1 OR COALESCE(password_hash, '') = '')
                """,
                (username_text, password_hash, user_id),
            )
            if cursor.rowcount <= 0:
                conn.rollback()
                return False, "初始化已完成"
            conn.commit()
            return True, ""
        except Exception:
            conn.rollback()
            return False, "初始化失败"
        finally:
            conn.close()

    def _table_rebind_count(self, cursor, table: str, target_user_id: str) -> int:
        cursor.execute(
            f"SELECT COUNT(1) AS c FROM {table} WHERE COALESCE(user_id, '') != ?",
            (target_user_id,),
        )
        row = cursor.fetchone()
        return int(row["c"] or 0)

    def preview_rebind_to_user(self, target_user_id: str) -> Dict[str, Any]:
        conn = self.get_connection()
        cursor = conn.cursor()
        tables = [
            "portfolio",
            "transactions",
            "cash_assets",
            "other_assets",
            "liabilities",
            "daily_snapshots",
        ]
        try:
            cursor.execute("SELECT id, username FROM users WHERE id = ? LIMIT 1", (target_user_id,))
            user_row = cursor.fetchone()
            if not user_row:
                return {"error": "Target user not found"}
            per_table = {
                table: self._table_rebind_count(cursor, table, target_user_id)
                for table in tables
            }
            source_distribution: Dict[str, Dict[str, int]] = {}
            for table in tables:
                cursor.execute(
                    f"""
                    SELECT COALESCE(NULLIF(TRIM(user_id), ''), '__local__') AS source_user_id, COUNT(1) AS c
                    FROM {table}
                    WHERE COALESCE(user_id, '') != ?
                    GROUP BY COALESCE(NULLIF(TRIM(user_id), ''), '__local__')
                    ORDER BY c DESC
                    """,
                    (target_user_id,),
                )
                source_distribution[table] = {
                    row["source_user_id"]: int(row["c"] or 0)
                    for row in cursor.fetchall()
                }
            return {
                "target_user_id": target_user_id,
                "target_username": user_row["username"],
                "tables": per_table,
                "sources": source_distribution,
                "total": int(sum(per_table.values())),
            }
        finally:
            conn.close()

    def execute_rebind_to_user(self, target_user_id: str) -> Dict[str, Any]:
        conn = self.get_connection()
        cursor = conn.cursor()
        result = {
            "target_user_id": target_user_id,
            "tables": {},
            "total": 0,
        }
        try:
            cursor.execute("BEGIN")
            cursor.execute("SELECT id FROM users WHERE id = ? LIMIT 1", (target_user_id,))
            if not cursor.fetchone():
                conn.rollback()
                return {"error": "Target user not found"}

            simple_tables = ["portfolio", "transactions", "cash_assets", "other_assets", "liabilities"]
            for table in simple_tables:
                cursor.execute(
                    f"UPDATE {table} SET user_id = ? WHERE COALESCE(user_id, '') != ?",
                    (target_user_id, target_user_id),
                )
                moved = int(cursor.rowcount or 0)
                result["tables"][table] = moved
                result["total"] += moved

            cursor.execute(
                """
                SELECT date, total_asset, total_invest, total_cash, total_other,
                       total_liability, total_pnl, day_pnl, updated_at
                FROM daily_snapshots
                WHERE COALESCE(user_id, '') != ?
                ORDER BY COALESCE(updated_at, ''), id
                """,
                (target_user_id,),
            )
            rows = cursor.fetchall()
            moved_snapshots = 0
            for row in rows:
                cursor.execute(
                    """
                    INSERT INTO daily_snapshots (
                        date, total_asset, total_invest, total_cash, total_other,
                        total_liability, total_pnl, day_pnl, user_id, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(date, user_id) DO UPDATE SET
                        total_asset = CASE WHEN excluded.updated_at >= COALESCE(daily_snapshots.updated_at, '') THEN excluded.total_asset ELSE daily_snapshots.total_asset END,
                        total_invest = CASE WHEN excluded.updated_at >= COALESCE(daily_snapshots.updated_at, '') THEN excluded.total_invest ELSE daily_snapshots.total_invest END,
                        total_cash = CASE WHEN excluded.updated_at >= COALESCE(daily_snapshots.updated_at, '') THEN excluded.total_cash ELSE daily_snapshots.total_cash END,
                        total_other = CASE WHEN excluded.updated_at >= COALESCE(daily_snapshots.updated_at, '') THEN excluded.total_other ELSE daily_snapshots.total_other END,
                        total_liability = CASE WHEN excluded.updated_at >= COALESCE(daily_snapshots.updated_at, '') THEN excluded.total_liability ELSE daily_snapshots.total_liability END,
                        total_pnl = CASE WHEN excluded.updated_at >= COALESCE(daily_snapshots.updated_at, '') THEN excluded.total_pnl ELSE daily_snapshots.total_pnl END,
                        day_pnl = CASE WHEN excluded.updated_at >= COALESCE(daily_snapshots.updated_at, '') THEN excluded.day_pnl ELSE daily_snapshots.day_pnl END,
                        updated_at = CASE WHEN excluded.updated_at >= COALESCE(daily_snapshots.updated_at, '') THEN excluded.updated_at ELSE daily_snapshots.updated_at END
                    """,
                    (
                        row["date"],
                        row["total_asset"],
                        row["total_invest"],
                        row["total_cash"],
                        row["total_other"],
                        row["total_liability"],
                        row["total_pnl"],
                        row["day_pnl"],
                        target_user_id,
                        row["updated_at"],
                    ),
                )
                moved_snapshots += 1
            cursor.execute(
                "DELETE FROM daily_snapshots WHERE COALESCE(user_id, '') != ?",
                (target_user_id,),
            )
            result["tables"]["daily_snapshots"] = moved_snapshots
            result["total"] += moved_snapshots

            conn.commit()
            return result
        except Exception as exc:
            logger.error("Failed to execute user rebind: %s", exc)
            conn.rollback()
            return {"error": "Failed to execute rebind"}
        finally:
            conn.close()

    def get_user_ids(self) -> List[str]:
        """获取所有用户ID（用于批量快照）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT id FROM users')
            return [row['id'] for row in cursor.fetchall() if row['id']]
        except Exception as exc:
            logger.error(f"Failed to get user ids: {exc}")
            return []
        finally:
            conn.close()
