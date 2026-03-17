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
    from .db_schema import DatabaseSchemaManager
    from .db_admin_state import AdminStateDatabaseMixin
    from .db_analysis import AnalysisDatabaseMixin
    from .db_analysis import _is_market_closed_date as _is_market_closed_date
    from .db_maintenance import MaintenanceDatabaseMixin
    from .db_portfolio import PortfolioDatabaseMixin
    from .db_snapshots import SnapshotDatabaseMixin
    from .db_users import UserDatabaseMixin
    from .db_asset_accounts import AssetAccountDatabaseMixin
except ImportError:  # 兼容被单文件动态加载的测试场景
    from core.db_schema import DatabaseSchemaManager
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
        self._schema_manager = DatabaseSchemaManager()
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
        self._schema_manager.initialize(db_manager=self, cursor=cursor)

        conn.commit()
        conn.close()

# 全局数据库实例
db = DatabaseManager(str(config.DATABASE_PATH))
