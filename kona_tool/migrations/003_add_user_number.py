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
    
    try:
        # Add user_number column
        cursor.execute("ALTER TABLE users ADD COLUMN user_number INTEGER")
        print("Added user_number column")
    except Exception as e:
        print(f"Column might already exist: {e}")

    # Assign numbers to existing users
    cursor.execute("SELECT id FROM users ORDER BY created_at")
    users = cursor.fetchall()
    
    start_num = 10001
    count = 0
    for idx, (user_id,) in enumerate(users):
        # Only update if null
        cursor.execute("SELECT user_number FROM users WHERE id = ?", (user_id,))
        if cursor.fetchone()[0] is None:
            num = start_num + idx
            cursor.execute("UPDATE users SET user_number = ? WHERE id = ?", (num, user_id))
            print(f"Assigned {num} to {user_id}")
            count += 1
            
    conn.commit()
    conn.close()
    print(f"Migration complete. Updated {count} users.")

if __name__ == "__main__":
    migrate()
