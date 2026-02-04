"""
数据库管理模块
使用SQLite替代CSV文件，提供高效的数据存储和查询
"""
import sqlite3
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import config  # 添加导入

logger = logging.getLogger(__name__)


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
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
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
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                qty REAL NOT NULL,
                price REAL NOT NULL,
                curr TEXT NOT NULL DEFAULT 'CNY',
                adjustment REAL DEFAULT 0.0,
                asset_type TEXT DEFAULT 'a',
                user_id TEXT,
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

        # 创建用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                nickname TEXT,
                register_method TEXT,
                phone TEXT,
                user_number INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # 创建每日快照表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                total_asset REAL NOT NULL,
                total_invest REAL NOT NULL,
                total_cash REAL NOT NULL,
                total_other REAL NOT NULL,
                total_liability REAL NOT NULL,
                total_pnl REAL NOT NULL,
                day_pnl REAL NOT NULL,
                user_id TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Ensure user_id columns exist for older DBs
        def _ensure_column(table: str, column: str, col_def: str) -> None:
            cursor.execute(f'PRAGMA table_info({table})')
            cols = [row[1] for row in cursor.fetchall()]
            if column not in cols:
                cursor.execute(f'ALTER TABLE {table} ADD COLUMN {col_def}')

        _ensure_column('portfolio', 'user_id', 'user_id TEXT')
        _ensure_column('transactions', 'user_id', 'user_id TEXT')
        _ensure_column('cash_assets', 'user_id', 'user_id TEXT')
        _ensure_column('other_assets', 'user_id', 'user_id TEXT')
        _ensure_column('liabilities', 'user_id', 'user_id TEXT')
        _ensure_column('daily_snapshots', 'user_id', 'user_id TEXT')
        _ensure_column('users', 'nickname', 'nickname TEXT')
        _ensure_column('users', 'register_method', 'register_method TEXT')
        _ensure_column('users', 'phone', 'phone TEXT')
        _ensure_column('users', 'user_number', 'user_number INTEGER')
        _ensure_column('users', 'created_at', 'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        _ensure_column('users', 'last_login', 'last_login TIMESTAMP')

        # 创建索引以优化查询性能
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_portfolio_user_id ON portfolio(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_portfolio_code ON portfolio(code)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_code ON transactions(code)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_cash_assets_user_id ON cash_assets(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_other_assets_user_id ON other_assets(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_liabilities_user_id ON liabilities(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_snapshots_date ON daily_snapshots(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_snapshots_user_id ON daily_snapshots(user_id)')

        # 确保 asset_type 列存在并回填
        self._ensure_portfolio_asset_type(cursor)

        conn.commit()
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
    
    def get_portfolio(self, asset_type: str = 'all', user_id: str = None) -> List[Dict[str, Any]]:
        """获取持仓数据，支持按类型筛选"""
        conn = self.get_connection()
        cursor = conn.cursor()

        logger.info(f"get_portfolio called with asset_type: {asset_type}, user_id: {user_id}")

        # 构建 user_id 条件
        user_condition = "user_id = ?" if user_id else "(user_id IS NULL OR user_id = '')"
        user_param = (user_id,) if user_id else ()

        if asset_type == 'all':
            cursor.execute(f'''
                SELECT code, name, qty, price, curr, adjustment, asset_type
                FROM portfolio
                WHERE {user_condition}
                ORDER BY code
            ''', user_param)
        elif asset_type in ('a', 'us', 'hk', 'fund'):
            cursor.execute(f'''
                SELECT code, name, qty, price, curr, adjustment, asset_type
                FROM portfolio
                WHERE {user_condition} AND asset_type = ?
                ORDER BY code
            ''', user_param + (asset_type,))
        else:
            cursor.execute(f'''
                SELECT code, name, qty, price, curr, adjustment, asset_type
                FROM portfolio
                WHERE {user_condition}
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
            # 对于有 user_id 的情况，使用 code + user_id 作为唯一键
            if user_id:
                # 先检查是否存在
                cursor.execute('''
                    SELECT id FROM portfolio WHERE code = ? AND user_id = ?
                ''', (data['code'], user_id))
                
                if cursor.fetchone():
                    # 更新
                    cursor.execute('''
                        UPDATE portfolio SET name=?, qty=?, price=?, curr=?, adjustment=?, asset_type=?, updated_at=CURRENT_TIMESTAMP
                        WHERE code = ? AND user_id = ?
                    ''', (
                        data['name'],
                        data['qty'],
                        data['price'],
                        data.get('curr', 'CNY'),
                        data.get('adjustment', 0.0),
                        data.get('asset_type', 'a'),
                        data['code'],
                        user_id
                    ))
                else:
                    # 插入
                    cursor.execute('''
                        INSERT INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, user_id, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (
                        data['code'],
                        data['name'],
                        data['qty'],
                        data['price'],
                        data.get('curr', 'CNY'),
                        data.get('adjustment', 0.0),
                        data.get('asset_type', 'a'),
                        user_id
                    ))
            else:
                cursor.execute('''
                    INSERT OR REPLACE INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    data['code'],
                    data['name'],
                    data['qty'],
                    data['price'],
                    data.get('curr', 'CNY'),
                    data.get('adjustment', 0.0),
                    data.get('asset_type', 'a')
                ))
            
            conn.commit()
            logger.info(f"Asset added/updated: {data['code']}")
            return True
        except Exception as e:
            logger.error(f"Failed to add asset: {e}")
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
    
    def modify_asset(self, code: str, qty: float, price: float, adjustment: float, user_id: str = None) -> bool:
        """修正资产数据（数量、成本、调整值）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if user_id:
                cursor.execute('''
                    UPDATE portfolio 
                    SET qty = ?, price = ?, adjustment = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE code = ? AND user_id = ?
                ''', (qty, price, adjustment, code, user_id))
            else:
                cursor.execute('''
                    UPDATE portfolio 
                    SET qty = ?, price = ?, adjustment = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE code = ? AND (user_id IS NULL OR user_id = '')
                ''', (qty, price, adjustment, code))
            
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"Asset modified: {code}, qty={qty}, price={price}, adj={adjustment}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to modify asset: {e}")
            conn.rollback()
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
    
    def buy_asset(self, code: str, price: float, qty: float, user_id: str = None) -> bool:
        """加仓"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 获取当前持仓
            if user_id:
                cursor.execute('SELECT name, qty, price, curr FROM portfolio WHERE code = ? AND user_id = ?', (code, user_id))
            else:
                cursor.execute('SELECT name, qty, price, curr FROM portfolio WHERE code = ? AND (user_id IS NULL OR user_id = "")', (code,))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return False
            
            name, old_qty, old_price, curr = row
            
            # 计算加权平均成本
            new_qty = old_qty + qty
            new_price = (old_qty * old_price + qty * price) / new_qty if new_qty > 0 else 0
            
            # 更新持仓
            if user_id:
                cursor.execute('''
                    UPDATE portfolio SET qty = ?, price = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE code = ? AND user_id = ?
                ''', (new_qty, new_price, code, user_id))
            else:
                cursor.execute('''
                    UPDATE portfolio SET qty = ?, price = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE code = ? AND (user_id IS NULL OR user_id = '')
                ''', (new_qty, new_price, code))
            
            # 记录交易
            cursor.execute('''
                INSERT INTO transactions (time, code, name, type, price, qty, amount, pnl, user_id)
                VALUES (?, ?, ?, '加仓', ?, ?, ?, 0, ?)
            ''', (
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                code,
                name,
                price,
                qty,
                price * qty,
                user_id
            ))
            
            conn.commit()
            logger.info(f"Buy: {code}, qty={qty}, price={price}")
            return True
        except Exception as e:
            logger.error(f"Failed to buy asset: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def sell_asset(self, code: str, price: float, qty: float, user_id: str = None) -> bool:
        """减仓"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 获取当前持仓
            if user_id:
                cursor.execute('SELECT name, qty, price, curr, adjustment FROM portfolio WHERE code = ? AND user_id = ?', (code, user_id))
            else:
                cursor.execute('SELECT name, qty, price, curr, adjustment FROM portfolio WHERE code = ? AND (user_id IS NULL OR user_id = "")', (code,))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return False
            
            name, old_qty, old_price, curr, old_adj = row
            
            if qty > old_qty:
                conn.close()
                logger.warning(f"Oversell: {code}")
                return False
            
            # 计算实现盈亏
            pnl = (price - old_price) * qty
            
            # 更新持仓或删除
            new_qty = old_qty - qty
            if new_qty < 0.001:
                if user_id:
                    cursor.execute('DELETE FROM portfolio WHERE code = ? AND user_id = ?', (code, user_id))
                else:
                    cursor.execute('DELETE FROM portfolio WHERE code = ? AND (user_id IS NULL OR user_id = "")', (code,))
            else:
                if user_id:
                    cursor.execute('''
                        UPDATE portfolio SET qty = ?, adjustment = adjustment + ?, updated_at = CURRENT_TIMESTAMP
                        WHERE code = ? AND user_id = ?
                    ''', (new_qty, pnl, code, user_id))
                else:
                    cursor.execute('''
                        UPDATE portfolio SET qty = ?, adjustment = adjustment + ?, updated_at = CURRENT_TIMESTAMP
                        WHERE code = ? AND (user_id IS NULL OR user_id = '')
                    ''', (new_qty, pnl, code))
            
            # 记录交易
            cursor.execute('''
                INSERT INTO transactions (time, code, name, type, price, qty, amount, pnl, user_id)
                VALUES (?, ?, ?, '减仓', ?, ?, ?, ?, ?)
            ''', (
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                code,
                name,
                price,
                qty,
                price * qty,
                pnl,
                user_id
            ))
            
            conn.commit()
            logger.info(f"Sell: {code}, qty={qty}, price={price}, pnl={pnl}")
            return True
        except Exception as e:
            logger.error(f"Failed to sell asset: {e}")
            conn.rollback()
            return False
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
    
    def add_cash_asset(self, name: str, amount: float, curr: str = 'CNY', user_id: str = None) -> bool:
        """添加现金资产"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO cash_assets (name, amount, curr, user_id)
                VALUES (?, ?, ?, ?)
            ''', (name, amount, curr, user_id))
            
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
            cursor.execute('''
                INSERT INTO other_assets (name, amount, curr, user_id)
                VALUES (?, ?, ?, ?)
            ''', (name, amount, curr, user_id))
            
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
            cursor.execute('''
                INSERT INTO liabilities (name, amount, curr, user_id)
                VALUES (?, ?, ?, ?)
            ''', (name, amount, curr, user_id))
            
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
            
            conn.commit()
            logger.info(f"Liability updated: {liability_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update liability: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    def get_today_realized_pnl(self) -> float:
        """获取今日已实现盈亏（卖出产生的盈亏）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        
        try:
            cursor.execute('''
                SELECT SUM(pnl) 
                FROM transactions 
                WHERE type = '减仓' AND time LIKE ?
            ''', (f'{today}%',))
            result = cursor.fetchone()[0]
            return float(result) if result else 0.0
        except Exception as e:
            logger.error(f"Failed to get realized pnl: {e}")
            return 0.0
        finally:
            conn.close()

    def save_daily_snapshot(self, data: Dict[str, float], user_id: str = None) -> bool:
        """保存每日资产快照（如果当日已存在则更新）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        try:
            if user_id:
                cursor.execute('''
                    SELECT id FROM daily_snapshots WHERE date = ? AND user_id = ?
                ''', (today, user_id))
                
                if cursor.fetchone():
                    cursor.execute('''
                        UPDATE daily_snapshots SET
                            total_asset=?, total_invest=?, total_cash=?,
                            total_other=?, total_liability=?, total_pnl=?,
                            day_pnl=?, updated_at=CURRENT_TIMESTAMP
                        WHERE date = ? AND user_id = ?
                    ''', (
                        data.get('total_asset', 0),
                        data.get('total_invest', 0),
                        data.get('total_cash', 0),
                        data.get('total_other', 0),
                        data.get('total_liability', 0),
                        data.get('total_pnl', 0),
                        data.get('day_pnl', 0),
                        today,
                        user_id
                    ))
                else:
                    cursor.execute('''
                        INSERT INTO daily_snapshots (
                            date, total_asset, total_invest, total_cash, 
                            total_other, total_liability, total_pnl, day_pnl, user_id, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (
                        today,
                        data.get('total_asset', 0),
                        data.get('total_invest', 0),
                        data.get('total_cash', 0),
                        data.get('total_other', 0),
                        data.get('total_liability', 0),
                        data.get('total_pnl', 0),
                        data.get('day_pnl', 0),
                        user_id
                    ))
            else:
                # 对于无 user_id 的情况 (兼容旧版)
                cursor.execute('''
                    SELECT id FROM daily_snapshots WHERE date = ? AND (user_id IS NULL OR user_id = '')
                ''', (today,))
                
                if cursor.fetchone():
                    cursor.execute('''
                        UPDATE daily_snapshots SET
                            total_asset=?, total_invest=?, total_cash=?,
                            total_other=?, total_liability=?, total_pnl=?,
                            day_pnl=?, updated_at=CURRENT_TIMESTAMP
                        WHERE date = ? AND (user_id IS NULL OR user_id = '')
                    ''', (
                        data.get('total_asset', 0),
                        data.get('total_invest', 0),
                        data.get('total_cash', 0),
                        data.get('total_other', 0),
                        data.get('total_liability', 0),
                        data.get('total_pnl', 0),
                        data.get('day_pnl', 0),
                        today
                    ))
                else:
                    cursor.execute('''
                        INSERT INTO daily_snapshots (
                            date, total_asset, total_invest, total_cash, 
                            total_other, total_liability, total_pnl, day_pnl, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (
                        today,
                        data.get('total_asset', 0),
                        data.get('total_invest', 0),
                        data.get('total_cash', 0),
                        data.get('total_other', 0),
                        data.get('total_liability', 0),
                        data.get('total_pnl', 0),
                        data.get('day_pnl', 0)
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

            def _fetch_prev_snapshot(date_str: str):
                cursor.execute(f'''
                    SELECT date, total_pnl, total_invest FROM daily_snapshots
                    WHERE date < ? AND {user_condition}
                    ORDER BY date DESC
                    LIMIT 1
                ''', (date_str,) + user_param)
                return cursor.fetchone()

            def _fetch_last_snapshot(date_str: str):
                cursor.execute(f'''
                    SELECT date, total_pnl, total_invest FROM daily_snapshots
                    WHERE date <= ? AND {user_condition}
                    ORDER BY date DESC
                    LIMIT 1
                ''', (date_str,) + user_param)
                return cursor.fetchone()
            
            if period == 'day':
                cursor.execute(f'''
                    SELECT date, total_pnl, total_invest FROM daily_snapshots
                    WHERE date = ? AND {user_condition}
                    LIMIT 1
                ''', (today.strftime('%Y-%m-%d'),) + user_param)
                row = cursor.fetchone()
                if row:
                    today_total = float(row['total_pnl']) if row['total_pnl'] else 0
                    base = float(row['total_invest']) if row['total_invest'] else 1
                    cursor.execute(f'''
                        SELECT total_pnl FROM daily_snapshots
                        WHERE date < ? AND {user_condition}
                        ORDER BY date DESC
                        LIMIT 1
                    ''', (today.strftime('%Y-%m-%d'),) + user_param)
                    prev = cursor.fetchone()
                    prev_total = float(prev['total_pnl']) if prev and prev['total_pnl'] else 0
                    pnl = today_total - prev_total
                    return {'pnl': pnl, 'pnl_rate': round(pnl / base * 100, 2) if base else 0, 'base_value': base}
                return {'pnl': 0, 'pnl_rate': 0, 'base_value': 0}
            
            elif period == 'month':
                month_start = today.strftime('%Y-%m-01')
                cursor.execute(f'''
                    SELECT date, total_pnl, total_invest FROM daily_snapshots
                    WHERE date >= ? AND date <= ? AND {user_condition}
                    ORDER BY date ASC
                ''', (month_start, today.strftime('%Y-%m-%d')) + user_param)
                rows = cursor.fetchall()
                prev = _fetch_prev_snapshot(month_start)
                if rows:
                    last = rows[-1]
                    base_row = prev or rows[0]
                else:
                    last = _fetch_last_snapshot(today.strftime('%Y-%m-%d'))
                    base_row = prev or last
                if last and base_row:
                    pnl = float(last['total_pnl'] or 0) - float(base_row['total_pnl'] or 0)
                    base = float(base_row['total_invest'] or 0) or float(last['total_invest'] or 0) or 1
                    return {'pnl': pnl, 'pnl_rate': round(pnl / base * 100, 2) if base else 0, 'base_value': base}
                return {'pnl': 0, 'pnl_rate': 0, 'base_value': 0}
            
            elif period == 'year':
                year_start = today.strftime('%Y-01-01')
                cursor.execute(f'''
                    SELECT date, total_pnl, total_invest FROM daily_snapshots
                    WHERE date >= ? AND date <= ? AND {user_condition}
                    ORDER BY date ASC
                ''', (year_start, today.strftime('%Y-%m-%d')) + user_param)
                rows = cursor.fetchall()
                prev = _fetch_prev_snapshot(year_start)
                if rows:
                    last = rows[-1]
                    base_row = prev or rows[0]
                else:
                    last = _fetch_last_snapshot(today.strftime('%Y-%m-%d'))
                    base_row = prev or last
                if last and base_row:
                    pnl = float(last['total_pnl'] or 0) - float(base_row['total_pnl'] or 0)
                    base = float(base_row['total_invest'] or 0) or float(last['total_invest'] or 0) or 1
                    return {'pnl': pnl, 'pnl_rate': round(pnl / base * 100, 2) if base else 0, 'base_value': base}
                return {'pnl': 0, 'pnl_rate': 0, 'base_value': 0}
            
            else:  # all
                cursor.execute(f'''
                    SELECT date, total_pnl, total_invest FROM daily_snapshots
                    WHERE {user_condition}
                    ORDER BY date ASC
                ''', user_param)
                rows = cursor.fetchall()
                if rows:
                    first = rows[0]
                    last = rows[-1]
                    pnl = float(last['total_pnl']) - float(first['total_pnl'])
                    base = float(first['total_invest']) if first['total_invest'] else 1
                    return {'pnl': pnl, 'pnl_rate': round(pnl / base * 100, 2) if base else 0, 'base_value': base}
                return {'pnl': 0, 'pnl_rate': 0, 'base_value': 0}
        
        except Exception as e:
            logger.error(f"Failed to get pnl overview: {e}")
            return {'pnl': 0, 'pnl_rate': 0, 'base_value': 0}
        finally:
            conn.close()
    
    def get_calendar_data(self, time_type: str = 'day', user_id: str = None) -> Dict[str, Any]:
        """
        获取收益日历数据
        
        Args:
            time_type: day|month|year
            user_id: 用户ID
            
        Returns:
            {items: [{label, pnl}], total_pnl, total_rate, title}
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 构建 user_id 条件
        user_condition = "user_id = ?" if user_id else "(user_id IS NULL OR user_id = '')"
        user_param = (user_id,) if user_id else ()
        
        try:
            today = datetime.now()
            items = []
            total_pnl = 0
            
            if time_type == 'day':
                month_start = today.strftime('%Y-%m-01')
                cursor.execute(f'''
                    SELECT date, day_pnl, total_pnl FROM daily_snapshots 
                    WHERE date >= ? AND date <= ? AND {user_condition}
                    ORDER BY date ASC
                ''', (month_start, today.strftime('%Y-%m-%d')) + user_param)
                
                prev_total = None
                for row in cursor.fetchall():
                    day = int(row['date'].split('-')[2])
                    pnl = float(row['day_pnl']) if row['day_pnl'] is not None else 0
                    if (pnl == 0 or pnl == -0.0) and row['total_pnl'] is not None and prev_total is not None:
                        pnl = float(row['total_pnl']) - prev_total
                    if row['total_pnl'] is not None:
                        prev_total = float(row['total_pnl'])
                    items.append({'label': str(day), 'pnl': pnl})
                    total_pnl += pnl
                
                title = f"{today.month}月累计"
            
            elif time_type == 'month':
                year_start = today.strftime('%Y-01-01')
                cursor.execute(f'''
                    SELECT date, total_pnl FROM daily_snapshots
                    WHERE date >= ? AND date <= ? AND {user_condition}
                    ORDER BY date ASC
                ''', (year_start, today.strftime('%Y-%m-%d')) + user_param)

                month_last = {}
                for row in cursor.fetchall():
                    date = row['date']
                    m = int(date.split('-')[1])
                    tp = float(row['total_pnl']) if row['total_pnl'] is not None else 0.0
                    month_last[m] = tp

                cursor.execute(f'''
                    SELECT total_pnl FROM daily_snapshots
                    WHERE date < ? AND {user_condition}
                    ORDER BY date DESC
                    LIMIT 1
                ''', (year_start,) + user_param)
                base_row = cursor.fetchone()
                prev_total = float(base_row['total_pnl']) if base_row and base_row['total_pnl'] is not None else 0.0

                for m in range(1, today.month + 1):
                    current_total = month_last.get(m, prev_total)
                    pnl = current_total - prev_total
                    items.append({'label': f"{m}月", 'pnl': pnl})
                    total_pnl += pnl
                    prev_total = current_total

                title = f"{today.year}年累计"
            
            elif time_type == 'year':
                cursor.execute(f'''
                    SELECT date, total_pnl FROM daily_snapshots
                    WHERE {user_condition}
                    ORDER BY date ASC
                ''', user_param)

                rows = cursor.fetchall()
                if rows:
                    year_last = {}
                    for row in rows:
                        date = row['date']
                        y = int(date.split('-')[0])
                        tp = float(row['total_pnl']) if row['total_pnl'] is not None else 0.0
                        year_last[y] = tp
                    start_year = int(rows[0]['date'].split('-')[0])
                    prev_total = float(rows[0]['total_pnl']) if rows[0]['total_pnl'] is not None else 0.0
                    for y in range(start_year, today.year + 1):
                        current_total = year_last.get(y, prev_total)
                        pnl = current_total - prev_total
                        items.append({'label': str(y), 'pnl': pnl})
                        total_pnl += pnl
                        prev_total = current_total

                title = "总累计"
            
            cursor.execute(f'''
                SELECT total_invest FROM daily_snapshots WHERE {user_condition} ORDER BY date ASC LIMIT 1
            ''', user_param)
            row = cursor.fetchone()
            base = float(row['total_invest']) if row and row['total_invest'] else 1
            total_rate = round(total_pnl / base * 100, 2) if base else 0
            
            return {
                'items': items,
                'total_pnl': total_pnl,
                'total_rate': total_rate,
                'title': title
            }
        
        except Exception as e:
            logger.error(f"Failed to get calendar data: {e}")
            return {'items': [], 'total_pnl': 0, 'total_rate': 0, 'title': ''}
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
