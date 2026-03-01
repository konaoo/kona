import sqlite3

def run():
    try:
        conn = sqlite3.connect('/home/ec2-user/portfolio/kona_tool/portfolio.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT date, total_pnl, day_pnl FROM daily_snapshots WHERE user_id='73bedbc4d43946334368ef09161da2ae' AND date >= '2026-02-24' ORDER BY date ASC")
        rows = cur.fetchall()
        for r in rows:
            print(f"date: {r['date']}, total_pnl: {r['total_pnl']}, day_pnl: {r['day_pnl']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    run()
