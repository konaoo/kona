import sqlite3
import core.auth as auth

conn = sqlite3.connect('portfolio.db')
cursor = conn.cursor()
hashed = auth.hash_password("qq111111")
cursor.execute("INSERT OR REPLACE INTO users (id, username, password_hash) VALUES (?, ?, ?)", ("u_konae", "konae", hashed))
conn.commit()
conn.close()
print("Registered konae")
