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


def _insert_snapshot(
    date,
    total_pnl,
    day_pnl,
    user_id="u1",
    updated_at=None,
):
    conn = db_module.db.get_connection()
    cursor = conn.cursor()
    ts = updated_at or f"{date} 00:00:00"
    cursor.execute(
        """
        INSERT OR REPLACE INTO daily_snapshots
        (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (date, 0, 1000, 0, 0, 0, total_pnl, day_pnl, user_id, ts),
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

    def test_day_view_market_closed_day_does_not_backfill_from_total_pnl(self):
        _insert_snapshot("2026-02-10", 100, 10)
        _insert_snapshot("2026-02-11", 108, 0)
        _insert_snapshot("2026-02-12", 110, 2)

        real_dt = datetime
        with patch.object(db_module, "_is_market_closed_date", create=True) as mock_closed:
            mock_closed.side_effect = lambda date_str: str(date_str) == "2026-02-11"
            with patch.object(db_module, "datetime") as mock_dt:
                mock_dt.now.return_value = real_dt(2026, 2, 12)
                data = db_module.db.get_calendar_data("day", "u1")

        items = {i["label"]: i["pnl"] for i in data["items"]}
        self.assertEqual(items.get("11"), 0)

    def test_day_view_snapshot_closed_time_does_not_backfill_from_total_pnl(self):
        _insert_snapshot("2026-02-10", 100, 10, updated_at="2026-02-10 10:00:00")
        _insert_snapshot("2026-02-11", 108, 0, updated_at="2026-02-11 23:00:00")
        _insert_snapshot("2026-02-12", 110, 2, updated_at="2026-02-12 10:00:00")

        real_dt = datetime
        with patch.object(db_module, "_is_market_closed_date", create=True) as mock_closed:
            mock_closed.return_value = False
            with patch.object(
                db_module,
                "_is_market_closed_at_snapshot_time",
                create=True,
            ) as mock_closed_at_snapshot:
                mock_closed_at_snapshot.side_effect = (
                    lambda ts: str(ts).startswith("2026-02-11")
                )
                with patch.object(db_module, "datetime") as mock_dt:
                    mock_dt.now.return_value = real_dt(2026, 2, 12)
                    data = db_module.db.get_calendar_data("day", "u1")

        items = {i["label"]: i["pnl"] for i in data["items"]}
        self.assertEqual(items.get("11"), 0)

    def test_day_view_keeps_nonzero_when_snapshot_written_at_closed_time(self):
        _insert_snapshot("2026-02-10", 100, 10, updated_at="2026-02-10 10:00:00")
        _insert_snapshot("2026-02-11", 108, 8, updated_at="2026-02-11 23:00:00")
        _insert_snapshot("2026-02-12", 110, 2, updated_at="2026-02-12 10:00:00")

        real_dt = datetime
        with patch.object(db_module, "_is_market_closed_date", create=True) as mock_closed:
            mock_closed.return_value = False
            with patch.object(
                db_module,
                "_is_market_closed_at_snapshot_time",
                create=True,
            ) as mock_closed_at_snapshot:
                mock_closed_at_snapshot.side_effect = (
                    lambda ts: str(ts).startswith("2026-02-11")
                )
                with patch.object(db_module, "datetime") as mock_dt:
                    mock_dt.now.return_value = real_dt(2026, 2, 12)
                    data = db_module.db.get_calendar_data("day", "u1")

        items = {i["label"]: i["pnl"] for i in data["items"]}
        self.assertEqual(items.get("11"), 8)

    def test_day_view_ignores_closed_time_guard_when_snapshot_updated_cross_day(self):
        _insert_snapshot("2026-02-11", 108, 8, updated_at="2026-02-17 23:00:00")

        real_dt = datetime
        with patch.object(db_module, "_is_market_closed_date", create=True) as mock_closed:
            mock_closed.return_value = False
            with patch.object(db_module, "datetime") as mock_dt:
                mock_dt.now.return_value = real_dt(2026, 2, 17)
                data = db_module.db.get_calendar_data("day", "u1")

        items = {i["label"]: i["pnl"] for i in data["items"]}
        self.assertEqual(items.get("11"), 8)

    def test_month_view_ignores_weekend_totals(self):
        _insert_snapshot("2026-02-06", 100, 10)
        _insert_snapshot("2026-02-07", 200, 0)
        _insert_snapshot("2026-02-08", 300, 0)

        real_dt = datetime
        with patch.object(db_module, "datetime") as mock_dt:
            mock_dt.now.return_value = real_dt(2026, 2, 8)
            data = db_module.db.get_calendar_data("month", "u1")

        feb = [i for i in data["items"] if i["label"] == "2月"][0]
        self.assertEqual(feb["pnl"], 10)

    def test_year_view_ignores_weekend_totals(self):
        _insert_snapshot("2026-02-06", 100, 10)
        _insert_snapshot("2026-02-07", 200, 0)
        _insert_snapshot("2026-02-08", 300, 0)

        real_dt = datetime
        with patch.object(db_module, "datetime") as mock_dt:
            mock_dt.now.return_value = real_dt(2026, 2, 8)
            data = db_module.db.get_calendar_data("year", "u1")

        year = [i for i in data["items"] if i["label"] == "2026"][0]
        self.assertEqual(year["pnl"], 10)

    def test_day_view_supports_specific_year_month_and_selectable(self):
        _insert_snapshot("2026-02-06", 100, 10)
        _insert_snapshot("2026-03-06", 120, 20)

        real_dt = datetime
        with patch.object(db_module, "datetime") as mock_dt:
            mock_dt.now.return_value = real_dt(2026, 12, 1)
            data = db_module.db.get_calendar_data("day", "u1", year=2026, month=2)

        self.assertEqual(data["period"]["year"], 2026)
        self.assertEqual(data["period"]["month"], 2)
        self.assertEqual(data["title"], "2026年2月累计")
        self.assertEqual(data["selectable"]["day"]["years"], [2026])
        self.assertEqual(
            data["selectable"]["day"]["months_by_year"].get("2026"),
            [2, 3, 12],
        )

    def test_month_view_supports_specific_year(self):
        _insert_snapshot("2024-12-31", 100, 0)
        _insert_snapshot("2025-01-15", 140, 0)
        _insert_snapshot("2025-03-20", 180, 0)

        real_dt = datetime
        with patch.object(db_module, "datetime") as mock_dt:
            mock_dt.now.return_value = real_dt(2026, 2, 8)
            data = db_module.db.get_calendar_data("month", "u1", year=2025)

        self.assertEqual(data["period"]["year"], 2025)
        self.assertEqual(data["title"], "2025年累计")
        self.assertEqual(len(data["items"]), 12)
        self.assertEqual(data["items"][0]["label"], "1月")

    def test_day_view_current_month_without_snapshot_is_accessible(self):
        _insert_snapshot("2026-02-06", 100, 10)

        real_dt = datetime
        with patch.object(db_module, "datetime") as mock_dt:
            mock_dt.now.return_value = real_dt(2026, 3, 2)
            data = db_module.db.get_calendar_data("day", "u1")

        self.assertEqual(data["period"]["year"], 2026)
        self.assertEqual(data["period"]["month"], 3)
        self.assertNotEqual(data.get("code"), "INVALID_CALENDAR_PERIOD")
        self.assertEqual(data["items"], [])
        self.assertEqual(
            data["selectable"]["day"]["months_by_year"].get("2026"),
            [2, 3],
        )

    def test_day_view_explicit_current_month_without_snapshot_is_accessible(self):
        _insert_snapshot("2026-02-06", 100, 10)

        real_dt = datetime
        with patch.object(db_module, "datetime") as mock_dt:
            mock_dt.now.return_value = real_dt(2026, 3, 2)
            data = db_module.db.get_calendar_data(
                "day",
                "u1",
                year=2026,
                month=3,
            )

        self.assertEqual(data["period"]["year"], 2026)
        self.assertEqual(data["period"]["month"], 3)
        self.assertNotEqual(data.get("code"), "INVALID_CALENDAR_PERIOD")
        self.assertEqual(data["items"], [])

    def test_month_view_current_year_without_snapshot_is_accessible(self):
        _insert_snapshot("2025-12-31", 100, 0)

        real_dt = datetime
        with patch.object(db_module, "datetime") as mock_dt:
            mock_dt.now.return_value = real_dt(2026, 3, 2)
            data = db_module.db.get_calendar_data("month", "u1", year=2026)

        self.assertEqual(data["period"]["year"], 2026)
        self.assertNotEqual(data.get("code"), "INVALID_CALENDAR_PERIOD")
        self.assertEqual(data["selectable"]["month"]["years"], [2025, 2026])
        self.assertEqual(len(data["items"]), 3)
        self.assertEqual(data["total_pnl"], 0.0)

    def test_selected_empty_period_returns_invalid_code(self):
        _insert_snapshot("2026-02-06", 100, 10)

        real_dt = datetime
        with patch.object(db_module, "datetime") as mock_dt:
            mock_dt.now.return_value = real_dt(2026, 2, 8)
            data = db_module.db.get_calendar_data("day", "u1", year=2026, month=12)

        self.assertEqual(data.get("code"), "INVALID_CALENDAR_PERIOD")


if __name__ == "__main__":
    unittest.main()
