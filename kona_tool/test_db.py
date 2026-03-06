import sqlite3
conn = sqlite3.connect('portfolio.db')
cursor = conn.cursor()
cursor.execute("SELECT id, username FROM users")
print(cursor.fetchall())
conn.close()
