"""
数据库管理模块
使用SQLite替代CSV文件，提供高效的数据存储和查询
"""
import sqlite3
import logging
import uuid
import re
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import datetime as dt
from pathlib import Path
import config  # 添加导入
try:
    from .market_calendar import all_markets_closed, is_markets_closed_on_date, market_from_asset
    from .parser import parse_code
except ImportError:  # 兼容被单文件动态加载的测试场景
    from core.market_calendar import all_markets_closed, is_markets_closed_on_date, market_from_asset
    from core.parser import parse_code

logger = logging.getLogger(__name__)
DEFAULT_MARKETS = ("a", "hk", "us", "fund")
MARKET_BREAKDOWN_MARKETS = ("a", "hk", "us", "fund", "unallocated")


def _is_weekend_date(date_str: str) -> bool:
    try:
        return dt.datetime.strptime(date_str, "%Y-%m-%d").weekday() >= 5
    except Exception:
        return False


def _is_market_closed_date(date_str: str, markets: Tuple[str, ...] = DEFAULT_MARKETS) -> bool:
    try:
        return is_markets_closed_on_date(markets, date_str)
    except Exception:
        return _is_weekend_date(date_str)


def _is_market_closed_at_snapshot_time(
    updated_at: Any, markets: Tuple[str, ...] = DEFAULT_MARKETS
) -> bool:
    """
    判断快照写入时刻是否处于全市场休市。
    用于避免在“非交易时段快照”里用 total_pnl 反推 day_pnl。
    """
    if not updated_at:
        return False
    try:
        raw = str(updated_at).strip()
        if not raw:
            return False
        snapshot_time = dt.datetime.strptime(raw[:19], "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=dt.timezone.utc
        )
        return all_markets_closed(markets, now=snapshot_time)
    except Exception:
        return False


def _is_snapshot_updated_on_same_date(date_str: Any, updated_at: Any) -> bool:
    """
    仅当 updated_at 与快照日期同日时，才认为它可用于“快照写入时刻”判断。
    避免后续运维操作改写 updated_at 导致历史交易日被误判为休市时写入。
    """
    if not date_str or not updated_at:
        return False
    try:
        d = str(date_str).strip()[:10]
        ts = str(updated_at).strip()[:10]
        if not d or not ts:
            return False
        return d == ts
    except Exception:
        return False


class DatabaseManager:
    """数据库管理类"""
    
    VALID_FIELDS = {'code', 'name', 'qty', 'price', 'curr', 'adjustment', 'asset_type'}
    
    def __init__(self, db_path: str):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        db_parent = Path(self.db_path).expanduser().resolve().parent
        db_parent.mkdir(parents=True, exist_ok=True)
        timeout = float(getattr(config, "SQLITE_TIMEOUT_SECONDS", 1.5))
        busy_timeout = int(getattr(config, "SQLITE_BUSY_TIMEOUT_MS", 1500))
        journal_mode = str(getattr(config, "SQLITE_JOURNAL_MODE", "WAL")).upper()
        synchronous = str(getattr(config, "SQLITE_SYNCHRONOUS", "NORMAL")).upper()
        conn = sqlite3.connect(
            self.db_path,
            timeout=timeout,
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        conn.execute(f"PRAGMA busy_timeout={busy_timeout}")
        conn.execute(f"PRAGMA journal_mode={journal_mode}")
        conn.execute(f"PRAGMA synchronous={synchronous}")
        return conn
    
    def __enter__(self):
        self._conn = self.get_connection()
        return self._conn
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn:
            self._conn.close()
    
    def init_database(self):
        """初始化数据库表结构"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 创建持仓表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                qty REAL NOT NULL,
                price REAL NOT NULL,
                curr TEXT NOT NULL DEFAULT 'CNY',
                adjustment REAL DEFAULT 0.0,
                asset_type TEXT DEFAULT 'a',
                user_id TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建交易记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time TEXT NOT NULL,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                price REAL NOT NULL,
                qty REAL NOT NULL,
                amount REAL NOT NULL,
                pnl REAL DEFAULT 0.0,
                user_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建现金资产表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cash_assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                amount REAL NOT NULL,
                curr TEXT NOT NULL DEFAULT 'CNY',
                user_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建其他资产表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS other_assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                amount REAL NOT NULL,
                curr TEXT NOT NULL DEFAULT 'CNY',
                user_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建负债表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS liabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                amount REAL NOT NULL,
                curr TEXT NOT NULL DEFAULT 'CNY',
                user_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建用户表（v2: username + password）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')

        # 创建后台审计日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                target_type TEXT,
                target_id TEXT,
                method TEXT NOT NULL,
                path TEXT NOT NULL,
                ip TEXT,
                request_body TEXT,
                status_code INTEGER NOT NULL,
                result TEXT NOT NULL,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 邀请码表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invite_codes (
                code TEXT PRIMARY KEY,
                batch_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                used_by_user_id TEXT,
                used_at TIMESTAMP,
                note TEXT
            )
        ''')

        # Refresh token 表（仅存 hash）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auth_refresh_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                token_hash TEXT UNIQUE NOT NULL,
                device_id TEXT,
                issued_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                revoked_at TIMESTAMP,
                last_used_at TIMESTAMP
            )
        ''')

        # 接口策略表（后台动态开关/限流）
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_api_policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scope_key TEXT UNIQUE NOT NULL,
                scope_type TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                limit_per_min INTEGER,
                note TEXT,
                updated_by TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        
        # 创建每日快照表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                total_asset REAL NOT NULL,
                total_invest REAL NOT NULL,
                total_cash REAL NOT NULL,
                total_other REAL NOT NULL,
                total_liability REAL NOT NULL,
                total_pnl REAL NOT NULL,
                day_pnl REAL NOT NULL,
                user_id TEXT NOT NULL DEFAULT '',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, user_id)
            )
        ''')

        # 每日分市场收益快照表（A/HK/US/Fund + unallocated）
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS daily_snapshot_market_breakdowns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                user_id TEXT NOT NULL DEFAULT '',
                market TEXT NOT NULL,
                day_pnl REAL NOT NULL,
                source TEXT NOT NULL DEFAULT 'exact',
                confidence REAL NOT NULL DEFAULT 1.0,
                meta_json TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, user_id, market)
            )
            '''
        )

        # Ensure user_id columns exist for older DBs
        def _ensure_column(table: str, column: str, col_def: str) -> None:
            cursor.execute(f'PRAGMA table_info({table})')
            cols = [row[1] for row in cursor.fetchall()]
            if column not in cols:
                cursor.execute(f'ALTER TABLE {table} ADD COLUMN {col_def}')

        _ensure_column('portfolio', 'user_id', "user_id TEXT NOT NULL DEFAULT ''")
        _ensure_column('transactions', 'user_id', 'user_id TEXT')
        _ensure_column('cash_assets', 'user_id', 'user_id TEXT')
        _ensure_column('other_assets', 'user_id', 'user_id TEXT')
        _ensure_column('liabilities', 'user_id', 'user_id TEXT')
        _ensure_column('cash_assets', 'curr', "curr TEXT NOT NULL DEFAULT 'CNY'")
        _ensure_column('other_assets', 'curr', "curr TEXT NOT NULL DEFAULT 'CNY'")
        _ensure_column('liabilities', 'curr', "curr TEXT NOT NULL DEFAULT 'CNY'")
        _ensure_column('cash_assets', 'created_at', 'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        _ensure_column('cash_assets', 'updated_at', 'updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        _ensure_column('other_assets', 'created_at', 'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        _ensure_column('other_assets', 'updated_at', 'updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        _ensure_column('liabilities', 'created_at', 'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        _ensure_column('liabilities', 'updated_at', 'updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        _ensure_column('daily_snapshots', 'user_id', "user_id TEXT DEFAULT ''")
        _ensure_column('daily_snapshot_market_breakdowns', 'user_id', "user_id TEXT DEFAULT ''")
        _ensure_column('daily_snapshot_market_breakdowns', 'source', "source TEXT NOT NULL DEFAULT 'exact'")
        _ensure_column('daily_snapshot_market_breakdowns', 'confidence', "confidence REAL NOT NULL DEFAULT 1.0")
        _ensure_column('daily_snapshot_market_breakdowns', 'meta_json', "meta_json TEXT")
        _ensure_column('daily_snapshot_market_breakdowns', 'updated_at', "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        self._ensure_portfolio_user_scoped_unique(cursor)
        self._ensure_users_schema(cursor)

        # 创建索引以优化查询性能
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_portfolio_user_id ON portfolio(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_portfolio_code ON portfolio(code)')
        cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_portfolio_code_user_unique ON portfolio(code, user_id)"
        )
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_code ON transactions(code)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_cash_assets_user_id ON cash_assets(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_other_assets_user_id ON other_assets(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_liabilities_user_id ON liabilities(user_id)')
        # 修复旧表结构（date 全局唯一）并统一快照唯一键：(date, user_id)
        self._ensure_daily_snapshots_schema(cursor)

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_snapshots_date ON daily_snapshots(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_snapshots_user_id ON daily_snapshots(user_id)')
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_snapshots_date_user_unique ON daily_snapshots(date, user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_market_breakdowns_user_date ON daily_snapshot_market_breakdowns(user_id, date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_market_breakdowns_date ON daily_snapshot_market_breakdowns(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_market_breakdowns_source ON daily_snapshot_market_breakdowns(source)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_admin_user_id ON admin_audit_logs(admin_user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_created_at ON admin_audit_logs(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_action ON admin_audit_logs(action)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_invite_codes_status ON invite_codes(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_invite_codes_batch_id ON invite_codes(batch_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_auth_refresh_tokens_user_id ON auth_refresh_tokens(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_auth_refresh_tokens_expires_at ON auth_refresh_tokens(expires_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_admin_api_policies_scope_type ON admin_api_policies(scope_type)')
        cursor.execute('DROP TABLE IF EXISTS email_verification_codes')

        # 确保 asset_type 列存在并回填
        self._ensure_portfolio_asset_type(cursor)
        self._ensure_admin_api_policies_defaults(cursor)

        conn.commit()
        conn.close()

    def _ensure_portfolio_user_scoped_unique(self, cursor) -> None:
        """将 portfolio 的全局 code 唯一约束迁移为 (code, user_id) 唯一约束。"""
        cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='portfolio'"
        )
        row = cursor.fetchone()
        if isinstance(row, sqlite3.Row):
            raw_sql = row["sql"]
        else:
            raw_sql = row[0] if row else ""
        table_sql = str(raw_sql or "").lower()
        has_legacy_unique = "code text unique" in table_sql or "code\ttext unique" in table_sql

        if has_legacy_unique:
            logger.info("Migrating portfolio schema from global code unique to (code, user_id) unique")
            cursor.execute("DROP TABLE IF EXISTS portfolio_new")
            cursor.execute(
                """
                CREATE TABLE portfolio_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL,
                    name TEXT NOT NULL,
                    qty REAL NOT NULL,
                    price REAL NOT NULL,
                    curr TEXT NOT NULL DEFAULT 'CNY',
                    adjustment REAL DEFAULT 0.0,
                    asset_type TEXT DEFAULT 'a',
                    user_id TEXT NOT NULL DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                INSERT INTO portfolio_new (
                    id, code, name, qty, price, curr, adjustment, asset_type, user_id, created_at, updated_at
                )
                SELECT
                    id,
                    code,
                    name,
                    qty,
                    price,
                    COALESCE(curr, 'CNY'),
                    COALESCE(adjustment, 0.0),
                    COALESCE(NULLIF(asset_type, ''), 'a'),
                    COALESCE(user_id, ''),
                    COALESCE(created_at, CURRENT_TIMESTAMP),
                    COALESCE(updated_at, CURRENT_TIMESTAMP)
                FROM portfolio
                """
            )
            cursor.execute("DROP TABLE portfolio")
            cursor.execute("ALTER TABLE portfolio_new RENAME TO portfolio")

        # 统一 user_id 的空值，避免 NULL 绕过联合唯一键
        cursor.execute("UPDATE portfolio SET user_id = '' WHERE user_id IS NULL")

        # 清理可能存在的 code 单列唯一索引，避免继续阻塞跨用户同代码
        cursor.execute("PRAGMA index_list(portfolio)")
        for index_row in cursor.fetchall():
            index_name = index_row[1]
            is_unique = int(index_row[2] or 0) == 1
            if not is_unique:
                continue
            safe_name = str(index_name).replace('"', '""')
            cursor.execute(f'PRAGMA index_info("{safe_name}")')
            cols = [str(col_row[2]) for col_row in cursor.fetchall()]
            if cols == ["code"]:
                cursor.execute(f'DROP INDEX IF EXISTS "{safe_name}"')

        removed = self._deduplicate_portfolio_by_code_user(cursor)
        if removed > 0:
            logger.warning(
                "Removed %s duplicate portfolio rows before creating (code, user_id) unique index",
                removed,
            )

    def _deduplicate_portfolio_by_code_user(self, cursor) -> int:
        """按 (code, user_id) 去重，保留最近更新的一条记录。"""
        removed = 0
        cursor.execute(
            """
            SELECT code, COALESCE(user_id, '') AS uid, COUNT(1) AS c
            FROM portfolio
            GROUP BY code, COALESCE(user_id, '')
            HAVING COUNT(1) > 1
            """
        )
        duplicates = cursor.fetchall()
        for row in duplicates:
            code = row[0]
            user_id = row[1]
            cursor.execute(
                """
                SELECT id
                FROM portfolio
                WHERE code = ? AND COALESCE(user_id, '') = ?
                ORDER BY datetime(COALESCE(updated_at, created_at, '1970-01-01 00:00:00')) DESC, id DESC
                """,
                (code, user_id),
            )
            ids = [int(r[0]) for r in cursor.fetchall()]
            for drop_id in ids[1:]:
                cursor.execute("DELETE FROM portfolio WHERE id = ?", (drop_id,))
                removed += 1
        return removed

    def _normalize_username_seed(self, seed: str) -> str:
        s = (seed or "").strip().lower()
        if "@" in s:
            s = s.split("@", 1)[0]
        s = re.sub(r"[^a-z0-9_]", "_", s)
        s = re.sub(r"_+", "_", s).strip("_")
        if not s:
            s = "user"
        if not s[0].isalpha():
            s = f"u_{s}"
        if len(s) < 4:
            s = (s + "user")[:4]
        return s[:24]

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
            "last_login",
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
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
                        user_number, is_admin, status, created_at, last_login
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        row.get("last_login"),
                    ),
                )
            cursor.execute("DROP TABLE users")
            cursor.execute("ALTER TABLE users_new RENAME TO users")
        else:
            def _ensure_column(column: str, col_def: str) -> None:
                cursor.execute("PRAGMA table_info(users)")
                cur_cols = [row[1] for row in cursor.fetchall()]
                if column not in cur_cols:
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
            _ensure_column("created_at", "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            _ensure_column("last_login", "last_login TIMESTAMP")

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
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_status ON users(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_user_number ON users(user_number)")

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

    def get_user_auth_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户的后台权限信息。"""
        if not user_id:
            return None
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT id, username, is_admin, status, must_change_password
                FROM users
                WHERE id = ?
                LIMIT 1
            ''', (user_id,))
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
                       user_number, is_admin, created_at, last_login, legacy_needs_password_setup,
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
        u = (username or "").strip().lower()
        if not u:
            return None
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                '''
                SELECT id, username, password_hash, legacy_needs_password_setup,
                       must_change_password, password_reset_at, password_reset_by,
                       nickname, avatar, register_method, phone, user_number,
                       is_admin, status, created_at, last_login
                FROM users
                WHERE username = ?
                LIMIT 1
                ''',
                (u,),
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
                       is_admin, status, created_at, last_login
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
        u = (username or "").strip().lower()
        user_id = user_id or uuid.uuid4().hex
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT MAX(user_number) AS max_num FROM users"
            )
            row = cursor.fetchone()
            max_num = int(row["max_num"] or 9999) if row else 9999
            user_number = max_num + 1
            cursor.execute(
                """
                INSERT INTO users (
                    id, username, password_hash, legacy_needs_password_setup,
                    password_updated_at, register_method, user_number, is_admin
                ) VALUES (?, ?, ?, 0, CURRENT_TIMESTAMP, ?, ?, ?)
                """,
                (user_id, u, password_hash, register_method, user_number, 1 if is_admin else 0),
            )
            conn.commit()
            return {"id": user_id, "username": u, "user_number": user_number, "is_admin": bool(is_admin)}
        except Exception as e:
            logger.error("Failed to create user: %s", e)
            conn.rollback()
            raise
        finally:
            conn.close()

    def update_last_login(self, user_id: str) -> None:
        if not user_id:
            return
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user_id,),
            )
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
                    password_updated_at = CURRENT_TIMESTAMP
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
                        password_reset_at = CURRENT_TIMESTAMP,
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
                    password_reset_at = CURRENT_TIMESTAMP,
                    password_reset_by = ?,
                    password_updated_at = CURRENT_TIMESTAMP
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
        u = (username or "").strip().lower()
        try:
            cursor.execute("SELECT id FROM users WHERE username = ? AND id != ?", (u, user_id))
            if cursor.fetchone():
                return False, "Username already exists"
            cursor.execute(
                """
                UPDATE users
                SET username = ?, password_hash = ?, legacy_needs_password_setup = 0, password_updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND (legacy_needs_password_setup = 1 OR COALESCE(password_hash, '') = '')
                """,
                (u, password_hash, user_id),
            )
            if cursor.rowcount <= 0:
                conn.rollback()
                return False, "Bootstrap already completed"
            conn.commit()
            return True, ""
        except Exception:
            conn.rollback()
            return False, "Bootstrap failed"
        finally:
            conn.close()

    def create_refresh_token(
        self,
        user_id: str,
        token_hash: str,
        expires_at: datetime,
        device_id: str = "",
    ) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        now_iso = datetime.utcnow().isoformat()
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
                (datetime.utcnow().isoformat(), token_hash),
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
                (datetime.utcnow().isoformat(), token_hash),
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
                (datetime.utcnow().isoformat(), user_id),
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
        now_utc = now or datetime.utcnow()
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
        st = str(scope_type or "").strip().lower()
        if st and st != "all":
            where = "WHERE scope_type = ?"
            params.append(st)
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
            return [dict(r) for r in cursor.fetchall()]
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
        updates.append("updated_at = CURRENT_TIMESTAMP")
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
        c = (code or "").strip().upper()
        if not c:
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
                (c,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def consume_invite_code(self, code: str, user_id: str) -> Tuple[bool, str]:
        c = (code or "").strip().upper()
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE invite_codes
                SET status = 'used', used_by_user_id = ?, used_at = CURRENT_TIMESTAMP
                WHERE code = ? AND status = 'active' AND used_by_user_id IS NULL
                """,
                (user_id, c),
            )
            if cursor.rowcount <= 0:
                conn.rollback()
                return False, "Invite code invalid or already used"
            conn.commit()
            return True, ""
        except Exception:
            conn.rollback()
            return False, "Invite code invalid or already used"
        finally:
            conn.close()

    def revoke_invite_code(self, code: str) -> bool:
        c = (code or "").strip().upper()
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE invite_codes SET status = 'revoked' WHERE code = ? AND status = 'active'",
                (c,),
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
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"SELECT COUNT(1) AS c FROM invite_codes ic {where_sql}",
                tuple(params),
            )
            total = int(cursor.fetchone()["c"])
            cursor.execute(
                f"""
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
                ORDER BY ic.created_at DESC, ic.code ASC
                LIMIT ? OFFSET ?
                """,
                tuple(params + [limit, offset]),
            )
            items = [dict(r) for r in cursor.fetchall()]
            return {"items": items, "total": total, "limit": limit, "offset": offset}
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
                t: self._table_rebind_count(cursor, t, target_user_id)
                for t in tables
            }
            source_distribution: Dict[str, Dict[str, int]] = {}
            for t in tables:
                cursor.execute(
                    f"""
                    SELECT COALESCE(NULLIF(TRIM(user_id), ''), '__local__') AS source_user_id, COUNT(1) AS c
                    FROM {t}
                    WHERE COALESCE(user_id, '') != ?
                    GROUP BY COALESCE(NULLIF(TRIM(user_id), ''), '__local__')
                    ORDER BY c DESC
                    """,
                    (target_user_id,),
                )
                source_distribution[t] = {
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
        except Exception as e:
            logger.error("Failed to execute user rebind: %s", e)
            conn.rollback()
            return {"error": "Failed to execute rebind"}
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
        target_type: str = '',
        target_id: str = '',
        ip: str = '',
        request_body: str = '',
        error: str = '',
    ) -> bool:
        """记录后台审计日志。"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO admin_audit_logs (
                    admin_user_id, action, target_type, target_id,
                    method, path, ip, request_body, status_code, result, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
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
            ))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to add admin audit log: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_user_ids(self) -> List[str]:
        """获取所有用户ID（用于批量快照）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT id FROM users')
            return [row['id'] for row in cursor.fetchall() if row['id']]
        except Exception as e:
            logger.error(f"Failed to get user ids: {e}")
            return []
        finally:
            conn.close()
        logger.info("Database initialized successfully")

    def _ensure_portfolio_asset_type(self, cursor) -> None:
        """确保 portfolio 表有 asset_type 字段，并回填默认值"""
        try:
            cursor.execute("PRAGMA table_info(portfolio)")
            cols = [row[1] for row in cursor.fetchall()]
            if 'asset_type' not in cols:
                cursor.execute("ALTER TABLE portfolio ADD COLUMN asset_type TEXT DEFAULT 'a'")
                logger.info("Added asset_type column to portfolio")
            # 回填空值
            cursor.execute("SELECT code, name FROM portfolio WHERE asset_type IS NULL OR asset_type = ''")
            rows = cursor.fetchall()
            if rows:
                from .asset_type import infer_asset_type
                for row in rows:
                    code = row[0]
                    name = row[1]
                    asset_type = infer_asset_type(code, name)
                    cursor.execute(
                        "UPDATE portfolio SET asset_type = ? WHERE code = ?",
                        (asset_type, code)
                    )
                logger.info(f"Backfilled asset_type for {len(rows)} records")
        except Exception as e:
            logger.warning(f"Failed to ensure asset_type column: {e}")

    def _ensure_daily_snapshots_schema(self, cursor) -> None:
        """
        统一 daily_snapshots 表结构到：
        - user_id 非空（默认 ''）
        - 唯一键 UNIQUE(date, user_id)
        并对历史重复数据做去重（保留最新 id）。
        """
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='daily_snapshots'")
        row = cursor.fetchone()
        table_sql = (row[0] or '').upper() if row and row[0] else ''
        has_old_date_unique = 'DATE TEXT NOT NULL UNIQUE' in table_sql
        has_new_unique = 'UNIQUE(DATE, USER_ID)' in table_sql

        if has_old_date_unique or not has_new_unique:
            logger.info("Migrating daily_snapshots schema to UNIQUE(date, user_id)")
            cursor.execute('DROP TABLE IF EXISTS daily_snapshots_new')
            cursor.execute('''
                CREATE TABLE daily_snapshots_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    total_asset REAL NOT NULL,
                    total_invest REAL NOT NULL,
                    total_cash REAL NOT NULL,
                    total_other REAL NOT NULL,
                    total_liability REAL NOT NULL,
                    total_pnl REAL NOT NULL,
                    day_pnl REAL NOT NULL,
                    user_id TEXT NOT NULL DEFAULT '',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, user_id)
                )
            ''')

            # 按 (date, user_id) 去重，保留最新一条
            cursor.execute('''
                INSERT INTO daily_snapshots_new (
                    date, total_asset, total_invest, total_cash,
                    total_other, total_liability, total_pnl, day_pnl, user_id, updated_at
                )
                SELECT
                    d.date, d.total_asset, d.total_invest, d.total_cash,
                    d.total_other, d.total_liability, d.total_pnl, d.day_pnl,
                    COALESCE(d.user_id, '') AS user_id,
                    d.updated_at
                FROM daily_snapshots d
                INNER JOIN (
                    SELECT MAX(id) AS id
                    FROM daily_snapshots
                    GROUP BY date, COALESCE(user_id, '')
                ) t ON d.id = t.id
            ''')

            cursor.execute('DROP TABLE daily_snapshots')
            cursor.execute('ALTER TABLE daily_snapshots_new RENAME TO daily_snapshots')
            logger.info("daily_snapshots schema migration completed")
    def get_portfolio(
        self,
        asset_type: str = 'all',
        user_id: str = None,
        include_closed: bool = False,
    ) -> List[Dict[str, Any]]:
        """获取持仓数据，支持按类型筛选。

        默认只返回 qty > 0 的"当前持仓"。当 include_closed=True 时也包含 qty=0 的已清仓记录，
        主要用于累计盈亏(total_pnl=未实现+已实现)计算。
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        logger.info(f"get_portfolio called with asset_type: {asset_type}, user_id: {user_id}")

        # 构建 user_id 条件
        user_condition = "user_id = ?" if user_id else "(user_id IS NULL OR user_id = '')"
        user_param = (user_id,) if user_id else ()
        qty_condition = "" if include_closed else " AND qty > 0"

        if asset_type == 'all':
            cursor.execute(f'''
                SELECT code, name, qty, price, curr, adjustment, asset_type
                FROM portfolio
                WHERE {user_condition}{qty_condition}
                ORDER BY code
            ''', user_param)
        elif asset_type in ('a', 'us', 'hk', 'fund'):
            cursor.execute(f'''
                SELECT code, name, qty, price, curr, adjustment, asset_type
                FROM portfolio
                WHERE {user_condition}{qty_condition} AND asset_type = ?
                ORDER BY code
            ''', user_param + (asset_type,))
        else:
            cursor.execute(f'''
                SELECT code, name, qty, price, curr, adjustment, asset_type
                FROM portfolio
                WHERE {user_condition}{qty_condition}
                ORDER BY code
            ''', user_param)

        data = []
        for row in cursor.fetchall():
            data.append({
                'code': row['code'],
                'name': row['name'],
                'qty': float(row['qty']),
                'price': float(row['price']),
                'curr': row['curr'],
                'adjustment': float(row['adjustment']),
                'asset_type': row['asset_type'] if 'asset_type' in row.keys() else ''
            })

        logger.info(f"get_portfolio returned {len(data)} records for type {asset_type}")

        conn.close()
        return data

    
    def get_asset(self, code: str, user_id: str = None) -> Optional[Dict[str, Any]]:
        """获取单个资产信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute('''
                SELECT code, name, qty, price, curr, adjustment, asset_type
                FROM portfolio
                WHERE code = ? AND user_id = ?
            ''', (code, user_id))
        else:
            cursor.execute('''
                SELECT code, name, qty, price, curr, adjustment, asset_type
                FROM portfolio
                WHERE code = ? AND (user_id IS NULL OR user_id = '')
            ''', (code,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'code': row['code'],
                'name': row['name'],
                'qty': float(row['qty']),
                'price': float(row['price']),
                'curr': row['curr'],
                'adjustment': float(row['adjustment']),
                'asset_type': row['asset_type'] if 'asset_type' in row.keys() else ''
            }
        return None
    
    def add_asset(self, data: Dict[str, Any], user_id: str = None) -> bool:
        """添加或更新资产"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            incoming_name = str(data.get('name') or '').strip()
            if user_id:
                cursor.execute(
                    '''
                    SELECT id, name FROM portfolio WHERE code = ? AND user_id = ?
                    ''',
                    (data['code'], user_id),
                )
            else:
                cursor.execute(
                    '''
                    SELECT id, name FROM portfolio WHERE code = ? AND (user_id IS NULL OR user_id = '')
                    ''',
                    (data['code'],),
                )
            existing = cursor.fetchone()

            if existing:
                existing_name = str(existing['name'] or '').strip()
                # 已有名称优先，避免被搜索短名覆盖；仅当原名称为空时才回填新名称。
                next_name = existing_name or incoming_name or data['code']
                if user_id:
                    cursor.execute(
                        '''
                        UPDATE portfolio
                        SET name=?, qty=?, price=?, curr=?, adjustment=?, asset_type=?, updated_at=CURRENT_TIMESTAMP
                        WHERE code = ? AND user_id = ?
                        ''',
                        (
                            next_name,
                            data['qty'],
                            data['price'],
                            data.get('curr', 'CNY'),
                            data.get('adjustment', 0.0),
                            data.get('asset_type', 'a'),
                            data['code'],
                            user_id,
                        ),
                    )
                else:
                    cursor.execute(
                        '''
                        UPDATE portfolio
                        SET name=?, qty=?, price=?, curr=?, adjustment=?, asset_type=?, updated_at=CURRENT_TIMESTAMP
                        WHERE code = ? AND (user_id IS NULL OR user_id = '')
                        ''',
                        (
                            next_name,
                            data['qty'],
                            data['price'],
                            data.get('curr', 'CNY'),
                            data.get('adjustment', 0.0),
                            data.get('asset_type', 'a'),
                            data['code'],
                        ),
                    )
            else:
                next_name = incoming_name or data['code']
                if user_id:
                    cursor.execute(
                        '''
                        INSERT INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, user_id, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        ''',
                        (
                            data['code'],
                            next_name,
                            data['qty'],
                            data['price'],
                            data.get('curr', 'CNY'),
                            data.get('adjustment', 0.0),
                            data.get('asset_type', 'a'),
                            user_id,
                        ),
                    )
                else:
                    cursor.execute(
                        '''
                        INSERT INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        ''',
                        (
                            data['code'],
                            next_name,
                            data['qty'],
                            data['price'],
                            data.get('curr', 'CNY'),
                            data.get('adjustment', 0.0),
                            data.get('asset_type', 'a'),
                        ),
                    )
            
            conn.commit()
            logger.info(f"Asset added/updated: {data['code']}")
            return True
        except Exception as e:
            logger.error(
                "Failed to add asset: code=%s user_id=%s err=%s",
                data.get('code'),
                user_id or '',
                e,
            )
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def update_asset(self, code: str, field: str, value: float, user_id: str = None) -> bool:
        """更新资产字段"""
        if field not in self.VALID_FIELDS:
            logger.error(f"Invalid field name: {field}")
            return False
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 构建 user_id 条件
            if user_id:
                user_condition = "AND user_id = ?"
                params_suffix = (code, user_id)
            else:
                user_condition = "AND (user_id IS NULL OR user_id = '')"
                params_suffix = (code,)
            
            # 对于 adjustment 字段，需要累加
            if field == 'adjustment':
                cursor.execute(f'''
                    UPDATE portfolio SET adjustment = COALESCE(adjustment, 0) + ?, updated_at = CURRENT_TIMESTAMP
                    WHERE code = ? {user_condition}
                ''', (value,) + params_suffix)
            else:
                cursor.execute(f'''
                    UPDATE portfolio SET {field} = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE code = ? {user_condition}
                ''', (value,) + params_suffix)
            
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"Asset updated: {code}, {field} = {value}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update asset: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def modify_asset(
        self,
        code: str,
        qty: float,
        price: float,
        adjustment: float,
        user_id: str = None,
        return_detail: bool = False,
    ):
        """修正资产数据（数量、成本、调整值）"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            if user_id:
                cursor.execute(
                    '''
                    SELECT name, qty, price, curr, adjustment, asset_type
                    FROM portfolio
                    WHERE code = ? AND user_id = ?
                    ''',
                    (code, user_id),
                )
            else:
                cursor.execute(
                    '''
                    SELECT name, qty, price, curr, adjustment, asset_type
                    FROM portfolio
                    WHERE code = ? AND (user_id IS NULL OR user_id = '')
                    ''',
                    (code,),
                )
            old_row = cursor.fetchone()
            if not old_row:
                if return_detail:
                    return {'ok': False, 'code': 'ASSET_NOT_FOUND', 'error': 'Asset not found'}
                return False

            before_asset = {
                'code': code,
                'name': old_row['name'],
                'qty': float(old_row['qty']),
                'price': float(old_row['price']),
                'curr': old_row['curr'],
                'adjustment': float(old_row['adjustment']),
                'asset_type': old_row['asset_type'] if 'asset_type' in old_row.keys() else 'a',
            }

            if user_id:
                cursor.execute(
                    '''
                    UPDATE portfolio
                    SET qty = ?, price = ?, adjustment = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE code = ? AND user_id = ?
                    ''',
                    (qty, price, adjustment, code, user_id),
                )
            else:
                cursor.execute(
                    '''
                    UPDATE portfolio
                    SET qty = ?, price = ?, adjustment = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE code = ? AND (user_id IS NULL OR user_id = '')
                    ''',
                    (qty, price, adjustment, code),
                )

            if cursor.rowcount <= 0:
                if return_detail:
                    return {'ok': False, 'code': 'ASSET_NOT_FOUND', 'error': 'Asset not found'}
                return False

            conn.commit()
            logger.info(f"Asset modified: {code}, qty={qty}, price={price}, adj={adjustment}")
            if return_detail:
                return {
                    'ok': True,
                    'before_asset': before_asset,
                    'after_asset': {
                        'code': code,
                        'name': before_asset['name'],
                        'qty': float(qty),
                        'price': float(price),
                        'curr': before_asset['curr'],
                        'adjustment': float(adjustment),
                        'asset_type': before_asset['asset_type'],
                    },
                }
            return True
        except Exception as e:
            logger.error(f"Failed to modify asset: {e}")
            conn.rollback()
            if return_detail:
                return {'ok': False, 'code': 'ASSET_MODIFY_FAILED', 'error': 'Failed to modify asset'}
            return False
        finally:
            conn.close()

    def delete_asset(self, code: str, user_id: str = None) -> bool:
        """删除资产"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if user_id:
                cursor.execute('DELETE FROM portfolio WHERE code = ? AND user_id = ?', (code, user_id))
            else:
                cursor.execute('DELETE FROM portfolio WHERE code = ? AND (user_id IS NULL OR user_id = "")', (code,))
            conn.commit()
            logger.info(f"Asset deleted: {code}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete asset: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def delete_asset_corrective(self, code: str, user_id: str = None) -> Optional[Dict[str, Any]]:
        """删除资产并清理该资产交易历史与受影响快照区间"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            if user_id:
                cursor.execute(
                    '''
                    SELECT time
                    FROM transactions
                    WHERE code = ? AND user_id = ?
                    ORDER BY time ASC
                    LIMIT 1
                    ''',
                    (code, user_id),
                )
                tx_row = cursor.fetchone()
                cursor.execute(
                    '''
                    SELECT created_at, updated_at
                    FROM portfolio
                    WHERE code = ? AND user_id = ?
                    LIMIT 1
                    ''',
                    (code, user_id),
                )
                pf_row = cursor.fetchone()
            else:
                cursor.execute(
                    '''
                    SELECT time
                    FROM transactions
                    WHERE code = ? AND (user_id IS NULL OR user_id = '')
                    ORDER BY time ASC
                    LIMIT 1
                    ''',
                    (code,),
                )
                tx_row = cursor.fetchone()
                cursor.execute(
                    '''
                    SELECT created_at, updated_at
                    FROM portfolio
                    WHERE code = ? AND (user_id IS NULL OR user_id = '')
                    LIMIT 1
                    ''',
                    (code,),
                )
                pf_row = cursor.fetchone()

            from_date = datetime.now().strftime('%Y-%m-%d')
            tx_time = str(tx_row['time']) if tx_row and tx_row['time'] else ''
            if len(tx_time) >= 10:
                from_date = tx_time[:10]
            elif pf_row:
                pf_time = str(pf_row['updated_at'] or pf_row['created_at'] or '')
                if len(pf_time) >= 10:
                    from_date = pf_time[:10]

            if user_id:
                cursor.execute(
                    'DELETE FROM portfolio WHERE code = ? AND user_id = ?',
                    (code, user_id),
                )
            else:
                cursor.execute(
                    "DELETE FROM portfolio WHERE code = ? AND (user_id IS NULL OR user_id = '')",
                    (code,),
                )
            portfolio_deleted = cursor.rowcount

            if user_id:
                cursor.execute(
                    'DELETE FROM transactions WHERE code = ? AND user_id = ?',
                    (code, user_id),
                )
            else:
                cursor.execute(
                    "DELETE FROM transactions WHERE code = ? AND (user_id IS NULL OR user_id = '')",
                    (code,),
                )
            tx_deleted = cursor.rowcount

            if portfolio_deleted <= 0 and tx_deleted <= 0:
                logger.info(f"Corrective delete noop: {code}")

            if user_id:
                cursor.execute(
                    'DELETE FROM daily_snapshots WHERE date >= ? AND user_id = ?',
                    (from_date, user_id),
                )
            else:
                cursor.execute(
                    "DELETE FROM daily_snapshots WHERE date >= ? AND (user_id IS NULL OR user_id = '')",
                    (from_date,),
                )
            snapshots_deleted = cursor.rowcount

            conn.commit()
            logger.info(
                "Corrective delete done: code=%s from_date=%s portfolio=%s tx=%s snapshots=%s",
                code,
                from_date,
                portfolio_deleted,
                tx_deleted,
                snapshots_deleted,
            )
            return {
                'portfolio': int(portfolio_deleted),
                'transactions': int(tx_deleted),
                'snapshots': int(snapshots_deleted),
                'from_date': from_date,
            }
        except Exception as e:
            logger.error(f"Failed to corrective delete asset: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def buy_asset(
        self,
        code: str,
        price: float,
        qty: float,
        user_id: str = None,
        return_detail: bool = False,
    ):
        """加仓"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            if user_id:
                cursor.execute(
                    '''
                    SELECT name, qty, price, curr, adjustment, asset_type
                    FROM portfolio
                    WHERE code = ? AND user_id = ?
                    ''',
                    (code, user_id),
                )
            else:
                cursor.execute(
                    '''
                    SELECT name, qty, price, curr, adjustment, asset_type
                    FROM portfolio
                    WHERE code = ? AND (user_id IS NULL OR user_id = '')
                    ''',
                    (code,),
                )
            row = cursor.fetchone()

            if not row:
                if return_detail:
                    return {'ok': False, 'code': 'ASSET_NOT_FOUND', 'error': 'Asset not found'}
                return False

            name = row['name']
            old_qty = float(row['qty'])
            old_price = float(row['price'])
            old_adjustment = float(row['adjustment'])
            curr = row['curr']
            asset_type = row['asset_type'] if 'asset_type' in row.keys() else 'a'

            before_asset = {
                'code': code,
                'name': name,
                'qty': old_qty,
                'price': old_price,
                'curr': curr,
                'adjustment': old_adjustment,
                'asset_type': asset_type,
            }

            new_qty = old_qty + qty
            new_price = (old_qty * old_price + qty * price) / new_qty if new_qty > 0 else 0

            if user_id:
                cursor.execute(
                    '''
                    UPDATE portfolio SET qty = ?, price = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE code = ? AND user_id = ?
                    ''',
                    (new_qty, new_price, code, user_id),
                )
            else:
                cursor.execute(
                    '''
                    UPDATE portfolio SET qty = ?, price = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE code = ? AND (user_id IS NULL OR user_id = '')
                    ''',
                    (new_qty, new_price, code),
                )

            cursor.execute(
                '''
                INSERT INTO transactions (time, code, name, type, price, qty, amount, pnl, user_id)
                VALUES (?, ?, ?, '加仓', ?, ?, ?, 0, ?)
                ''',
                (
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    code,
                    name,
                    price,
                    qty,
                    price * qty,
                    user_id,
                ),
            )
            tx_id = int(cursor.lastrowid or 0)

            conn.commit()
            logger.info(f"Buy: {code}, qty={qty}, price={price}")
            if return_detail:
                return {
                    'ok': True,
                    'tx_id': tx_id,
                    'before_asset': before_asset,
                    'after_asset': {
                        'code': code,
                        'name': name,
                        'qty': float(new_qty),
                        'price': float(new_price),
                        'curr': curr,
                        'adjustment': old_adjustment,
                        'asset_type': asset_type,
                    },
                }
            return True
        except Exception as e:
            logger.error(f"Failed to buy asset: {e}")
            conn.rollback()
            if return_detail:
                return {'ok': False, 'code': 'ASSET_BUY_FAILED', 'error': 'Failed to buy asset'}
            return False
        finally:
            conn.close()
    
    def sell_asset(
        self,
        code: str,
        price: float,
        qty: float,
        user_id: str = None,
        return_detail: bool = False,
    ):
        """减仓"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            if user_id:
                cursor.execute(
                    '''
                    SELECT name, qty, price, curr, adjustment, asset_type
                    FROM portfolio
                    WHERE code = ? AND user_id = ?
                    ''',
                    (code, user_id),
                )
            else:
                cursor.execute(
                    '''
                    SELECT name, qty, price, curr, adjustment, asset_type
                    FROM portfolio
                    WHERE code = ? AND (user_id IS NULL OR user_id = '')
                    ''',
                    (code,),
                )
            row = cursor.fetchone()

            if not row:
                if return_detail:
                    return {'ok': False, 'code': 'ASSET_NOT_FOUND', 'error': 'Asset not found'}
                return False

            name = row['name']
            old_qty = float(row['qty'])
            old_price = float(row['price'])
            curr = row['curr']
            old_adj = float(row['adjustment'])
            asset_type = row['asset_type'] if 'asset_type' in row.keys() else 'a'

            if qty > old_qty + 1e-6:
                logger.warning(f"Oversell: {code}")
                if return_detail:
                    return {'ok': False, 'code': 'OVERSELL', 'error': 'Sell quantity exceeds holding'}
                return False

            before_asset = {
                'code': code,
                'name': name,
                'qty': old_qty,
                'price': old_price,
                'curr': curr,
                'adjustment': old_adj,
                'asset_type': asset_type,
            }

            pnl = (price - old_price) * qty
            new_qty = old_qty - qty
            if new_qty < 0.001:
                # 不删除记录：保留 qty=0 + adjustment 累积的已实现收益，避免累计收益丢失。
                if user_id:
                    cursor.execute(
                        '''
                        UPDATE portfolio
                        SET qty = 0, adjustment = COALESCE(adjustment, 0) + ?, updated_at = CURRENT_TIMESTAMP
                        WHERE code = ? AND user_id = ?
                        ''',
                        (pnl, code, user_id),
                    )
                else:
                    cursor.execute(
                        '''
                        UPDATE portfolio
                        SET qty = 0, adjustment = COALESCE(adjustment, 0) + ?, updated_at = CURRENT_TIMESTAMP
                        WHERE code = ? AND (user_id IS NULL OR user_id = '')
                        ''',
                        (pnl, code),
                    )
                after_asset = None
            else:
                if user_id:
                    cursor.execute(
                        '''
                        UPDATE portfolio SET qty = ?, adjustment = adjustment + ?, updated_at = CURRENT_TIMESTAMP
                        WHERE code = ? AND user_id = ?
                        ''',
                        (new_qty, pnl, code, user_id),
                    )
                else:
                    cursor.execute(
                        '''
                        UPDATE portfolio SET qty = ?, adjustment = adjustment + ?, updated_at = CURRENT_TIMESTAMP
                        WHERE code = ? AND (user_id IS NULL OR user_id = '')
                        ''',
                        (new_qty, pnl, code),
                    )
                after_asset = {
                    'code': code,
                    'name': name,
                    'qty': float(new_qty),
                    'price': old_price,
                    'curr': curr,
                    'adjustment': old_adj + pnl,
                    'asset_type': asset_type,
                }

            cursor.execute(
                '''
                INSERT INTO transactions (time, code, name, type, price, qty, amount, pnl, user_id)
                VALUES (?, ?, ?, '减仓', ?, ?, ?, ?, ?)
                ''',
                (
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    code,
                    name,
                    price,
                    qty,
                    price * qty,
                    pnl,
                    user_id,
                ),
            )
            tx_id = int(cursor.lastrowid or 0)

            conn.commit()
            logger.info(f"Sell: {code}, qty={qty}, price={price}, pnl={pnl}")
            if return_detail:
                return {
                    'ok': True,
                    'tx_id': tx_id,
                    'before_asset': before_asset,
                    'after_asset': after_asset,
                }
            return True
        except Exception as e:
            logger.error(f"Failed to sell asset: {e}")
            conn.rollback()
            if return_detail:
                return {'ok': False, 'code': 'ASSET_SELL_FAILED', 'error': 'Failed to sell asset'}
            return False
        finally:
            conn.close()

    def buy_asset_with_cash(
        self,
        code: str,
        name: str,
        price: float,
        qty: float,
        curr: str,
        asset_type: str,
        cash_asset_id: int,
        cash_deduct_amount: float,
        user_id: str = None,
    ) -> Dict[str, Any]:
        """使用现金账户买入（扣现金 + 增持仓，同一事务）"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            if qty <= 0 or price <= 0:
                return {'ok': False, 'code': 'INVALID_VALUE', 'error': 'Invalid value'}
            if cash_deduct_amount <= 0:
                return {'ok': False, 'code': 'INVALID_CASH_AMOUNT', 'error': 'Invalid cash deduction amount'}

            if user_id:
                cursor.execute(
                    '''
                    SELECT id, name, amount, curr
                    FROM cash_assets
                    WHERE id = ? AND user_id = ?
                    ''',
                    (cash_asset_id, user_id),
                )
            else:
                cursor.execute(
                    '''
                    SELECT id, name, amount, curr
                    FROM cash_assets
                    WHERE id = ? AND (user_id IS NULL OR user_id = '')
                    ''',
                    (cash_asset_id,),
                )
            cash_row = cursor.fetchone()
            if not cash_row:
                return {'ok': False, 'code': 'CASH_ASSET_NOT_FOUND', 'error': 'Cash account not found'}

            cash_before = float(cash_row['amount'])
            if cash_before + 1e-9 < cash_deduct_amount:
                return {
                    'ok': False,
                    'code': 'INSUFFICIENT_CASH',
                    'error': 'Insufficient cash balance',
                    'available': cash_before,
                    'required': float(cash_deduct_amount),
                    'cash_curr': cash_row['curr'],
                }
            cash_after = cash_before - cash_deduct_amount

            if user_id:
                cursor.execute(
                    '''
                    UPDATE cash_assets
                    SET amount = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ?
                    ''',
                    (cash_after, cash_asset_id, user_id),
                )
            else:
                cursor.execute(
                    '''
                    UPDATE cash_assets
                    SET amount = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND (user_id IS NULL OR user_id = '')
                    ''',
                    (cash_after, cash_asset_id),
                )
            if cursor.rowcount <= 0:
                return {'ok': False, 'code': 'CASH_ASSET_UPDATE_FAILED', 'error': 'Failed to update cash asset'}

            if user_id:
                cursor.execute(
                    '''
                    SELECT name, qty, price, curr, adjustment, asset_type
                    FROM portfolio
                    WHERE code = ? AND user_id = ?
                    ''',
                    (code, user_id),
                )
            else:
                cursor.execute(
                    '''
                    SELECT name, qty, price, curr, adjustment, asset_type
                    FROM portfolio
                    WHERE code = ? AND (user_id IS NULL OR user_id = '')
                    ''',
                    (code,),
                )
            row = cursor.fetchone()

            before_asset = None
            if row:
                old_name = row['name']
                old_qty = float(row['qty'])
                old_price = float(row['price'])
                old_adjustment = float(row['adjustment'])
                old_curr = row['curr']
                old_asset_type = row['asset_type'] if 'asset_type' in row.keys() else 'a'
                before_asset = {
                    'code': code,
                    'name': old_name,
                    'qty': old_qty,
                    'price': old_price,
                    'curr': old_curr,
                    'adjustment': old_adjustment,
                    'asset_type': old_asset_type,
                }

                new_qty = old_qty + qty
                new_price = (old_qty * old_price + qty * price) / new_qty if new_qty > 0 else 0
                if user_id:
                    cursor.execute(
                        '''
                        UPDATE portfolio SET qty = ?, price = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE code = ? AND user_id = ?
                        ''',
                        (new_qty, new_price, code, user_id),
                    )
                else:
                    cursor.execute(
                        '''
                        UPDATE portfolio SET qty = ?, price = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE code = ? AND (user_id IS NULL OR user_id = '')
                        ''',
                        (new_qty, new_price, code),
                    )
                after_asset = {
                    'code': code,
                    'name': old_name,
                    'qty': float(new_qty),
                    'price': float(new_price),
                    'curr': old_curr,
                    'adjustment': old_adjustment,
                    'asset_type': old_asset_type,
                }
                tx_name = old_name
            else:
                tx_name = (name or code).strip() or code
                next_asset_type = (asset_type or 'a').strip() or 'a'
                next_curr = (curr or 'CNY').strip() or 'CNY'
                if user_id:
                    cursor.execute(
                        '''
                        INSERT INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, user_id, updated_at)
                        VALUES (?, ?, ?, ?, ?, 0, ?, ?, CURRENT_TIMESTAMP)
                        ''',
                        (code, tx_name, qty, price, next_curr, next_asset_type, user_id),
                    )
                else:
                    cursor.execute(
                        '''
                        INSERT INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, updated_at)
                        VALUES (?, ?, ?, ?, ?, 0, ?, CURRENT_TIMESTAMP)
                        ''',
                        (code, tx_name, qty, price, next_curr, next_asset_type),
                    )
                after_asset = {
                    'code': code,
                    'name': tx_name,
                    'qty': float(qty),
                    'price': float(price),
                    'curr': next_curr,
                    'adjustment': 0.0,
                    'asset_type': next_asset_type,
                }

            cursor.execute(
                '''
                INSERT INTO transactions (time, code, name, type, price, qty, amount, pnl, user_id)
                VALUES (?, ?, ?, '加仓', ?, ?, ?, 0, ?)
                ''',
                (
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    code,
                    tx_name,
                    price,
                    qty,
                    price * qty,
                    user_id,
                ),
            )
            tx_id = int(cursor.lastrowid or 0)

            conn.commit()
            return {
                'ok': True,
                'tx_id': tx_id,
                'before_asset': before_asset,
                'after_asset': after_asset,
                'cash_asset_id': int(cash_asset_id),
                'cash_curr': cash_row['curr'],
                'cash_before_amount': cash_before,
                'cash_after_amount': cash_after,
                'cash_deduct_amount': float(cash_deduct_amount),
            }
        except Exception as e:
            logger.error(
                "Failed to buy asset with cash: code=%s user_id=%s cash_asset_id=%s err=%s",
                code,
                user_id or '',
                cash_asset_id,
                e,
            )
            conn.rollback()
            return {'ok': False, 'code': 'ASSET_BUY_WITH_CASH_FAILED', 'error': 'Failed to buy asset with cash'}
        finally:
            conn.close()

    def undo_invest_operation(self, operation: Dict[str, Any], user_id: str = None) -> Dict[str, Any]:
        """撤销投资写操作（买入/卖出/调整）"""
        if not isinstance(operation, dict):
            return {'ok': False, 'code': 'INVALID_OPERATION', 'error': 'Invalid undo operation'}

        code = str(operation.get('code') or '').strip()
        if not code:
            return {'ok': False, 'code': 'INVALID_OPERATION', 'error': 'Missing code in undo operation'}

        before_asset = operation.get('before_asset')
        tx_id = operation.get('tx_id')
        cash_asset_id = operation.get('cash_asset_id')
        cash_before_amount = operation.get('cash_before_amount')

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if before_asset is None:
                if user_id:
                    cursor.execute('DELETE FROM portfolio WHERE code = ? AND user_id = ?', (code, user_id))
                else:
                    cursor.execute(
                        "DELETE FROM portfolio WHERE code = ? AND (user_id IS NULL OR user_id = '')",
                        (code,),
                    )
            else:
                name = str(before_asset.get('name') or code)
                qty = float(before_asset.get('qty') or 0.0)
                price = float(before_asset.get('price') or 0.0)
                curr = str(before_asset.get('curr') or 'CNY')
                adjustment = float(before_asset.get('adjustment') or 0.0)
                asset_type = str(before_asset.get('asset_type') or 'a')

                if user_id:
                    cursor.execute(
                        '''
                        SELECT id FROM portfolio WHERE code = ? AND user_id = ?
                        ''',
                        (code, user_id),
                    )
                else:
                    cursor.execute(
                        '''
                        SELECT id FROM portfolio WHERE code = ? AND (user_id IS NULL OR user_id = '')
                        ''',
                        (code,),
                    )
                existing = cursor.fetchone()
                if existing:
                    if user_id:
                        cursor.execute(
                            '''
                            UPDATE portfolio
                            SET name = ?, qty = ?, price = ?, curr = ?, adjustment = ?, asset_type = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE code = ? AND user_id = ?
                            ''',
                            (name, qty, price, curr, adjustment, asset_type, code, user_id),
                        )
                    else:
                        cursor.execute(
                            '''
                            UPDATE portfolio
                            SET name = ?, qty = ?, price = ?, curr = ?, adjustment = ?, asset_type = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE code = ? AND (user_id IS NULL OR user_id = '')
                            ''',
                            (name, qty, price, curr, adjustment, asset_type, code),
                        )
                else:
                    if user_id:
                        cursor.execute(
                            '''
                            INSERT INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, user_id, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                            ''',
                            (code, name, qty, price, curr, adjustment, asset_type, user_id),
                        )
                    else:
                        cursor.execute(
                            '''
                            INSERT INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                            ''',
                            (code, name, qty, price, curr, adjustment, asset_type),
                        )

            if tx_id is not None:
                try:
                    tx_id_int = int(tx_id)
                except (TypeError, ValueError):
                    tx_id_int = 0
                if tx_id_int > 0:
                    if user_id:
                        cursor.execute(
                            'DELETE FROM transactions WHERE id = ? AND user_id = ?',
                            (tx_id_int, user_id),
                        )
                    else:
                        cursor.execute(
                            "DELETE FROM transactions WHERE id = ? AND (user_id IS NULL OR user_id = '')",
                            (tx_id_int,),
                        )

            if cash_asset_id is not None and cash_before_amount is not None:
                try:
                    cash_asset_id_int = int(cash_asset_id)
                    cash_before = float(cash_before_amount)
                except (TypeError, ValueError):
                    return {'ok': False, 'code': 'INVALID_CASH_RESTORE', 'error': 'Invalid cash restore payload'}
                if user_id:
                    cursor.execute(
                        '''
                        UPDATE cash_assets
                        SET amount = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ? AND user_id = ?
                        ''',
                        (cash_before, cash_asset_id_int, user_id),
                    )
                else:
                    cursor.execute(
                        '''
                        UPDATE cash_assets
                        SET amount = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ? AND (user_id IS NULL OR user_id = '')
                        ''',
                        (cash_before, cash_asset_id_int),
                    )
                if cursor.rowcount <= 0:
                    return {'ok': False, 'code': 'CASH_ASSET_NOT_FOUND', 'error': 'Cash account not found'}

            conn.commit()
            return {'ok': True}
        except Exception as e:
            logger.error(f"Failed to undo invest operation: {e}")
            conn.rollback()
            return {'ok': False, 'code': 'UNDO_FAILED', 'error': 'Failed to undo operation'}
        finally:
            conn.close()
    
    def get_transactions(self, limit: int = 100, user_id: str = None) -> List[Dict[str, Any]]:
        """获取交易记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute('''
                SELECT time, code, name, type, price, qty, amount, pnl
                FROM transactions
                WHERE user_id = ?
                ORDER BY time DESC
                LIMIT ?
            ''', (user_id, limit))
        else:
            cursor.execute('''
                SELECT time, code, name, type, price, qty, amount, pnl
                FROM transactions
                WHERE user_id IS NULL OR user_id = ''
                ORDER BY time DESC
                LIMIT ?
            ''', (limit,))
        
        data = []
        for row in cursor.fetchall():
            data.append({
                'time': row['time'],
                'code': row['code'],
                'name': row['name'],
                'type': row['type'],
                'price': float(row['price']),
                'qty': float(row['qty']),
                'amount': float(row['amount']),
                'pnl': float(row['pnl'])
            })
        
        conn.close()
        return data
    
    def backup_from_csv(self, csv_path: str) -> bool:
        """从CSV备份数据导入数据库"""
        try:
            import pandas as pd
            
            df = pd.read_csv(csv_path)
            conn = self.get_connection()
            cursor = conn.cursor()
            
            for _, row in df.iterrows():
                code = row['code']
                name = row['name']
                qty = row['qty']
                price = row['price']
                curr = row.get('curr', 'CNY')
                adjustment = row.get('adjustment', 0.0)
                
                cursor.execute('''
                    INSERT OR REPLACE INTO portfolio (code, name, qty, price, curr, adjustment)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (code, name, qty, price, curr, adjustment))
            
            conn.commit()
            conn.close()
            logger.info(f"Backup imported from CSV: {csv_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to backup from CSV: {e}")
            return False
    
    def get_cash_assets(self, user_id: str = None) -> List[Dict[str, Any]]:
        """获取所有现金资产"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute('''
                SELECT id, name, amount, curr
                FROM cash_assets
                WHERE user_id = ?
                ORDER BY id
            ''', (user_id,))
        else:
            cursor.execute('''
                SELECT id, name, amount, curr
                FROM cash_assets
                WHERE user_id IS NULL OR user_id = ''
                ORDER BY id
            ''')
        
        data = []
        for row in cursor.fetchall():
            data.append({
                'id': row['id'],
                'name': row['name'],
                'amount': float(row['amount']),
                'curr': row['curr']
            })
        
        conn.close()
        return data

    def get_cash_asset_by_id(self, asset_id: int, user_id: str = None) -> Optional[Dict[str, Any]]:
        """按 ID 获取现金资产"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if user_id:
                cursor.execute(
                    '''
                    SELECT id, name, amount, curr
                    FROM cash_assets
                    WHERE id = ? AND user_id = ?
                    LIMIT 1
                    ''',
                    (asset_id, user_id),
                )
            else:
                cursor.execute(
                    '''
                    SELECT id, name, amount, curr
                    FROM cash_assets
                    WHERE id = ? AND (user_id IS NULL OR user_id = '')
                    LIMIT 1
                    ''',
                    (asset_id,),
                )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                'id': int(row['id']),
                'name': row['name'],
                'amount': float(row['amount']),
                'curr': row['curr'],
            }
        finally:
            conn.close()
    
    def add_cash_asset(self, name: str, amount: float, curr: str = 'CNY', user_id: str = None) -> bool:
        """添加现金资产"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            try:
                cursor.execute('''
                    INSERT INTO cash_assets (name, amount, curr, user_id)
                    VALUES (?, ?, ?, ?)
                ''', (name, amount, curr, user_id))
            except sqlite3.OperationalError as e:
                # 兼容旧库列缺失：回退到最小列写入
                logger.warning(f"cash_assets insert fallback due to schema mismatch: {e}")
                cursor.execute('''
                    INSERT INTO cash_assets (name, amount)
                    VALUES (?, ?)
                ''', (name, amount))
            
            conn.commit()
            logger.info(f"Cash asset added: {name}, amount={amount}")
            return True
        except Exception as e:
            logger.error(f"Failed to add cash asset: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def delete_cash_asset(self, asset_id: int, user_id: str = None) -> bool:
        """删除现金资产"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if user_id:
                cursor.execute('DELETE FROM cash_assets WHERE id = ? AND user_id = ?', (asset_id, user_id))
            else:
                cursor.execute('DELETE FROM cash_assets WHERE id = ? AND (user_id IS NULL OR user_id = "")', (asset_id,))
            conn.commit()
            logger.info(f"Cash asset deleted: {asset_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete cash asset: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_other_assets(self, user_id: str = None) -> List[Dict[str, Any]]:
        """获取所有其他资产"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute('''
                SELECT id, name, amount, curr
                FROM other_assets
                WHERE user_id = ?
                ORDER BY id
            ''', (user_id,))
        else:
            cursor.execute('''
                SELECT id, name, amount, curr
                FROM other_assets
                WHERE user_id IS NULL OR user_id = ''
                ORDER BY id
            ''')
        
        data = []
        for row in cursor.fetchall():
            data.append({
                'id': row['id'],
                'name': row['name'],
                'amount': float(row['amount']),
                'curr': row['curr']
            })
        
        conn.close()
        return data
    
    def add_other_asset(self, name: str, amount: float, curr: str = 'CNY', user_id: str = None) -> bool:
        """添加其他资产"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            try:
                cursor.execute('''
                    INSERT INTO other_assets (name, amount, curr, user_id)
                    VALUES (?, ?, ?, ?)
                ''', (name, amount, curr, user_id))
            except sqlite3.OperationalError as e:
                logger.warning(f"other_assets insert fallback due to schema mismatch: {e}")
                cursor.execute('''
                    INSERT INTO other_assets (name, amount)
                    VALUES (?, ?)
                ''', (name, amount))
            
            conn.commit()
            logger.info(f"Other asset added: {name}, amount={amount}")
            return True
        except Exception as e:
            logger.error(f"Failed to add other asset: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def delete_other_asset(self, asset_id: int, user_id: str = None) -> bool:
        """删除其他资产"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if user_id:
                cursor.execute('DELETE FROM other_assets WHERE id = ? AND user_id = ?', (asset_id, user_id))
            else:
                cursor.execute('DELETE FROM other_assets WHERE id = ? AND (user_id IS NULL OR user_id = "")', (asset_id,))
            conn.commit()
            logger.info(f"Other asset deleted: {asset_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete other asset: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def update_cash_asset(self, asset_id: int, name: str, amount: float, curr: str = 'CNY', user_id: str = None) -> bool:
        """更新现金资产"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            try:
                if user_id:
                    cursor.execute('''
                        UPDATE cash_assets SET name = ?, amount = ?, curr = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ? AND user_id = ?
                    ''', (name, amount, curr, asset_id, user_id))
                else:
                    cursor.execute('''
                        UPDATE cash_assets SET name = ?, amount = ?, curr = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ? AND (user_id IS NULL OR user_id = '')
                    ''', (name, amount, curr, asset_id))
            except sqlite3.OperationalError as e:
                logger.warning(f"cash_assets update fallback due to schema mismatch: {e}")
                cursor.execute('''
                    UPDATE cash_assets SET name = ?, amount = ?
                    WHERE id = ?
                ''', (name, amount, asset_id))
            
            conn.commit()
            logger.info(f"Cash asset updated: {asset_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update cash asset: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def update_other_asset(self, asset_id: int, name: str, amount: float, curr: str = 'CNY', user_id: str = None) -> bool:
        """更新其他资产"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            try:
                if user_id:
                    cursor.execute('''
                        UPDATE other_assets SET name = ?, amount = ?, curr = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ? AND user_id = ?
                    ''', (name, amount, curr, asset_id, user_id))
                else:
                    cursor.execute('''
                        UPDATE other_assets SET name = ?, amount = ?, curr = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ? AND (user_id IS NULL OR user_id = '')
                    ''', (name, amount, curr, asset_id))
            except sqlite3.OperationalError as e:
                logger.warning(f"other_assets update fallback due to schema mismatch: {e}")
                cursor.execute('''
                    UPDATE other_assets SET name = ?, amount = ?
                    WHERE id = ?
                ''', (name, amount, asset_id))
            
            conn.commit()
            logger.info(f"Other asset updated: {asset_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update other asset: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_liabilities(self, user_id: str = None) -> List[Dict[str, Any]]:
        """获取所有负债"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute('''
                SELECT id, name, amount, curr
                FROM liabilities
                WHERE user_id = ?
                ORDER BY id
            ''', (user_id,))
        else:
            cursor.execute('''
                SELECT id, name, amount, curr
                FROM liabilities
                WHERE user_id IS NULL OR user_id = ''
                ORDER BY id
            ''')
        
        data = []
        for row in cursor.fetchall():
            data.append({
                'id': row['id'],
                'name': row['name'],
                'amount': float(row['amount']),
                'curr': row['curr']
            })
        
        conn.close()
        return data
    
    def add_liability(self, name: str, amount: float, curr: str = 'CNY', user_id: str = None) -> bool:
        """添加负债"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            try:
                cursor.execute('''
                    INSERT INTO liabilities (name, amount, curr, user_id)
                    VALUES (?, ?, ?, ?)
                ''', (name, amount, curr, user_id))
            except sqlite3.OperationalError as e:
                logger.warning(f"liabilities insert fallback due to schema mismatch: {e}")
                cursor.execute('''
                    INSERT INTO liabilities (name, amount)
                    VALUES (?, ?)
                ''', (name, amount))
            
            conn.commit()
            logger.info(f"Liability added: {name}, amount={amount}")
            return True
        except Exception as e:
            logger.error(f"Failed to add liability: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def delete_liability(self, liability_id: int, user_id: str = None) -> bool:
        """删除负债"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if user_id:
                cursor.execute('DELETE FROM liabilities WHERE id = ? AND user_id = ?', (liability_id, user_id))
            else:
                cursor.execute('DELETE FROM liabilities WHERE id = ? AND (user_id IS NULL OR user_id = "")', (liability_id,))
            conn.commit()
            logger.info(f"Liability deleted: {liability_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete liability: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def update_liability(self, liability_id: int, name: str, amount: float, curr: str = 'CNY', user_id: str = None) -> bool:
        """更新负债"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            try:
                if user_id:
                    cursor.execute('''
                        UPDATE liabilities SET name = ?, amount = ?, curr = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ? AND user_id = ?
                    ''', (name, amount, curr, liability_id, user_id))
                else:
                    cursor.execute('''
                        UPDATE liabilities SET name = ?, amount = ?, curr = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ? AND (user_id IS NULL OR user_id = '')
                    ''', (name, amount, curr, liability_id))
            except sqlite3.OperationalError as e:
                logger.warning(f"liabilities update fallback due to schema mismatch: {e}")
                cursor.execute('''
                    UPDATE liabilities SET name = ?, amount = ?
                    WHERE id = ?
                ''', (name, amount, liability_id))
            
            conn.commit()
            logger.info(f"Liability updated: {liability_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update liability: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    def get_today_realized_pnl(self, user_id: str = None) -> float:
        """获取今日已实现盈亏（卖出产生的盈亏）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')

        user_condition = "AND user_id = ?" if user_id else "AND (user_id IS NULL OR user_id = '')"
        user_param = (user_id,) if user_id else ()

        try:
            cursor.execute('''
                SELECT SUM(pnl)
                FROM transactions
                WHERE type = '减仓' AND time LIKE ?
            ''' + f" {user_condition}", (f'{today}%',) + user_param)
            result = cursor.fetchone()[0]
            return float(result) if result else 0.0
        except Exception as e:
            logger.error(f"Failed to get realized pnl: {e}")
            return 0.0
        finally:
            conn.close()

    def get_realized_pnl_by_date(self, date_str: str, user_id: str = None) -> Dict[str, float]:
        """获取指定日期按市场聚合的已实现盈亏（减仓 pnl）。"""
        result = {k: 0.0 for k in DEFAULT_MARKETS}
        conn = self.get_connection()
        cursor = conn.cursor()
        user_condition = "AND user_id = ?" if user_id else "AND (user_id IS NULL OR user_id = '')"
        user_param = (user_id,) if user_id else ()

        try:
            cursor.execute(
                '''
                SELECT code, pnl
                FROM transactions
                WHERE type = '减仓' AND time LIKE ?
                '''
                + f" {user_condition}",
                (f'{date_str}%',) + user_param,
            )
            for row in cursor.fetchall():
                raw_code = str(row['code'] or '')
                normalized = parse_code(raw_code, "").get("code") or raw_code
                code = str(normalized or raw_code)
                market = str(market_from_asset(code) or 'a').lower()
                if market not in result:
                    market = 'a'
                result[market] += float(row['pnl'] or 0.0)
            return result
        except Exception as e:
            logger.error(f"Failed to get realized pnl by date=%s: %s", date_str, e)
            return result
        finally:
            conn.close()


    def save_daily_snapshot_market_breakdown(
        self,
        date_str: str,
        day_pnl_by_market: Dict[str, float],
        total_day_pnl: float,
        user_id: str = None,
        source: str = 'exact',
        confidence: float = 1.0,
        meta_by_market: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        保存每日分市场收益快照（按 date + user_id + market upsert）。
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        uid = user_id or ''

        try:
            normalized = {k: 0.0 for k in MARKET_BREAKDOWN_MARKETS}
            for market in ('a', 'hk', 'us', 'fund'):
                normalized[market] = float((day_pnl_by_market or {}).get(market, 0.0) or 0.0)
            explicit_unallocated = (day_pnl_by_market or {}).get('unallocated')
            if explicit_unallocated is None:
                allocated = sum(normalized[m] for m in ('a', 'hk', 'us', 'fund'))
                normalized['unallocated'] = float(total_day_pnl or 0.0) - allocated
            else:
                normalized['unallocated'] = float(explicit_unallocated or 0.0)

            market_meta = meta_by_market or {}
            for market in MARKET_BREAKDOWN_MARKETS:
                payload = market_meta.get(market)
                meta_json = None
                if payload is not None:
                    try:
                        meta_json = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
                    except Exception:
                        meta_json = json.dumps({'raw': str(payload)}, ensure_ascii=False, separators=(',', ':'))
                cursor.execute(
                    '''
                    INSERT INTO daily_snapshot_market_breakdowns
                    (date, user_id, market, day_pnl, source, confidence, meta_json, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(date, user_id, market) DO UPDATE SET
                        day_pnl = excluded.day_pnl,
                        source = excluded.source,
                        confidence = excluded.confidence,
                        meta_json = excluded.meta_json,
                        updated_at = CURRENT_TIMESTAMP
                    ''',
                    (
                        str(date_str),
                        uid,
                        market,
                        round(float(normalized[market]), 2),
                        str(source or 'exact'),
                        float(confidence),
                        meta_json,
                    ),
                )
            conn.commit()
            return True
        except Exception as e:
            logger.error(
                "Failed to save market breakdown date=%s user_id=%s: %s",
                date_str,
                uid,
                e,
            )
            conn.rollback()
            return False
        finally:
            conn.close()


    def save_daily_snapshot(self, data: Dict[str, float], user_id: str = None) -> bool:
        """保存每日资产快照（按 date + user_id upsert）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        uid = user_id or ''
        
        try:
            cursor.execute('''
                INSERT INTO daily_snapshots (
                    date, total_asset, total_invest, total_cash,
                    total_other, total_liability, total_pnl, day_pnl, user_id, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(date, user_id) DO UPDATE SET
                    total_asset = excluded.total_asset,
                    total_invest = excluded.total_invest,
                    total_cash = excluded.total_cash,
                    total_other = excluded.total_other,
                    total_liability = excluded.total_liability,
                    total_pnl = excluded.total_pnl,
                    day_pnl = excluded.day_pnl,
                    updated_at = CURRENT_TIMESTAMP
            ''', (
                today,
                data.get('total_asset', 0),
                data.get('total_invest', 0),
                data.get('total_cash', 0),
                data.get('total_other', 0),
                data.get('total_liability', 0),
                data.get('total_pnl', 0),
                data.get('day_pnl', 0),
                uid
            ))
            
            conn.commit()
            logger.info(f"Daily snapshot saved for {today}")
            return True
        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
            
    def get_history(self, limit: int = 365, user_id: str = None) -> List[Dict[str, Any]]:
        """获取历史资产数据"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if user_id:
                cursor.execute('''
                    SELECT * FROM daily_snapshots 
                    WHERE user_id = ?
                    ORDER BY date ASC 
                    LIMIT ?
                ''', (user_id, limit))
            else:
                cursor.execute('''
                    SELECT * FROM daily_snapshots 
                    WHERE user_id IS NULL OR user_id = ''
                    ORDER BY date ASC 
                    LIMIT ?
                ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def _sync_version_from_parts(self, domain: str, *parts: str) -> str:
        raw = f"{domain}|" + "|".join(str(p or "") for p in parts)
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]

    def get_sync_versions(self, user_id: str = None) -> Dict[str, str]:
        """
        计算客户端增量同步版本号（按用户维度）。

        版本规则：
        - portfolio/cash_assets/other_assets/liabilities: max(updated_at)+count+user_id
        - history: max(date)+count+user_id
        - overview_all: max(daily_snapshots.updated_at)+count+user_id
        """
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        uid = str(user_id or "")
        user_condition = "user_id = ?" if user_id else "(user_id IS NULL OR user_id = '')"
        user_param = (user_id,) if user_id else ()

        def _table_version(table: str) -> str:
            cursor.execute(
                f"""
                SELECT COALESCE(MAX(updated_at), '') AS max_updated, COUNT(*) AS cnt
                FROM {table}
                WHERE {user_condition}
                """,
                user_param,
            )
            row = cursor.fetchone() or {}
            max_updated = str((row["max_updated"] if isinstance(row, sqlite3.Row) else "") or "")
            cnt = str((row["cnt"] if isinstance(row, sqlite3.Row) else 0) or 0)
            return self._sync_version_from_parts(table, max_updated, cnt, uid)

        try:
            versions: Dict[str, str] = {
                "portfolio": _table_version("portfolio"),
                "cash_assets": _table_version("cash_assets"),
                "other_assets": _table_version("other_assets"),
                "liabilities": _table_version("liabilities"),
            }

            cursor.execute(
                f"""
                SELECT COALESCE(MAX(date), '') AS max_date, COUNT(*) AS cnt
                FROM daily_snapshots
                WHERE {user_condition}
                """,
                user_param,
            )
            history_row = cursor.fetchone() or {}
            max_date = str((history_row["max_date"] if isinstance(history_row, sqlite3.Row) else "") or "")
            history_cnt = str((history_row["cnt"] if isinstance(history_row, sqlite3.Row) else 0) or 0)
            versions["history"] = self._sync_version_from_parts("history", max_date, history_cnt, uid)

            cursor.execute(
                f"""
                SELECT COALESCE(MAX(updated_at), '') AS max_updated, COUNT(*) AS cnt
                FROM daily_snapshots
                WHERE {user_condition}
                """,
                user_param,
            )
            overview_row = cursor.fetchone() or {}
            overview_updated = str((overview_row["max_updated"] if isinstance(overview_row, sqlite3.Row) else "") or "")
            overview_cnt = str((overview_row["cnt"] if isinstance(overview_row, sqlite3.Row) else 0) or 0)
            versions["overview_all"] = self._sync_version_from_parts(
                "overview_all",
                overview_updated,
                overview_cnt,
                uid,
            )
            return versions
        finally:
            conn.close()

    # ============================================================
    # 分析数据查询
    # ============================================================
    
    def get_pnl_overview(self, period: str = 'day', user_id: str = None) -> Dict[str, Any]:
        """
        获取盈亏概览数据

        Args:
            period: day|month|year|all
            user_id: 用户ID

        Returns:
            {pnl: float, pnl_rate: float, base_value: float}
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # 构建 user_id 条件
        user_condition = "user_id = ?" if user_id else "(user_id IS NULL OR user_id = '')"
        user_param = (user_id,) if user_id else ()

        try:
            today = datetime.now()
            today_str = today.strftime('%Y-%m-%d')

            def _fetch_prev_snapshot(date_str: str):
                cursor.execute(
                    f'''
                    SELECT date, total_pnl, total_invest FROM daily_snapshots
                    WHERE date < ? AND {user_condition}
                    ORDER BY date DESC
                    LIMIT 1
                    ''',
                    (date_str,) + user_param,
                )
                return cursor.fetchone()

            def _fetch_last_snapshot(date_str: str):
                cursor.execute(
                    f'''
                    SELECT date, total_pnl, total_invest FROM daily_snapshots
                    WHERE date <= ? AND {user_condition}
                    ORDER BY date DESC
                    LIMIT 1
                    ''',
                    (date_str,) + user_param,
                )
                return cursor.fetchone()

            if period == 'day':
                cursor.execute(
                    f'''
                    SELECT date, total_pnl, total_invest FROM daily_snapshots
                    WHERE date = ? AND {user_condition}
                    LIMIT 1
                    ''',
                    (today_str,) + user_param,
                )
                row = cursor.fetchone()
                if row:
                    today_total = float(row['total_pnl']) if row['total_pnl'] else 0
                    base = float(row['total_invest']) if row['total_invest'] else 1
                    cursor.execute(
                        f'''
                        SELECT total_pnl FROM daily_snapshots
                        WHERE date < ? AND {user_condition}
                        ORDER BY date DESC
                        LIMIT 1
                        ''',
                        (today_str,) + user_param,
                    )
                    prev = cursor.fetchone()
                    if not prev:
                        return {'pnl': 0, 'pnl_rate': 0, 'base_value': base}
                    prev_total = float(prev['total_pnl']) if prev['total_pnl'] else 0
                    # 修正：收益率分母应使用期初本金（prev_invest），避免当日加仓稀释收益率
                    # 如果期初本金为0（新用户首日），则兜底使用当日期末本金
                    prev_invest = float(prev['total_invest']) if prev['total_invest'] else 0
                    calc_base = prev_invest if prev_invest > 0 else base
                    
                    pnl = today_total - prev_total
                    return {
                        'pnl': pnl,
                        'pnl_rate': round(pnl / calc_base * 100, 2) if calc_base else 0,
                        'base_value': base,
                    }
                return {'pnl': 0, 'pnl_rate': 0, 'base_value': 0}

            elif period == 'month':
                month_start = today.strftime('%Y-%m-01')
                cursor.execute(
                    f'''
                    SELECT date, total_pnl, day_pnl, total_invest FROM daily_snapshots
                    WHERE date >= ? AND date <= ? AND {user_condition}
                    ORDER BY date ASC
                    ''',
                    (month_start, today_str) + user_param,
                )
                rows = cursor.fetchall()
                business_rows = [
                    row for row in rows if not _is_weekend_date(str(row['date']))
                ]
                prev = _fetch_prev_snapshot(month_start)
                if business_rows:
                    last = business_rows[-1]
                    if prev:
                        base_total = float(prev['total_pnl'] or 0)
                        base_invest = float(prev['total_invest'] or 0)
                    else:
                        # 修正: 无期初快照时，基准总盈亏应为本月第一天的(总盈亏 - 当日盈亏)
                        first_day = business_rows[0]
                        base_total = float(first_day['total_pnl'] or 0) - float(first_day['day_pnl'] or 0)
                        base_invest = float(first_day['total_invest'] or 0)
                else:
                    last = prev
                    base_total = float(prev['total_pnl'] or 0) if prev else 0.0
                    base_invest = float(prev['total_invest'] or 0) if prev else 0.0
                if last:
                    pnl = float(last['total_pnl'] or 0) - base_total
                    base = base_invest or float(last['total_invest'] or 0) or 1
                    # 修正：收益率分母优先使用期初本金
                    calc_base = base_invest if base_invest > 0 else base
                    return {
                        'pnl': pnl,
                        'pnl_rate': round(pnl / calc_base * 100, 2) if calc_base else 0,
                        'base_value': base,
                    }
                return {'pnl': 0, 'pnl_rate': 0, 'base_value': 0}

            elif period == 'year':
                year_start = today.strftime('%Y-01-01')
                cursor.execute(
                    f'''
                    SELECT date, total_pnl, day_pnl, total_invest FROM daily_snapshots
                    WHERE date >= ? AND date <= ? AND {user_condition}
                    ORDER BY date ASC
                    ''',
                    (year_start, today_str) + user_param,
                )
                rows = cursor.fetchall()
                business_rows = [
                    row for row in rows if not _is_weekend_date(str(row['date']))
                ]
                prev = _fetch_prev_snapshot(year_start)
                if business_rows:
                    last = business_rows[-1]
                    if prev:
                        base_total = float(prev['total_pnl'] or 0)
                        base_invest = float(prev['total_invest'] or 0)
                    else:
                        # 修正: 无期初快照时，基准总盈亏应为今年第一天的(总盈亏 - 当日盈亏)
                        first_day = business_rows[0]
                        base_total = float(first_day['total_pnl'] or 0) - float(first_day['day_pnl'] or 0)
                        base_invest = float(first_day['total_invest'] or 0)
                else:
                    last = prev
                    base_total = float(prev['total_pnl'] or 0) if prev else 0.0
                    base_invest = float(prev['total_invest'] or 0) if prev else 0.0
                if last:
                    pnl = float(last['total_pnl'] or 0) - base_total
                    base = base_invest or float(last['total_invest'] or 0) or 1
                    # 修正：收益率分母优先使用期初本金
                    calc_base = base_invest if base_invest > 0 else base
                    return {
                        'pnl': pnl,
                        'pnl_rate': round(pnl / calc_base * 100, 2) if calc_base else 0,
                        'base_value': base,
                    }
                return {'pnl': 0, 'pnl_rate': 0, 'base_value': 0}

            else:  # all
                cursor.execute(
                    f'''
                    SELECT date, total_pnl, total_invest FROM daily_snapshots
                    WHERE date <= ? AND {user_condition}
                    ORDER BY date ASC
                    ''',
                    (today_str,) + user_param,
                )
                rows = cursor.fetchall()
                if rows:
                    last = rows[-1]
                    # total_pnl 本身就是累计口径；all 应返回当前累计值而非差值。
                    pnl = float(last['total_pnl'] or 0.0)
                    latest_invest = float(last['total_invest'] or 0.0)
                    first_invest = float(rows[0]['total_invest'] or 0.0)
                    base = latest_invest or first_invest or 1
                    return {
                        'pnl': pnl,
                        'pnl_rate': round(pnl / base * 100, 2) if base else 0,
                        'base_value': base,
                    }
                return {'pnl': 0, 'pnl_rate': 0, 'base_value': 0}

        except Exception as e:
            logger.error(f"Failed to get pnl overview: {e}")
            return {'pnl': 0, 'pnl_rate': 0, 'base_value': 0}
        finally:
            conn.close()
    
    def get_calendar_data(
        self,
        time_type: str = 'day',
        user_id: str = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        获取收益日历数据

        Args:
            time_type: day|month|year
            user_id: 用户ID
            year: 可选年份（day/month 视图使用）
            month: 可选月份（day 视图使用）

        Returns:
            {
                items: [{label, pnl}],
                total_pnl: float,
                total_rate: float,
                title: str,
                period: {time_type, year?, month?},
                selectable: {day: {years, months_by_year}, month: {years}}
            }
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        user_condition = "user_id = ?" if user_id else "(user_id IS NULL OR user_id = '')"
        user_param = (user_id,) if user_id else ()

        try:
            now = datetime.now()
            today_str = now.strftime('%Y-%m-%d')
            items = []
            total_pnl = 0.0

            cursor.execute(
                f'''
                SELECT date
                FROM daily_snapshots
                WHERE {user_condition}
                ORDER BY date ASC
                ''',
                user_param,
            )
            all_dates = [str(row['date']) for row in cursor.fetchall() if row['date']]
            months_by_year: Dict[int, set] = {}
            for date_str in all_dates:
                parts = date_str.split('-')
                if len(parts) != 3:
                    continue
                y = int(parts[0])
                m = int(parts[1])
                months_by_year.setdefault(y, set()).add(m)

            selectable_years = sorted(months_by_year.keys())
            selectable_months_by_year = {
                str(y): sorted(list(months_by_year[y]))
                for y in selectable_years
            }
            selectable = {
                'day': {
                    'years': selectable_years,
                    'months_by_year': selectable_months_by_year,
                },
                'month': {
                    'years': selectable_years,
                },
            }

            latest_year = selectable_years[-1] if selectable_years else None
            latest_month = (
                max(months_by_year[latest_year])
                if latest_year is not None and months_by_year.get(latest_year)
                else None
            )

            period: Dict[str, Any] = {'time_type': time_type}

            if time_type == 'day':
                if not selectable_years:
                    period.update({'year': now.year, 'month': now.month})
                    return {
                        'items': [],
                        'total_pnl': 0.0,
                        'total_rate': 0.0,
                        'title': f'{now.year}年{now.month}月累计',
                        'period': period,
                        'selectable': selectable,
                    }

                target_year = year
                target_month = month
                if target_year is None and target_month is None:
                    if now.year in months_by_year and now.month in months_by_year[now.year]:
                        target_year = now.year
                        target_month = now.month
                    else:
                        target_year = latest_year
                        target_month = latest_month
                else:
                    if target_year is None:
                        target_year = now.year
                    if target_month is None:
                        target_month = now.month

                assert target_year is not None
                assert target_month is not None
                period.update({'year': int(target_year), 'month': int(target_month)})

                if (
                    target_year not in months_by_year
                    or target_month not in months_by_year[target_year]
                ):
                    return {
                        'error': 'Selected period has no snapshot data',
                        'code': 'INVALID_CALENDAR_PERIOD',
                        'items': [],
                        'total_pnl': 0.0,
                        'total_rate': 0.0,
                        'title': f'{target_year}年{target_month}月累计',
                        'period': period,
                        'selectable': selectable,
                    }

                month_start = f'{target_year:04d}-{target_month:02d}-01'
                if target_month == 12:
                    next_month = dt.datetime(target_year + 1, 1, 1)
                else:
                    next_month = dt.datetime(target_year, target_month + 1, 1)
                month_end = (next_month - timedelta(days=1)).strftime('%Y-%m-%d')
                if target_year == now.year and target_month == now.month:
                    month_end = min(month_end, today_str)

                cursor.execute(
                    f'''
                    SELECT date, day_pnl, total_pnl, updated_at
                    FROM daily_snapshots
                    WHERE date >= ? AND date <= ? AND {user_condition}
                    ORDER BY date ASC
                    ''',
                    (month_start, month_end) + user_param,
                )
                rows = cursor.fetchall()
                
                # 使用首尾差值计算当月总盈亏，对齐 get_pnl_overview 逻辑
                business_rows = [r for r in rows if not _is_weekend_date(str(r['date']))]
                true_total_pnl = 0.0
                if business_rows:
                    first_day = business_rows[0]
                    last_day = business_rows[-1]
                    cursor.execute(
                        f'''
                        SELECT date, total_pnl, total_invest FROM daily_snapshots
                        WHERE date < ? AND {user_condition}
                        ORDER BY date DESC
                        LIMIT 1
                        ''',
                        (month_start,) + user_param,
                    )
                    prev_month_snap = cursor.fetchone()
                    if prev_month_snap:
                        base_total = float(prev_month_snap['total_pnl'] or 0)
                    else:
                        base_total = float(first_day['total_pnl'] or 0) - float(first_day['day_pnl'] or 0)
                    true_total_pnl = float(last_day['total_pnl'] or 0) - base_total
                total_pnl = true_total_pnl

                prev_total = None
                for row in rows:
                    date_str = row['date']
                    day = int(str(date_str).split('-')[2])
                    is_market_closed = _is_market_closed_date(date_str)
                    closed_at_snapshot = False
                    if _is_snapshot_updated_on_same_date(date_str, row['updated_at']):
                        closed_at_snapshot = _is_market_closed_at_snapshot_time(
                            row['updated_at']
                        )
                    pnl = float(row['day_pnl']) if row['day_pnl'] is not None else 0.0
                    if is_market_closed:
                        pnl = 0.0
                    elif (
                        (pnl == 0 or pnl == -0.0)
                        and (not closed_at_snapshot)
                        and row['total_pnl'] is not None
                        and prev_total is not None
                    ):
                        pnl = float(row['total_pnl']) - prev_total
                    if (not is_market_closed) and row['total_pnl'] is not None:
                        prev_total = float(row['total_pnl'])
                    items.append({'label': str(day), 'pnl': pnl})

                title = f'{target_year}年{target_month}月累计'

            elif time_type == 'month':
                if not selectable_years:
                    period.update({'year': now.year})
                    return {
                        'items': [],
                        'total_pnl': 0.0,
                        'total_rate': 0.0,
                        'title': f'{now.year}年累计',
                        'period': period,
                        'selectable': selectable,
                    }

                target_year = year
                if target_year is None:
                    target_year = now.year if now.year in months_by_year else latest_year

                assert target_year is not None
                period.update({'year': int(target_year)})

                if target_year not in months_by_year:
                    return {
                        'error': 'Selected period has no snapshot data',
                        'code': 'INVALID_CALENDAR_PERIOD',
                        'items': [],
                        'total_pnl': 0.0,
                        'total_rate': 0.0,
                        'title': f'{target_year}年累计',
                        'period': period,
                        'selectable': selectable,
                    }

                year_start = f'{target_year:04d}-01-01'
                year_end = today_str if target_year == now.year else f'{target_year:04d}-12-31'
                cursor.execute(
                    f'''
                    SELECT date, total_pnl
                    FROM daily_snapshots
                    WHERE date >= ? AND date <= ? AND {user_condition}
                    ORDER BY date ASC
                    ''',
                    (year_start, year_end) + user_param,
                )

                month_last: Dict[int, float] = {}
                for row in cursor.fetchall():
                    date_str = row['date']
                    if _is_market_closed_date(date_str):
                        continue
                    m = int(str(date_str).split('-')[1])
                    tp = float(row['total_pnl']) if row['total_pnl'] is not None else 0.0
                    month_last[m] = tp

                cursor.execute(
                    f'''
                    SELECT total_pnl
                    FROM daily_snapshots
                    WHERE date < ? AND {user_condition}
                    ORDER BY date DESC
                    LIMIT 1
                    ''',
                    (year_start,) + user_param,
                )
                base_row = cursor.fetchone()
                if base_row and base_row['total_pnl'] is not None:
                    prev_total = float(base_row['total_pnl'])
                else:
                    cursor.execute(
                        f'''
                        SELECT date, total_pnl, day_pnl
                        FROM daily_snapshots
                        WHERE date >= ? AND date <= ? AND {user_condition}
                        ORDER BY date ASC
                        LIMIT 1
                        ''',
                        (year_start, year_end) + user_param,
                    )
                    first_row = cursor.fetchone()
                    if first_row and first_row['total_pnl'] is not None:
                        prev_total = float(first_row['total_pnl']) - float(first_row['day_pnl'] or 0.0)
                    else:
                        prev_total = 0.0
                month_limit = now.month if target_year == now.year else 12

                for m in range(1, month_limit + 1):
                    current_total = month_last.get(m, prev_total)
                    pnl = current_total - prev_total
                    items.append({'label': f'{m}月', 'pnl': pnl})
                    total_pnl += pnl
                    prev_total = current_total

                title = f'{target_year}年累计'

            elif time_type == 'year':
                period = {'time_type': 'year'}
                cursor.execute(
                    f'''
                    SELECT date, total_pnl
                    FROM daily_snapshots
                    WHERE date <= ? AND {user_condition}
                    ORDER BY date ASC
                    ''',
                    (today_str,) + user_param,
                )

                rows = cursor.fetchall()
                if rows:
                    year_last: Dict[int, float] = {}
                    for row in rows:
                        date_str = row['date']
                        if _is_market_closed_date(date_str):
                            continue
                        y = int(str(date_str).split('-')[0])
                        tp = float(row['total_pnl']) if row['total_pnl'] is not None else 0.0
                        year_last[y] = tp

                    start_year = int(str(rows[0]['date']).split('-')[0])
                    base_date = f'{start_year}-01-01'
                    cursor.execute(
                        f'''
                        SELECT total_pnl
                        FROM daily_snapshots
                        WHERE date < ? AND {user_condition}
                        ORDER BY date DESC
                        LIMIT 1
                        ''',
                        (base_date,) + user_param,
                    )
                    base_row = cursor.fetchone()
                    if base_row and base_row['total_pnl'] is not None:
                        prev_total = float(base_row['total_pnl'])
                    else:
                        cursor.execute(
                            f'''
                            SELECT date, total_pnl, day_pnl
                            FROM daily_snapshots
                            WHERE date >= ? AND date <= ? AND {user_condition}
                            ORDER BY date ASC
                            LIMIT 1
                            ''',
                            (base_date, today_str) + user_param,
                        )
                        first_row = cursor.fetchone()
                        if first_row and first_row['total_pnl'] is not None:
                            prev_total = float(first_row['total_pnl']) - float(first_row['day_pnl'] or 0.0)
                        else:
                            prev_total = 0.0
                    for y in range(start_year, now.year + 1):
                        current_total = year_last.get(y, prev_total)
                        pnl = current_total - prev_total
                        items.append({'label': str(y), 'pnl': pnl})
                        prev_total = current_total
                    
                    total_pnl = current_total if 'current_total' in locals() else prev_total

                title = '总累计'
            else:
                return {
                    'error': 'Invalid time type',
                    'code': 'INVALID_CALENDAR_PERIOD',
                    'items': [],
                    'total_pnl': 0.0,
                    'total_rate': 0.0,
                    'title': '',
                    'period': period,
                    'selectable': selectable,
                }

            cursor.execute(
                f'''
                SELECT total_invest
                FROM daily_snapshots
                WHERE {user_condition}
                ORDER BY date ASC
                LIMIT 1
                ''',
                user_param,
            )
            row = cursor.fetchone()
            base = float(row['total_invest']) if row and row['total_invest'] else 0.0
            total_rate = round(total_pnl / base * 100, 2) if base else 0.0

            return {
                'items': items,
                'total_pnl': total_pnl,
                'total_rate': total_rate,
                'title': title,
                'period': period,
                'selectable': selectable,
            }

        except Exception as e:
            logger.error(f"Failed to get calendar data: {e}")
            return {
                'items': [],
                'total_pnl': 0.0,
                'total_rate': 0.0,
                'title': '',
                'period': {'time_type': time_type},
                'selectable': {'day': {'years': [], 'months_by_year': {}}, 'month': {'years': []}},
            }
        finally:
            conn.close()

    def get_market_breakdown_calendar_data(
        self,
        time_type: str = 'day',
        user_id: str = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        获取按市场拆分的收益日历数据（首期仅支持 day）。

        返回:
            {
                time_type: "day",
                year: 2026,
                month: 2,
                items: [
                    {
                        date: "2026-02-17",
                        markets: {"a": ..., "hk": ..., "us": ..., "fund": ..., "unallocated": ...},
                        total_pnl: 123.45,  # 当日收益（日口径）
                        source: "exact|estimated|missing"
                    }
                ]
            }
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        if time_type != 'day':
            return {
                'error': 'Invalid calendar type',
                'code': 'INVALID_CALENDAR_PERIOD',
                'time_type': 'day',
                'year': int(year or 0),
                'month': int(month or 0),
                'items': [],
            }

        user_condition = "user_id = ?" if user_id else "(user_id IS NULL OR user_id = '')"
        user_param = (user_id,) if user_id else ()

        try:
            now = datetime.now()
            cursor.execute(
                f'''
                SELECT date
                FROM daily_snapshots
                WHERE {user_condition}
                ORDER BY date ASC
                ''',
                user_param,
            )
            all_dates = [str(r['date']) for r in cursor.fetchall() if r['date']]

            if not all_dates:
                return {
                    'time_type': 'day',
                    'year': int(year or now.year),
                    'month': int(month or now.month),
                    'items': [],
                }

            months_by_year: Dict[int, set] = {}
            for date_str in all_dates:
                parts = date_str.split('-')
                if len(parts) != 3:
                    continue
                y = int(parts[0])
                m = int(parts[1])
                months_by_year.setdefault(y, set()).add(m)

            selectable_years = sorted(months_by_year.keys())
            latest_year = selectable_years[-1]
            latest_month = max(months_by_year[latest_year])

            target_year = year
            target_month = month
            if target_year is None and target_month is None:
                if now.year in months_by_year and now.month in months_by_year[now.year]:
                    target_year = now.year
                    target_month = now.month
                else:
                    target_year = latest_year
                    target_month = latest_month
            else:
                if target_year is None:
                    target_year = now.year
                if target_month is None:
                    target_month = now.month

            assert target_year is not None
            assert target_month is not None

            if (
                target_year not in months_by_year
                or target_month not in months_by_year[target_year]
            ):
                return {
                    'error': 'Selected period has no snapshot data',
                    'code': 'INVALID_CALENDAR_PERIOD',
                    'time_type': 'day',
                    'year': int(target_year),
                    'month': int(target_month),
                    'items': [],
                }

            month_start = f'{target_year:04d}-{target_month:02d}-01'
            if target_month == 12:
                next_month = dt.datetime(target_year + 1, 1, 1)
            else:
                next_month = dt.datetime(target_year, target_month + 1, 1)
            month_end = (next_month - timedelta(days=1)).strftime('%Y-%m-%d')
            if target_year == now.year and target_month == now.month:
                month_end = min(month_end, now.strftime('%Y-%m-%d'))

            cursor.execute(
                f'''
                SELECT date, day_pnl
                FROM daily_snapshots
                WHERE date >= ? AND date <= ? AND {user_condition}
                ORDER BY date ASC
                ''',
                (month_start, month_end) + user_param,
            )
            snapshot_rows = cursor.fetchall()

            cursor.execute(
                f'''
                SELECT date, market, day_pnl, source
                FROM daily_snapshot_market_breakdowns
                WHERE date >= ? AND date <= ? AND {user_condition}
                ORDER BY date ASC
                ''',
                (month_start, month_end) + user_param,
            )
            breakdown_rows = cursor.fetchall()

            by_date: Dict[str, Dict[str, Any]] = {}
            for row in breakdown_rows:
                d = str(row['date'])
                data = by_date.setdefault(
                    d,
                    {
                        'markets': {m: None for m in MARKET_BREAKDOWN_MARKETS},
                        'sources': set(),
                    },
                )
                market = str(row['market'] or '').lower()
                if market not in data['markets']:
                    continue
                data['markets'][market] = round(float(row['day_pnl'] or 0.0), 2)
                source = str(row['source'] or '').strip().lower() or 'estimated'
                data['sources'].add(source)

            items: List[Dict[str, Any]] = []
            for row in snapshot_rows:
                date_str = str(row['date'])
                day_total = round(float(row['day_pnl'] or 0.0), 2)
                breakdown = by_date.get(date_str)
                if not breakdown:
                    markets = {m: None for m in MARKET_BREAKDOWN_MARKETS}
                    source = 'missing'
                else:
                    markets = {}
                    for market in MARKET_BREAKDOWN_MARKETS:
                        value = breakdown['markets'].get(market)
                        markets[market] = (
                            None if value is None else round(float(value), 2)
                        )
                    source_set = breakdown['sources']
                    source = 'exact' if source_set == {'exact'} else 'estimated'
                items.append(
                    {
                        'date': date_str,
                        'markets': markets,
                        'total_pnl': day_total,
                        'source': source,
                    }
                )

            return {
                'time_type': 'day',
                'year': int(target_year),
                'month': int(target_month),
                'items': items,
            }
        except Exception as e:
            logger.error(f"Failed to get market breakdown calendar data: {e}")
            return {
                'time_type': 'day',
                'year': int(year or 0),
                'month': int(month or 0),
                'items': [],
            }
        finally:
            conn.close()
    
    def get_rank_data(self, rank_type: str = 'gain', market: str = 'all', user_id: str = None) -> List[Dict[str, Any]]:
        """
        获取盈亏排行数据（持仓信息）
        
        Args:
            rank_type: gain|loss
            market: all|a|us|hk|fund
            user_id: 用户ID
            
        Returns:
            [{code, name, qty, cost_price, curr, adjustment, market}]
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 构建 user_id 条件
        user_condition = "user_id = ?" if user_id else "(user_id IS NULL OR user_id = '')"
        user_param = (user_id,) if user_id else ()
        
        try:
            if market == 'all':
                cursor.execute(f'''
                    SELECT code, name, qty, price, curr, adjustment FROM portfolio
                    WHERE {user_condition}
                ''', user_param)
            elif market == 'a':
                cursor.execute(f'''
                    SELECT code, name, qty, price, curr, adjustment FROM portfolio
                    WHERE (code LIKE 'sh%' OR code LIKE 'sz%' OR code LIKE 'bj%') AND {user_condition}
                ''', user_param)
            elif market == 'us':
                cursor.execute(f'''
                    SELECT code, name, qty, price, curr, adjustment FROM portfolio
                    WHERE code LIKE 'gb_%' AND {user_condition}
                ''', user_param)
            elif market == 'hk':
                cursor.execute(f'''
                    SELECT code, name, qty, price, curr, adjustment FROM portfolio
                    WHERE code LIKE 'hk%' AND {user_condition}
                ''', user_param)
            elif market == 'fund':
                cursor.execute(f'''
                    SELECT code, name, qty, price, curr, adjustment FROM portfolio
                    WHERE (code LIKE 'f_%' OR code LIKE 'ft_%') AND {user_condition}
                ''', user_param)
            
            data = []
            for row in cursor.fetchall():
                data.append({
                    'code': row['code'],
                    'name': row['name'],
                    'qty': float(row['qty']),
                    'cost_price': float(row['price']),
                    'curr': row['curr'],
                    'adjustment': float(row['adjustment']),
                    'market': self._detect_market(row['code'])
                })
            
            return data
        
        except Exception as e:
            logger.error(f"Failed to get rank data: {e}")
            return []
        finally:
            conn.close()
    
    def _detect_market(self, code: str) -> str:
        """根据代码检测市场类型"""
        if code.startswith('sh') or code.startswith('sz') or code.startswith('bj'):
            return 'a'
        elif code.startswith('hk'):
            return 'hk'
        elif code.startswith('gb_'):
            return 'us'
        elif code.startswith('f_') or code.startswith('ft_'):
            return 'fund'
        else:
            return 'other'

    def _normalize_cleanup_markets(self, markets: Optional[List[str]]) -> List[str]:
        allowed = {"a", "hk", "us", "fund"}
        result: List[str] = []
        for raw in (markets or list(DEFAULT_MARKETS)):
            market = str(raw or "").strip().lower()
            if market in allowed and market not in result:
                result.append(market)
        return result or list(DEFAULT_MARKETS)

    def get_closed_snapshot_dates(
        self,
        markets: Optional[List[str]] = None,
        user_id: str = None,
        start_date: str = "",
        end_date: str = "",
    ) -> List[str]:
        """
        获取在指定市场集合下判定为“休市日”的快照日期列表。
        """
        normalized_markets = self._normalize_cleanup_markets(markets)
        conn = self.get_connection()
        cursor = conn.cursor()

        sql = "SELECT DISTINCT date FROM daily_snapshots WHERE 1=1"
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
        sql += " ORDER BY date ASC"

        try:
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            result: List[str] = []
            for row in rows:
                date_str = str(row["date"])
                if is_markets_closed_on_date(normalized_markets, date_str):
                    result.append(date_str)
            return result
        finally:
            conn.close()

    def preview_cleanup_market_closed(
        self,
        markets: Optional[List[str]] = None,
        user_id: str = None,
        start_date: str = "",
        end_date: str = "",
    ) -> int:
        """
        预览休市日清理将影响的快照条数（按日期去重后的数量）。
        """
        return len(
            self.get_closed_snapshot_dates(
                markets=markets,
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
            )
        )

    def cleanup_market_closed_day_pnl(
        self,
        markets: Optional[List[str]] = None,
        user_id: str = None,
        start_date: str = "",
        end_date: str = "",
    ) -> int:
        """
        将判定为休市日的 day_pnl 批量清零。

        Returns:
            被更新的记录数。
        """
        dates = self.get_closed_snapshot_dates(
            markets=markets,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )
        if not dates:
            return 0

        conn = self.get_connection()
        cursor = conn.cursor()
        cleaned = 0

        try:
            for date_str in dates:
                if user_id:
                    cursor.execute(
                        """
                        UPDATE daily_snapshots
                        SET day_pnl = 0, updated_at = CURRENT_TIMESTAMP
                        WHERE date = ? AND user_id = ?
                        """,
                        (date_str, user_id),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE daily_snapshots
                        SET day_pnl = 0, updated_at = CURRENT_TIMESTAMP
                        WHERE date = ?
                        """,
                        (date_str,),
                    )
                cleaned += int(cursor.rowcount or 0)
            conn.commit()
            return cleaned
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def fix_snapshot_day_pnl(self, dates: list, user_id: str = None) -> bool:
        """
        修复指定日期的 day_pnl 为 0（用于修正休市日错误记录的数据）
        
        Args:
            dates: 日期列表，格式 ['2026-01-17', '2026-01-18']
            user_id: 用户ID
            
        Returns:
            True 表示成功
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            for date in dates:
                if user_id:
                    cursor.execute('''
                        UPDATE daily_snapshots 
                        SET day_pnl = 0, updated_at = CURRENT_TIMESTAMP
                        WHERE date = ? AND user_id = ?
                    ''', (date, user_id))
                else:
                    cursor.execute('''
                        UPDATE daily_snapshots 
                        SET day_pnl = 0, updated_at = CURRENT_TIMESTAMP
                        WHERE date = ? AND (user_id IS NULL OR user_id = '')
                    ''', (date,))
                logger.info(f"Fixed day_pnl for date: {date}")
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to fix snapshot day_pnl: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

# 全局数据库实例
db = DatabaseManager(str(config.DATABASE_PATH))
