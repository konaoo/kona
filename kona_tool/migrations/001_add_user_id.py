"""
数据库迁移：添加 user_id 字段到所有表

运行方式：
    python migrations/001_add_user_id.py

这个迁移会：
1. 给所有表添加 user_id 字段（可为空，便于兼容旧数据）
2. 创建用户表
3. 创建索引加速查询
"""
import sqlite3
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))
import config


def migrate():
    """执行迁移"""
    db_path = str(config.DATABASE_PATH)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Migrating database: {db_path}")
    
    try:
        # 1. 创建用户表
        print("Creating users table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # 2. 给 portfolio 表添加 user_id
        print("Adding user_id to portfolio...")
        try:
            cursor.execute('ALTER TABLE portfolio ADD COLUMN user_id TEXT')
        except sqlite3.OperationalError as e:
            if 'duplicate column' in str(e).lower():
                print("  - user_id already exists, skipping")
            else:
                raise
        
        # 3. 给 transactions 表添加 user_id
        print("Adding user_id to transactions...")
        try:
            cursor.execute('ALTER TABLE transactions ADD COLUMN user_id TEXT')
        except sqlite3.OperationalError as e:
            if 'duplicate column' in str(e).lower():
                print("  - user_id already exists, skipping")
            else:
                raise
        
        # 4. 给 cash_assets 表添加 user_id
        print("Adding user_id to cash_assets...")
        try:
            cursor.execute('ALTER TABLE cash_assets ADD COLUMN user_id TEXT')
        except sqlite3.OperationalError as e:
            if 'duplicate column' in str(e).lower():
                print("  - user_id already exists, skipping")
            else:
                raise
        
        # 5. 给 other_assets 表添加 user_id
        print("Adding user_id to other_assets...")
        try:
            cursor.execute('ALTER TABLE other_assets ADD COLUMN user_id TEXT')
        except sqlite3.OperationalError as e:
            if 'duplicate column' in str(e).lower():
                print("  - user_id already exists, skipping")
            else:
                raise
        
        # 6. 给 liabilities 表添加 user_id
        print("Adding user_id to liabilities...")
        try:
            cursor.execute('ALTER TABLE liabilities ADD COLUMN user_id TEXT')
        except sqlite3.OperationalError as e:
            if 'duplicate column' in str(e).lower():
                print("  - user_id already exists, skipping")
            else:
                raise
        
        # 7. 给 daily_snapshots 表添加 user_id
        print("Adding user_id to daily_snapshots...")
        try:
            cursor.execute('ALTER TABLE daily_snapshots ADD COLUMN user_id TEXT')
        except sqlite3.OperationalError as e:
            if 'duplicate column' in str(e).lower():
                print("  - user_id already exists, skipping")
            else:
                raise
        
        # 8. 修改 daily_snapshots 的唯一约束（date + user_id）
        # SQLite 不支持直接修改约束，需要重建表
        print("Updating daily_snapshots unique constraint...")
        # 先检查是否已经有新表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_snapshots_new'")
        if cursor.fetchone():
            cursor.execute("DROP TABLE daily_snapshots_new")
        
        cursor.execute('''
            CREATE TABLE daily_snapshots_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                user_id TEXT,
                total_asset REAL NOT NULL,
                total_invest REAL NOT NULL,
                total_cash REAL NOT NULL,
                total_other REAL NOT NULL,
                total_liability REAL NOT NULL,
                total_pnl REAL NOT NULL,
                day_pnl REAL NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, user_id)
            )
        ''')
        
        cursor.execute('''
            INSERT INTO daily_snapshots_new 
            SELECT id, date, user_id, total_asset, total_invest, total_cash, 
                   total_other, total_liability, total_pnl, day_pnl, updated_at
            FROM daily_snapshots
        ''')
        
        cursor.execute('DROP TABLE daily_snapshots')
        cursor.execute('ALTER TABLE daily_snapshots_new RENAME TO daily_snapshots')
        
        # 9. 创建索引
        print("Creating indexes...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_portfolio_user ON portfolio(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_cash_assets_user ON cash_assets(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_other_assets_user ON other_assets(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_liabilities_user ON liabilities(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_user ON daily_snapshots(user_id)')
        
        conn.commit()
        print("\nMigration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"\nMigration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    migrate()
