import sys
import os

sys.path.insert(0, '/home/ec2-user/portfolio/kona_tool')
os.environ["JWT_SECRET"] = "dummy"

from core.db import db

def run():
    u = 'cd72d1f50d18081db378bc0ff525966c'
    res = db.get_market_breakdown_calendar_data('day', u, 2026, 2)
    print("Calendar Total PnL:", res.get('total_pnl'))
    for it in res.get('items', []):
        print(it)

if __name__ == '__main__':
    run()
