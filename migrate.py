"""
数据迁移脚本 - 将CSV数据导入SQLite数据库
"""
import csv
import json
import sys
from core.db import DatabaseManager
import config

def migrate_csv_to_db():
    """迁移CSV数据到SQLite数据库"""
    
    print("Start data migration...")
    
    # 读取CSV文件
    csv_path = config.BASE_DIR / "portfolio.csv"
    if not csv_path.exists():
        print(f"CSV file not found: {csv_path}")
        print("Try to import from portfolio.json...")
        migrate_json_to_db()
        return
    
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            data = list(reader)
        
        print(f"Found {len(data)} CSV records")
        
        # 导入到数据库
        db = DatabaseManager(str(config.DATABASE_PATH))
        
        count = 0
        for row in data:
            # 检查必要字段
            if not row.get('code'):
                continue
            
            # 处理968开头的基金代码
            code = row['code']
            if code.isdigit() and code.startswith('968'):
                code = f"f_{code}"
            elif code.isdigit() and code.startswith('11'):
                code = f"f_{code}"
            
            asset = {
                'code': code,
                'name': row.get('name', code),
                'qty': float(row.get('qty', 0) or 0),
                'price': float(row.get('price', 0) or 0),
                'curr': row.get('curr', 'CNY'),
                'adjustment': float(row.get('adjustment', 0) or 0)
            }
            
            if db.add_asset(asset):
                count += 1
        
        print(f"Successfully imported {count} records to database")
        
    except Exception as e:
        print(f"Migration failed: {e}")


def migrate_json_to_db():
    """从JSON数据迁移到数据库"""
    
    json_path = config.BASE_DIR / "portfolio.json"
    if not json_path.exists():
        print(f"JSON file not found: {json_path}")
        return
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Found {len(data)} JSON records")
        
        # 导入到数据库
        db = DatabaseManager(str(config.DATABASE_PATH))
        
        count = 0
        for item in data:
            # 处理968开头的基金代码
            code = item['code']
            if code.isdigit() and code.startswith('968'):
                code = f"f_{code}"
            elif code.isdigit() and code.startswith('11'):
                code = f"f_{code}"
            
            asset = {
                'code': code,
                'name': item.get('name', code),
                'qty': float(item.get('qty', 0) or 0),
                'price': float(item.get('price', 0) or 0),
                'curr': item.get('curr', 'CNY'),
                'adjustment': float(item.get('adjustment', 0) or 0)
            }
            
            if db.add_asset(asset):
                count += 1
        
        print(f"Successfully imported {count} records to database")
        
    except Exception as e:
        print(f"Migration failed: {e}")


if __name__ == "__main__":
    migrate_csv_to_db()
    print("\nMigration complete!")