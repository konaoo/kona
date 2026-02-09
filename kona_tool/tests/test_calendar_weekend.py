import os
import sys
import importlib.util
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))

tmp_dir = tempfile.TemporaryDirectory()
os.environ["KONA_DATABASE_PATH"] = str(Path(tmp_dir.name) / "test.db")
os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

db_path = KONA_TOOL / "core" / "db.py"
spec = importlib.util.spec_from_file_location("db_module", db_path)
db_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(db_module)


def _insert_snapshot(date, total_pnl, day_pnl, user_id="u1"):
    conn = db_module.db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO daily_snapshots
        (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (date, 0, 1000, 0, 0, 0, total_pnl, day_pnl, user_id),
    )
    conn.commit()
    conn.close()


class CalendarWeekendTests(unittest.TestCase):
    def setUp(self):
        conn = db_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM daily_snapshots")
        conn.commit()
        conn.close()

    def test_day_view_weekend_is_zero(self):
        _insert_snapshot("2026-02-06", 100, 10)
        _insert_snapshot("2026-02-07", 200, 0)
        _insert_snapshot("2026-02-08", 300, 0)
        _insert_snapshot("2026-02-09", 305, 5)

        real_dt = datetime
        with patch.object(db_module, "datetime") as mock_dt:
            mock_dt.now.return_value = real_dt(2026, 2, 9)
            data = db_module.db.get_calendar_data("day", "u1")

        items = {i["label"]: i["pnl"] for i in data["items"]}
        self.assertEqual(items.get("7"), 0)
        self.assertEqual(items.get("8"), 0)

    def test_month_view_ignores_weekend_totals(self):
        _insert_snapshot("2026-02-06", 100, 10)
        _insert_snapshot("2026-02-07", 200, 0)
        _insert_snapshot("2026-02-08", 300, 0)

        real_dt = datetime
        with patch.object(db_module, "datetime") as mock_dt:
            mock_dt.now.return_value = real_dt(2026, 2, 8)
            data = db_module.db.get_calendar_data("month", "u1")

        feb = [i for i in data["items"] if i["label"] == "2月"][0]
        self.assertEqual(feb["pnl"], 100)

    def test_year_view_ignores_weekend_totals(self):
        _insert_snapshot("2026-02-06", 100, 10)
        _insert_snapshot("2026-02-07", 200, 0)
        _insert_snapshot("2026-02-08", 300, 0)

        real_dt = datetime
        with patch.object(db_module, "datetime") as mock_dt:
            mock_dt.now.return_value = real_dt(2026, 2, 8)
            data = db_module.db.get_calendar_data("year", "u1")

        year = [i for i in data["items"] if i["label"] == "2026"][0]
        self.assertEqual(year["pnl"], 100)


if __name__ == "__main__":
    unittest.main()
