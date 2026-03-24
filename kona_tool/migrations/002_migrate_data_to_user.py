"""
数据迁移脚本：把所有旧数据（user_id 为空）迁移给指定用户

运行方式：
    python3 migrations/002_migrate_data_to_user.py konaeee@gmail.com
"""
import sqlite3
import sys
import uuid
from pathlib import Path
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))
import config


def migrate_to_user(email: str):
    """把所有旧数据迁移给指定用户"""
    db_path = str(config.DATABASE_PATH)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Database: {db_path}")
    print(f"Target email: {email}")
    print("-" * 50)
    
    try:
        # 1. 查找或创建用户
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        
        if row:
            user_id = row[0]
            print(f"Found existing user: {user_id}")
        else:
            user_id = str(uuid.uuid4())
            cursor.execute(
                'INSERT INTO users (id, email, created_at) VALUES (?, ?, ?)',
                (user_id, email, datetime.now().isoformat())
            )
            print(f"Created new user: {user_id}")
        
        # 2. 迁移 portfolio（持仓）
        cursor.execute('''
            UPDATE portfolio SET user_id = ? 
            WHERE user_id IS NULL OR user_id = ''
        ''', (user_id,))
        print(f"Migrated portfolio: {cursor.rowcount} records")
        
        # 3. 迁移 transactions（交易记录）
        cursor.execute('''
            UPDATE transactions SET user_id = ? 
            WHERE user_id IS NULL OR user_id = ''
        ''', (user_id,))
        print(f"Migrated transactions: {cursor.rowcount} records")
        
        # 4. 迁移 cash_assets（现金资产）
        cursor.execute('''
            UPDATE cash_assets SET user_id = ? 
            WHERE user_id IS NULL OR user_id = ''
        ''', (user_id,))
        print(f"Migrated cash_assets: {cursor.rowcount} records")
        
        # 5. 迁移 other_assets（其他资产）
        cursor.execute('''
            UPDATE other_assets SET user_id = ? 
            WHERE user_id IS NULL OR user_id = ''
        ''', (user_id,))
        print(f"Migrated other_assets: {cursor.rowcount} records")
        
        # 6. 迁移 liabilities（负债）
        cursor.execute('''
            UPDATE liabilities SET user_id = ? 
            WHERE user_id IS NULL OR user_id = ''
        ''', (user_id,))
        print(f"Migrated liabilities: {cursor.rowcount} records")
        
        # 7. 迁移 daily_snapshots（每日快照）
        cursor.execute('''
            UPDATE daily_snapshots SET user_id = ? 
            WHERE user_id IS NULL OR user_id = ''
        ''', (user_id,))
        print(f"Migrated daily_snapshots: {cursor.rowcount} records")
        
        conn.commit()
        print("-" * 50)
        print("Migration completed successfully!")
        print(f"User ID: {user_id}")
        print(f"Email: {email}")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 migrations/002_migrate_data_to_user.py <email>")
        print("Example: python3 migrations/002_migrate_data_to_user.py konaeee@gmail.com")
        sys.exit(1)
    
    email = sys.argv[1]
    migrate_to_user(email)
