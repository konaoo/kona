"""
数据库管理模块
使用SQLite替代CSV文件，提供高效的数据存储和查询
"""
import sqlite3
import logging
from datetime import datetime as datetime
from pathlib import Path
import config  # 添加导入
try:
    from .db_admin_state import AdminStateDatabaseMixin
    from .db_analysis import AnalysisDatabaseMixin
    from .db_analysis import _is_market_closed_date as _is_market_closed_date
    from .db_maintenance import MaintenanceDatabaseMixin
    from .db_portfolio import PortfolioDatabaseMixin
    from .db_snapshots import SnapshotDatabaseMixin
    from .db_users import UserDatabaseMixin
    from .db_asset_accounts import AssetAccountDatabaseMixin
except ImportError:  # 兼容被单文件动态加载的测试场景
    from core.db_admin_state import AdminStateDatabaseMixin
    from core.db_analysis import AnalysisDatabaseMixin
    from core.db_analysis import _is_market_closed_date as _is_market_closed_date
    from core.db_maintenance import MaintenanceDatabaseMixin
    from core.db_portfolio import PortfolioDatabaseMixin
    from core.db_snapshots import SnapshotDatabaseMixin
    from core.db_users import UserDatabaseMixin
    from core.db_asset_accounts import AssetAccountDatabaseMixin

logger = logging.getLogger(__name__)


class DatabaseManager(
    UserDatabaseMixin,
    AdminStateDatabaseMixin,
    AssetAccountDatabaseMixin,
    PortfolioDatabaseMixin,
    SnapshotDatabaseMixin,
    AnalysisDatabaseMixin,
    MaintenanceDatabaseMixin,
):
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
                icon TEXT NOT NULL DEFAULT '🏦',
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
                icon TEXT NOT NULL DEFAULT '📦',
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
                icon TEXT NOT NULL DEFAULT '💳',
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
                build_start_at TIMESTAMP,
                last_login TIMESTAMP,
                last_login_ip TEXT,
                last_login_region TEXT,
                last_active_ip TEXT,
                last_active_region TEXT,
                last_active_at TIMESTAMP
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

        # 运行时配置表（用于后台可持久化运营配置）
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS runtime_configs (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_by TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            '''
        )

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

        # 价格异常巡检日报表（每天保留最新一版全局结果）
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS price_alert_reports (
                report_date TEXT PRIMARY KEY,
                tested_at_utc TEXT NOT NULL,
                total_assets INTEGER NOT NULL DEFAULT 0,
                alert_count INTEGER NOT NULL DEFAULT 0,
                summary_json TEXT NOT NULL DEFAULT '{}',
                items_json TEXT NOT NULL DEFAULT '[]',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # 行情测试小时快照（每小时保留最新一版四源检测结果）
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS provider_test_reports (
                report_slot TEXT PRIMARY KEY,
                tested_at_utc TEXT NOT NULL,
                summary_json TEXT NOT NULL DEFAULT '{}',
                providers_json TEXT NOT NULL DEFAULT '{}',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # 用户日活表（按 user_id + 日期去重），用于 DAU 和真正的 N 日留存
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_daily_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                activity_date TEXT NOT NULL,
                first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, activity_date)
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
        _ensure_column('portfolio', 'logo_url', "logo_url TEXT")
        _ensure_column('transactions', 'user_id', 'user_id TEXT')
        _ensure_column('cash_assets', 'user_id', 'user_id TEXT')
        _ensure_column('other_assets', 'user_id', 'user_id TEXT')
        _ensure_column('liabilities', 'user_id', 'user_id TEXT')
        _ensure_column('cash_assets', 'icon', "icon TEXT NOT NULL DEFAULT '🏦'")
        _ensure_column('other_assets', 'icon', "icon TEXT NOT NULL DEFAULT '📦'")
        _ensure_column('liabilities', 'icon', "icon TEXT NOT NULL DEFAULT '💳'")
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
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_snapshots_user_date_id ON daily_snapshots(user_id, date DESC, id DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_market_breakdowns_user_date ON daily_snapshot_market_breakdowns(user_id, date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_market_breakdowns_date ON daily_snapshot_market_breakdowns(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_market_breakdowns_source ON daily_snapshot_market_breakdowns(source)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_admin_user_id ON admin_audit_logs(admin_user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_created_at ON admin_audit_logs(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_action ON admin_audit_logs(action)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_invite_codes_status ON invite_codes(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_invite_codes_status_created_code ON invite_codes(status, created_at DESC, code ASC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_invite_codes_created_code ON invite_codes(created_at DESC, code ASC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_invite_codes_batch_id ON invite_codes(batch_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_auth_refresh_tokens_user_id ON auth_refresh_tokens(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_auth_refresh_tokens_expires_at ON auth_refresh_tokens(expires_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_runtime_configs_updated_at ON runtime_configs(updated_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_admin_api_policies_scope_type ON admin_api_policies(scope_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_alert_reports_tested_at ON price_alert_reports(tested_at_utc)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_provider_test_reports_tested_at ON provider_test_reports(tested_at_utc)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_daily_activity_date ON user_daily_activity(activity_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_daily_activity_user_id ON user_daily_activity(user_id)')
        cursor.execute('DROP TABLE IF EXISTS email_verification_codes')

        # 确保 asset_type 列存在并回填
        self._ensure_portfolio_asset_type(cursor)
        self._ensure_b_share_currency(cursor)
        self._ensure_admin_api_policies_defaults(cursor)
        self._backfill_user_daily_activity(cursor)

        conn.commit()
        conn.close()

# 全局数据库实例
db = DatabaseManager(str(config.DATABASE_PATH))
