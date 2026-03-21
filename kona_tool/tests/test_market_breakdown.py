import os
import sys
import tempfile
import subprocess
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))

tmp_dir = tempfile.TemporaryDirectory()
os.environ["KONA_DATABASE_PATH"] = str(Path(tmp_dir.name) / "test_market_breakdown.db")
os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

import app as app_module  # noqa: E402


def _safe_delete(cursor, table_name: str):
    try:
        cursor.execute(f"DELETE FROM {table_name}")
    except Exception:
        pass


class MarketBreakdownTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app_module.app.testing = True
        cls.client = app_module.app.test_client()

    def setUp(self):
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        _safe_delete(cursor, "daily_snapshot_market_breakdowns")
        _safe_delete(cursor, "daily_snapshots")
        _safe_delete(cursor, "transactions")
        _safe_delete(cursor, "portfolio")
        conn.commit()
        conn.close()

    def _insert_snapshot(self, date_str: str, total_pnl: float, day_pnl: float, user_id: str = ""):
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id, updated_at)
            VALUES (?, 1000, 1000, 0, 0, 0, ?, ?, ?, ?)
            """,
            (date_str, total_pnl, day_pnl, user_id, f"{date_str} 23:00:00"),
        )
        conn.commit()
        conn.close()

    def test_save_market_breakdown_exact_rows(self):
        ok = app_module.db.save_daily_snapshot_market_breakdown(
            date_str="2026-02-17",
            day_pnl_by_market={"a": 100.0, "hk": 100.0, "us": 180.0, "fund": 20.0},
            total_day_pnl=400.0,
            user_id="u1",
            source="exact",
            confidence=1.0,
        )
        self.assertTrue(ok)

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT market, day_pnl, source, confidence
            FROM daily_snapshot_market_breakdowns
            WHERE user_id = ? AND date = ?
            ORDER BY market ASC
            """,
            ("u1", "2026-02-17"),
        )
        rows = cursor.fetchall()
        conn.close()
        self.assertEqual(len(rows), 5)
        by_market = {r["market"]: float(r["day_pnl"]) for r in rows}
        self.assertAlmostEqual(by_market["a"], 100.0, places=2)
        self.assertAlmostEqual(by_market["hk"], 100.0, places=2)
        self.assertAlmostEqual(by_market["us"], 180.0, places=2)
        self.assertAlmostEqual(by_market["fund"], 20.0, places=2)
        self.assertAlmostEqual(by_market["unallocated"], 0.0, places=2)

    def test_realized_pnl_by_date_numeric_hk_code_maps_to_hk_market(self):
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO transactions (time, code, name, type, price, qty, amount, pnl, user_id)
            VALUES (?, ?, ?, '减仓', ?, ?, ?, ?, ?)
            """,
            ("2026-02-18 10:00:00", "00700", "腾讯控股", 500.0, 1.0, 500.0, 123.45, "u_hk"),
        )
        conn.commit()
        conn.close()

        by_market = app_module.db.get_realized_pnl_by_date("2026-02-18", user_id="u_hk")
        self.assertAlmostEqual(float(by_market.get("hk") or 0), 123.45, places=2)
        self.assertAlmostEqual(float(by_market.get("a") or 0), 0.0, places=2)

    def test_analysis_calendar_market_breakdown_endpoint(self):
        self._insert_snapshot("2026-02-17", total_pnl=100.0, day_pnl=400.0, user_id="")
        app_module.db.save_daily_snapshot_market_breakdown(
            date_str="2026-02-17",
            day_pnl_by_market={"a": 100.0, "hk": 100.0, "us": 100.0, "fund": 100.0},
            total_day_pnl=400.0,
            user_id="",
            source="exact",
            confidence=1.0,
        )

        resp = self.client.get("/api/analysis/calendar/market_breakdown?type=day&year=2026&month=2")
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json() or {}
        self.assertEqual(body.get("time_type"), "day")
        self.assertEqual(int(body.get("year")), 2026)
        self.assertEqual(int(body.get("month")), 2)
        items = body.get("items") or []
        target = next((x for x in items if x.get("date") == "2026-02-17"), None)
        self.assertIsNotNone(target)
        self.assertEqual(target.get("source"), "exact")
        markets = target.get("markets") or {}
        self.assertAlmostEqual(float(markets.get("a") or 0), 100.0, places=2)
        self.assertAlmostEqual(float(markets.get("hk") or 0), 100.0, places=2)
        self.assertAlmostEqual(float(markets.get("us") or 0), 100.0, places=2)
        self.assertAlmostEqual(float(markets.get("fund") or 0), 100.0, places=2)
        self.assertAlmostEqual(float(markets.get("unallocated") or 0), 0.0, places=2)

    def test_analysis_calendar_market_breakdown_missing_source(self):
        self._insert_snapshot("2026-02-18", total_pnl=120.0, day_pnl=50.0, user_id="")
        resp = self.client.get("/api/analysis/calendar/market_breakdown?type=day&year=2026&month=2")
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json() or {}
        items = body.get("items") or []
        target = next((x for x in items if x.get("date") == "2026-02-18"), None)
        self.assertIsNotNone(target)
        self.assertEqual(target.get("source"), "missing")
        markets = target.get("markets") or {}
        self.assertIsNone(markets.get("a"))
        self.assertIsNone(markets.get("hk"))
        self.assertIsNone(markets.get("us"))
        self.assertIsNone(markets.get("fund"))
        self.assertIsNone(markets.get("unallocated"))

    def test_main_calendar_ignores_breakdown_only_date(self):
        self._insert_snapshot("2026-02-18", total_pnl=120.0, day_pnl=50.0, user_id="")
        app_module.db.save_daily_snapshot_market_breakdown(
            date_str="2026-02-19",
            day_pnl_by_market={"a": 10.0, "hk": 20.0, "us": 30.0, "fund": 40.0},
            total_day_pnl=100.0,
            user_id="",
            source="exact",
            confidence=1.0,
        )

        resp = self.client.get("/api/analysis/calendar?type=day&year=2026&month=2")
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json() or {}
        items = body.get("items") or []
        self.assertFalse(any(str(item.get("label")) == "2-19" for item in items))

    def test_backfill_script_estimated_with_unallocated(self):
        self._insert_snapshot("2026-02-18", total_pnl=120.0, day_pnl=50.0, user_id="u_est")
        script_path = KONA_TOOL / "scripts" / "backfill_market_breakdown.py"
        self.assertTrue(script_path.exists())

        proc = subprocess.run(
            [
                sys.executable,
                str(script_path),
                "--db-path",
                str(app_module.db.db_path),
                "--start-date",
                "2026-02-18",
                "--end-date",
                "2026-02-18",
                "--user-id",
                "u_est",
                "--apply",
            ],
            cwd=str(KONA_TOOL),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, msg=f"stdout={proc.stdout}\nstderr={proc.stderr}")

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT day_pnl, source, confidence
            FROM daily_snapshot_market_breakdowns
            WHERE user_id = ? AND date = ? AND market = 'unallocated'
            """,
            ("u_est", "2026-02-18"),
        )
        row = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(row)
        self.assertAlmostEqual(float(row["day_pnl"]), 50.0, places=2)
        self.assertEqual(str(row["source"]), "estimated")
        self.assertLessEqual(float(row["confidence"]), 0.5)


if __name__ == "__main__":
    unittest.main()
