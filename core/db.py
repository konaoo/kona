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
    
    VALID_FIELDS = {'code', 'name', 'qty', 'price', 'curr', 'adjustment'}
    
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    def get_portfolio(self, asset_type: str = 'all') -> List[Dict[str, Any]]:
        """获取持仓数据，支持按类型筛选"""
        conn = self.get_connection()
        cursor = conn.cursor()

        logger.info(f"get_portfolio called with asset_type: {asset_type}")

        if asset_type == 'all':
            cursor.execute('''
                SELECT code, name, qty, price, curr, adjustment
                FROM portfolio
                ORDER BY code
            ''')
        elif asset_type == 'stock_cn':
            # A股: sh/sz/bj开头 或 ETF代码
            cursor.execute('''
                SELECT code, name, qty, price, curr, adjustment
                FROM portfolio
                WHERE code LIKE 'sh%' OR code LIKE 'sz%' OR code LIKE 'bj%'
                   OR code IN ('159201', '159655', '512890', '513130', '513530')
                ORDER BY code
            ''')
        elif asset_type == 'stock_us':
            # 美股: gb_开头 或 纯字母（不含下划线和点）
            cursor.execute('''
                SELECT code, name, qty, price, curr, adjustment
                FROM portfolio
                WHERE code LIKE 'gb_%' 
                   OR (code NOT LIKE 'f_%' 
                       AND code NOT LIKE 'ft_%' 
                       AND code NOT LIKE 'gb_%'
                       AND code NOT LIKE 'sh%' 
                       AND code NOT LIKE 'sz%' 
                       AND code NOT LIKE 'hk%' 
                       AND code NOT LIKE 'bj%'
                       AND code NOT LIKE '%.%' 
                       AND code GLOB '[A-Za-z][A-Za-z]*')
                ORDER BY code
            ''')
        elif asset_type == 'stock_hk':
            # 港股: hk开头 或 .HK结尾
            logger.info("Querying HK stocks")
            cursor.execute('''
                SELECT code, name, qty, price, curr, adjustment
                FROM portfolio
                WHERE code LIKE 'hk%' OR code LIKE '%.HK' OR code LIKE '%.hk'
                ORDER BY code
            ''')
        elif asset_type == 'fund':
            # 基金: f_ 或 ft_ 开头
            cursor.execute('''
                SELECT code, name, qty, price, curr, adjustment
                FROM portfolio
                WHERE code LIKE 'f_%' OR code LIKE 'ft_%'
                ORDER BY code
            ''')
        else:
            cursor.execute('''
                SELECT code, name, qty, price, curr, adjustment
                FROM portfolio
                ORDER BY code
            ''')
        
        data = []
        for row in cursor.fetchall():
            data.append({
                'code': row['code'],
                'name': row['name'],
                'qty': float(row['qty']),
                'price': float(row['price']),
                'curr': row['curr'],
                'adjustment': float(row['adjustment'])
            })

        logger.info(f"get_portfolio returned {len(data)} records for type {asset_type}")

        conn.close()
        return data
    
    def get_asset(self, code: str) -> Optional[Dict[str, Any]]:
        """获取单个资产信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT code, name, qty, price, curr, adjustment
            FROM portfolio
            WHERE code = ?
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
                'adjustment': float(row['adjustment'])
            }
        return None
    
    def add_asset(self, data: Dict[str, Any]) -> bool:
        """添加或更新资产"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO portfolio (code, name, qty, price, curr, adjustment, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                data['code'],
                data['name'],
                data['qty'],
                data['price'],
                data.get('curr', 'CNY'),
                data.get('adjustment', 0.0)
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
    
    def update_asset(self, code: str, field: str, value: float) -> bool:
        """更新资产字段"""
        if field not in self.VALID_FIELDS:
            logger.error(f"Invalid field name: {field}")
            return False
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 对于 adjustment 字段，需要累加
            if field == 'adjustment':
                cursor.execute('''
                    UPDATE portfolio SET adjustment = COALESCE(adjustment, 0) + ?, updated_at = CURRENT_TIMESTAMP
                    WHERE code = ?
                ''', (value, code))
            else:
                cursor.execute(f'''
                    UPDATE portfolio SET {field} = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE code = ?
                ''', (value, code))
            
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
    
    def modify_asset(self, code: str, qty: float, price: float, adjustment: float) -> bool:
        """修正资产数据（数量、成本、调整值）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE portfolio 
                SET qty = ?, price = ?, adjustment = ?, updated_at = CURRENT_TIMESTAMP
                WHERE code = ?
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

    def delete_asset(self, code: str) -> bool:
        """删除资产"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM portfolio WHERE code = ?', (code,))
            conn.commit()
            logger.info(f"Asset deleted: {code}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete asset: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def buy_asset(self, code: str, price: float, qty: float) -> bool:
        """加仓"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 获取当前持仓
            cursor.execute('SELECT name, qty, price, curr FROM portfolio WHERE code = ?', (code,))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return False
            
            name, old_qty, old_price, curr = row
            
            # 计算加权平均成本
            new_qty = old_qty + qty
            new_price = (old_qty * old_price + qty * price) / new_qty if new_qty > 0 else 0
            
            # 更新持仓
            cursor.execute('''
                UPDATE portfolio SET qty = ?, price = ?, updated_at = CURRENT_TIMESTAMP
                WHERE code = ?
            ''', (new_qty, new_price, code))
            
            # 记录交易
            cursor.execute('''
                INSERT INTO transactions (time, code, name, type, price, qty, amount, pnl)
                VALUES (?, ?, ?, '加仓', ?, ?, ?, 0)
            ''', (
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                code,
                name,
                price,
                qty,
                price * qty
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
    
    def sell_asset(self, code: str, price: float, qty: float) -> bool:
        """减仓"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 获取当前持仓
            cursor.execute('SELECT name, qty, price, curr, adjustment FROM portfolio WHERE code = ?', (code,))
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
                cursor.execute('DELETE FROM portfolio WHERE code = ?', (code,))
            else:
                cursor.execute('''
                    UPDATE portfolio SET qty = ?, adjustment = adjustment + ?, updated_at = CURRENT_TIMESTAMP
                    WHERE code = ?
                ''', (new_qty, pnl, code))
            
            # 记录交易
            cursor.execute('''
                INSERT INTO transactions (time, code, name, type, price, qty, amount, pnl)
                VALUES (?, ?, ?, '减仓', ?, ?, ?, ?)
            ''', (
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                code,
                name,
                price,
                qty,
                price * qty,
                pnl
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
    
    def get_transactions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取交易记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT time, code, name, type, price, qty, amount, pnl
            FROM transactions
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
    
    def get_cash_assets(self) -> List[Dict[str, Any]]:
        """获取所有现金资产"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, amount, curr
            FROM cash_assets
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
    
    def add_cash_asset(self, name: str, amount: float, curr: str = 'CNY') -> bool:
        """添加现金资产"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO cash_assets (name, amount, curr)
                VALUES (?, ?, ?)
            ''', (name, amount, curr))
            
            conn.commit()
            logger.info(f"Cash asset added: {name}, amount={amount}")
            return True
        except Exception as e:
            logger.error(f"Failed to add cash asset: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def delete_cash_asset(self, asset_id: int) -> bool:
        """删除现金资产"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM cash_assets WHERE id = ?', (asset_id,))
            conn.commit()
            logger.info(f"Cash asset deleted: {asset_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete cash asset: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_other_assets(self) -> List[Dict[str, Any]]:
        """获取所有其他资产"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, amount, curr
            FROM other_assets
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
    
    def add_other_asset(self, name: str, amount: float, curr: str = 'CNY') -> bool:
        """添加其他资产"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO other_assets (name, amount, curr)
                VALUES (?, ?, ?)
            ''', (name, amount, curr))
            
            conn.commit()
            logger.info(f"Other asset added: {name}, amount={amount}")
            return True
        except Exception as e:
            logger.error(f"Failed to add other asset: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def delete_other_asset(self, asset_id: int) -> bool:
        """删除其他资产"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM other_assets WHERE id = ?', (asset_id,))
            conn.commit()
            logger.info(f"Other asset deleted: {asset_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete other asset: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def update_cash_asset(self, asset_id: int, name: str, amount: float, curr: str = 'CNY') -> bool:
        """更新现金资产"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE cash_assets SET name = ?, amount = ?, curr = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
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
    
    def update_other_asset(self, asset_id: int, name: str, amount: float, curr: str = 'CNY') -> bool:
        """更新其他资产"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE other_assets SET name = ?, amount = ?, curr = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
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
    
    def get_liabilities(self) -> List[Dict[str, Any]]:
        """获取所有负债"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, amount, curr
            FROM liabilities
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
    
    def add_liability(self, name: str, amount: float, curr: str = 'CNY') -> bool:
        """添加负债"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO liabilities (name, amount, curr)
                VALUES (?, ?, ?)
            ''', (name, amount, curr))
            
            conn.commit()
            logger.info(f"Liability added: {name}, amount={amount}")
            return True
        except Exception as e:
            logger.error(f"Failed to add liability: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def delete_liability(self, liability_id: int) -> bool:
        """删除负债"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM liabilities WHERE id = ?', (liability_id,))
            conn.commit()
            logger.info(f"Liability deleted: {liability_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete liability: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def update_liability(self, liability_id: int, name: str, amount: float, curr: str = 'CNY') -> bool:
        """更新负债"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE liabilities SET name = ?, amount = ?, curr = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
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

    def save_daily_snapshot(self, data: Dict[str, float]) -> bool:
        """保存每日资产快照（如果当日已存在则更新）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        try:
            cursor.execute('''
                INSERT INTO daily_snapshots (
                    date, total_asset, total_invest, total_cash, 
                    total_other, total_liability, total_pnl, day_pnl, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(date) DO UPDATE SET
                    total_asset=excluded.total_asset,
                    total_invest=excluded.total_invest,
                    total_cash=excluded.total_cash,
                    total_other=excluded.total_other,
                    total_liability=excluded.total_liability,
                    total_pnl=excluded.total_pnl,
                    day_pnl=excluded.day_pnl,
                    updated_at=CURRENT_TIMESTAMP
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
            
    def get_history(self, limit: int = 365) -> List[Dict[str, Any]]:
        """获取历史资产数据"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT * FROM daily_snapshots 
                ORDER BY date ASC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    # ============================================================
    # 分析数据查询
    # ============================================================
    
    def get_pnl_overview(self, period: str = 'day') -> Dict[str, Any]:
        """
        获取盈亏概览数据
        
        Args:
            period: day|month|year|all
            
        Returns:
            {pnl: float, pnl_rate: float, base_value: float}
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            today = datetime.now()
            
            if period == 'day':
                cursor.execute('''
                    SELECT day_pnl, total_invest FROM daily_snapshots 
                    WHERE date = ? 
                    LIMIT 1
                ''', (today.strftime('%Y-%m-%d'),))
                row = cursor.fetchone()
                if row:
                    pnl = float(row['day_pnl'])
                    base = float(row['total_invest']) if row['total_invest'] else 1
                    return {'pnl': pnl, 'pnl_rate': round(pnl / base * 100, 2) if base else 0, 'base_value': base}
                return {'pnl': 0, 'pnl_rate': 0, 'base_value': 0}
            
            elif period == 'month':
                month_start = today.strftime('%Y-%m-01')
                cursor.execute('''
                    SELECT SUM(day_pnl) as total_pnl, 
                           (SELECT total_invest FROM daily_snapshots WHERE date >= ? ORDER BY date ASC LIMIT 1) as base
                    FROM daily_snapshots 
                    WHERE date >= ? AND date <= ?
                ''', (month_start, month_start, today.strftime('%Y-%m-%d')))
                row = cursor.fetchone()
                if row:
                    pnl = float(row['total_pnl']) if row['total_pnl'] else 0
                    base = float(row['base']) if row['base'] else 1
                    return {'pnl': pnl, 'pnl_rate': round(pnl / base * 100, 2) if base else 0, 'base_value': base}
                return {'pnl': 0, 'pnl_rate': 0, 'base_value': 0}
            
            elif period == 'year':
                year_start = today.strftime('%Y-01-01')
                cursor.execute('''
                    SELECT SUM(day_pnl) as total_pnl,
                           (SELECT total_invest FROM daily_snapshots WHERE date >= ? ORDER BY date ASC LIMIT 1) as base
                    FROM daily_snapshots 
                    WHERE date >= ? AND date <= ?
                ''', (year_start, year_start, today.strftime('%Y-%m-%d')))
                row = cursor.fetchone()
                if row:
                    pnl = float(row['total_pnl']) if row['total_pnl'] else 0
                    base = float(row['base']) if row['base'] else 1
                    return {'pnl': pnl, 'pnl_rate': round(pnl / base * 100, 2) if base else 0, 'base_value': base}
                return {'pnl': 0, 'pnl_rate': 0, 'base_value': 0}
            
            else:  # all
                cursor.execute('''
                    SELECT SUM(day_pnl) as total_pnl,
                           (SELECT total_invest FROM daily_snapshots ORDER BY date ASC LIMIT 1) as base
                    FROM daily_snapshots
                ''')
                row = cursor.fetchone()
                if row:
                    pnl = float(row['total_pnl']) if row['total_pnl'] else 0
                    base = float(row['base']) if row['base'] else 1
                    return {'pnl': pnl, 'pnl_rate': round(pnl / base * 100, 2) if base else 0, 'base_value': base}
                return {'pnl': 0, 'pnl_rate': 0, 'base_value': 0}
        
        except Exception as e:
            logger.error(f"Failed to get pnl overview: {e}")
            return {'pnl': 0, 'pnl_rate': 0, 'base_value': 0}
        finally:
            conn.close()
    
    def get_calendar_data(self, time_type: str = 'day') -> Dict[str, Any]:
        """
        获取收益日历数据
        
        Args:
            time_type: day|month|year
            
        Returns:
            {items: [{label, pnl}], total_pnl, total_rate, title}
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            today = datetime.now()
            items = []
            total_pnl = 0
            
            if time_type == 'day':
                month_start = today.strftime('%Y-%m-01')
                cursor.execute('''
                    SELECT date, day_pnl FROM daily_snapshots 
                    WHERE date >= ? AND date <= ?
                    ORDER BY date ASC
                ''', (month_start, today.strftime('%Y-%m-%d')))
                
                for row in cursor.fetchall():
                    day = int(row['date'].split('-')[2])
                    pnl = float(row['day_pnl'])
                    items.append({'label': str(day), 'pnl': pnl})
                    total_pnl += pnl
                
                title = f"{today.month}月累计"
            
            elif time_type == 'month':
                year_start = today.strftime('%Y-01-01')
                cursor.execute('''
                    SELECT strftime('%m', date) as month, SUM(day_pnl) as month_pnl 
                    FROM daily_snapshots 
                    WHERE date >= ? AND date <= ?
                    GROUP BY strftime('%Y-%m', date)
                    ORDER BY month ASC
                ''', (year_start, today.strftime('%Y-%m-%d')))
                
                for row in cursor.fetchall():
                    month = int(row['month'])
                    pnl = float(row['month_pnl']) if row['month_pnl'] else 0
                    items.append({'label': f"{month}月", 'pnl': pnl})
                    total_pnl += pnl
                
                title = f"{today.year}年累计"
            
            elif time_type == 'year':
                cursor.execute('''
                    SELECT strftime('%Y', date) as year, SUM(day_pnl) as year_pnl 
                    FROM daily_snapshots 
                    GROUP BY strftime('%Y', date)
                    ORDER BY year ASC
                ''')
                
                for row in cursor.fetchall():
                    year = row['year']
                    pnl = float(row['year_pnl']) if row['year_pnl'] else 0
                    items.append({'label': year, 'pnl': pnl})
                    total_pnl += pnl
                
                title = "总累计"
            
            cursor.execute('''
                SELECT total_invest FROM daily_snapshots ORDER BY date ASC LIMIT 1
            ''')
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
    
    def get_rank_data(self, rank_type: str = 'gain', market: str = 'all') -> List[Dict[str, Any]]:
        """
        获取盈亏排行数据（持仓信息）
        
        Args:
            rank_type: gain|loss
            market: all|a|us|hk|fund
            
        Returns:
            [{code, name, qty, cost_price, curr, adjustment, market}]
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if market == 'all':
                cursor.execute('''
                    SELECT code, name, qty, price, curr, adjustment FROM portfolio
                ''')
            elif market == 'a':
                cursor.execute('''
                    SELECT code, name, qty, price, curr, adjustment FROM portfolio
                    WHERE code LIKE 'sh%' OR code LIKE 'sz%' OR code LIKE 'bj%'
                ''')
            elif market == 'us':
                cursor.execute('''
                    SELECT code, name, qty, price, curr, adjustment FROM portfolio
                    WHERE code LIKE 'gb_%'
                ''')
            elif market == 'hk':
                cursor.execute('''
                    SELECT code, name, qty, price, curr, adjustment FROM portfolio
                    WHERE code LIKE 'hk%'
                ''')
            elif market == 'fund':
                cursor.execute('''
                    SELECT code, name, qty, price, curr, adjustment FROM portfolio
                    WHERE code LIKE 'f_%' OR code LIKE 'ft_%'
                ''')
            
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
    
    def fix_snapshot_day_pnl(self, dates: list) -> bool:
        """
        修复指定日期的 day_pnl 为 0（用于修正休市日错误记录的数据）
        
        Args:
            dates: 日期列表，格式 ['2026-01-17', '2026-01-18']
            
        Returns:
            True 表示成功
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            for date in dates:
                cursor.execute('''
                    UPDATE daily_snapshots 
                    SET day_pnl = 0, updated_at = CURRENT_TIMESTAMP
                    WHERE date = ?
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
