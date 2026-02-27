import sys
import os

sys.path.insert(0, '/home/ec2-user/portfolio/kona_tool')
os.environ["JWT_SECRET"] = "dummy"

from core.db import db
from datetime import datetime

def run():
    u = 'cd72d1f50d18081db378bc0ff525966c'
    res = db.get_pnl_overview('month', u)
    print("MONTH:", res)
    res_year = db.get_pnl_overview('year', u)
    print("YEAR:", res_year)
    
    # Dump actual snapshot rows to see why!
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT date, total_pnl, day_pnl FROM daily_snapshots WHERE user_id = ? ORDER BY date ASC", (u,))
    print("\nAll snapshots for this user:")
    for r in cur.fetchall():
        print(dict(r))
    conn.close()

if __name__ == '__main__':
    run()
