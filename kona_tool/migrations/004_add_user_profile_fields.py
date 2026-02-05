import sqlite3
import sys
from pathlib import Path

# Add parent dir to path
sys.path.append(str(Path(__file__).parent.parent))
from config import DATABASE_PATH


def migrate():
    print(f"Migrating database: {DATABASE_PATH}")
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    def add_column(table: str, column: str, col_def: str) -> None:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")
            print(f"Added {column} to {table}")
        except Exception as e:
            print(f"{column} might already exist: {e}")

    try:
        # Ensure users table exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                nickname TEXT,
                avatar TEXT,
                register_method TEXT,
                phone TEXT,
                user_number INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')

        add_column('users', 'nickname', 'nickname TEXT')
        add_column('users', 'avatar', 'avatar TEXT')
        add_column('users', 'register_method', 'register_method TEXT')
        add_column('users', 'phone', 'phone TEXT')
        add_column('users', 'user_number', 'user_number INTEGER')
        add_column('users', 'created_at', 'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        add_column('users', 'last_login', 'last_login TIMESTAMP')

        conn.commit()
        print("Migration completed successfully!")
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
