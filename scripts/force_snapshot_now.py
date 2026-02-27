import sys
import os
import logging
from datetime import datetime, timezone

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, os.path.join(project_root, "kona_tool"))

import config
try:
    from dotenv import load_dotenv
    env_path = os.path.join(project_root, "kona_tool", ".env")
    load_dotenv(env_path)
except ImportError:
    pass

from core.db import db
from core.snapshot import calculate_portfolio_stats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run():
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT user_id FROM daily_snapshots")
    users = [r[0] for r in cur.fetchall()]
    conn.close()

    for u in users:
        print(f"Recalculating for user: {u}")
        try:
            stats = calculate_portfolio_stats(u)
            db.save_daily_snapshot(stats, u)
            
            # Print the newly calculated stats to see what exactly they are
            print(f"  Result: total_pnl={stats.get('total_pnl', 0)}, day_pnl={stats.get('day_pnl', 0)}")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == '__main__':
    run()
