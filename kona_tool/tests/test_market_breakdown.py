import os
import sys
import tempfile
import subprocess
import json
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
        _safe_delete(cursor, "ledger_daily_snapshot_market_breakdowns")
        _safe_delete(cursor, "ledger_daily_snapshots")
        _safe_delete(cursor, "investment_ledgers")
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

    def test_realized_pnl_by_date_prefers_stored_effective_date_and_market(self):
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO transactions (time, code, name, type, price, qty, amount, pnl, market, effective_date, user_id)
            VALUES (?, ?, ?, '减仓', ?, ?, ?, ?, ?, ?, ?)
            """,
            ("2026-02-18 23:30:00", "gb_aapl", "苹果", 200.0, 1.0, 200.0, 50.0, "us", "2026-02-17", "u_us"),
        )
        conn.commit()
        conn.close()

        by_market = app_module.db.get_realized_pnl_by_date("2026-02-17", user_id="u_us")
        self.assertAlmostEqual(float(by_market.get("us") or 0), 50.0, places=2)
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

    def test_partial_market_backfill_keeps_daily_total_stable(self):
        user_id = "u_partial_total"
        self._insert_snapshot("2026-02-18", total_pnl=120.0, day_pnl=50.0, user_id=user_id)

        ok = app_module.db.save_daily_snapshot_market_breakdown_partial(
            date_str="2026-02-18",
            market_updates={"fund": 20.0},
            user_id=user_id,
            snapshot_date="2026-02-19",
            source="backfill",
            confidence=1.0,
        )
        self.assertTrue(ok)
        self.assertTrue(app_module.db.sync_daily_snapshot_day_pnl_from_breakdown("2026-02-18", user_id=user_id))

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT market, day_pnl
            FROM daily_snapshot_market_breakdowns
            WHERE user_id = ? AND date = ?
            ORDER BY market
            """,
            (user_id, "2026-02-18"),
        )
        rows = cursor.fetchall()
        cursor.execute(
            """
            SELECT day_pnl
            FROM daily_snapshots
            WHERE user_id = ? AND date = ?
            """,
            (user_id, "2026-02-18"),
        )
        snapshot_row = cursor.fetchone()
        conn.close()

        self.assertEqual(len(rows), 5)
        by_market = {str(row["market"]): float(row["day_pnl"] or 0.0) for row in rows}
        self.assertAlmostEqual(by_market["a"], 0.0, places=2)
        self.assertAlmostEqual(by_market["hk"], 0.0, places=2)
        self.assertAlmostEqual(by_market["us"], 0.0, places=2)
        self.assertAlmostEqual(by_market["fund"], 20.0, places=2)
        self.assertAlmostEqual(by_market["unallocated"], 30.0, places=2)
        self.assertIsNotNone(snapshot_row)
        self.assertAlmostEqual(float(snapshot_row["day_pnl"] or 0.0), 50.0, places=2)

    def test_ledger_partial_backfill_aggregates_without_zeroing_missing_markets(self):
        user_id = "u_ledger_partial"
        ledger = app_module.db.create_ledger(user_id, "主账本")
        ledger_id = int(ledger["ledger_id"])

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO ledger_daily_snapshots
            (user_id, ledger_id, date, total_market_value, total_cost, total_pnl, total_pnl_rate, day_pnl, holdings_count)
            VALUES (?, ?, '2026-02-18', 1000, 900, 100, 11.11, 50, 1)
            """,
            (user_id, ledger_id),
        )
        cursor.execute(
            """
            INSERT INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id, updated_at)
            VALUES ('2026-02-18', 1000, 1000, 0, 0, 0, 100, 50, ?, '2026-02-18 23:00:00')
            """,
            (user_id,),
        )
        conn.commit()
        conn.close()

        ok = app_module.db.save_ledger_daily_snapshot_market_breakdown_partial(
            user_id=user_id,
            ledger_id=ledger_id,
            date_str="2026-02-18",
            market_updates={"fund": 20.0},
            snapshot_date="2026-02-19",
            source="backfill",
            confidence=1.0,
        )
        self.assertTrue(ok)
        self.assertTrue(
            app_module.db.aggregate_daily_snapshot_market_breakdown_from_ledgers(
                user_id=user_id,
                date_str="2026-02-18",
                snapshot_date="2026-02-19",
                source="backfill",
            )
        )
        self.assertTrue(app_module.db.sync_daily_snapshot_day_pnl_from_breakdown("2026-02-18", user_id=user_id))

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT market, day_pnl
            FROM ledger_daily_snapshot_market_breakdowns
            WHERE user_id = ? AND ledger_id = ? AND date = ?
            ORDER BY market
            """,
            (user_id, ledger_id, "2026-02-18"),
        )
        ledger_rows = cursor.fetchall()
        cursor.execute(
            """
            SELECT market, day_pnl
            FROM daily_snapshot_market_breakdowns
            WHERE user_id = ? AND date = ?
            ORDER BY market
            """,
            (user_id, "2026-02-18"),
        )
        global_rows = cursor.fetchall()
        cursor.execute(
            """
            SELECT day_pnl
            FROM daily_snapshots
            WHERE user_id = ? AND date = ?
            """,
            (user_id, "2026-02-18"),
        )
        snapshot_row = cursor.fetchone()
        conn.close()

        self.assertEqual(len(ledger_rows), 5)
        self.assertEqual(len(global_rows), 5)
        ledger_by_market = {str(row["market"]): float(row["day_pnl"] or 0.0) for row in ledger_rows}
        global_by_market = {str(row["market"]): float(row["day_pnl"] or 0.0) for row in global_rows}
        self.assertAlmostEqual(ledger_by_market["fund"], 20.0, places=2)
        self.assertAlmostEqual(ledger_by_market["unallocated"], 30.0, places=2)
        self.assertAlmostEqual(global_by_market["fund"], 20.0, places=2)
        self.assertAlmostEqual(global_by_market["unallocated"], 30.0, places=2)
        self.assertIsNotNone(snapshot_row)
        self.assertAlmostEqual(float(snapshot_row["day_pnl"] or 0.0), 50.0, places=2)

    def test_save_single_market_breakdown_row_does_not_rebalance_other_markets(self):
        user_id = "u_single_market"
        self._insert_snapshot("2026-03-03", total_pnl=100.0, day_pnl=50.0, user_id=user_id)
        ok = app_module.db.save_daily_snapshot_market_breakdown(
            date_str="2026-03-03",
            day_pnl_by_market={"a": 10.0, "hk": 20.0, "us": 30.0, "fund": 40.0},
            total_day_pnl=100.0,
            user_id=user_id,
            source="exact",
            confidence=1.0,
        )
        self.assertTrue(ok)

        ok = app_module.db.save_daily_snapshot_market_breakdown_row(
            date_str="2026-03-03",
            market="fund",
            day_pnl=25.0,
            user_id=user_id,
            snapshot_date="2026-03-03",
            source="manual_fix",
            confidence=1.0,
            meta_json='{"reason":"test"}',
        )
        self.assertTrue(ok)
        self.assertTrue(app_module.db.sync_daily_snapshot_day_pnl_from_breakdown("2026-03-03", user_id=user_id))

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT market, day_pnl, source
            FROM daily_snapshot_market_breakdowns
            WHERE user_id = ? AND date = ?
            ORDER BY market
            """,
            (user_id, "2026-03-03"),
        )
        rows = cursor.fetchall()
        cursor.execute(
            """
            SELECT day_pnl
            FROM daily_snapshots
            WHERE user_id = ? AND date = ?
            """,
            (user_id, "2026-03-03"),
        )
        snapshot_row = cursor.fetchone()
        conn.close()

        by_market = {str(row["market"]): float(row["day_pnl"] or 0.0) for row in rows}
        by_source = {str(row["market"]): str(row["source"] or "") for row in rows}
        self.assertAlmostEqual(by_market["a"], 10.0, places=2)
        self.assertAlmostEqual(by_market["hk"], 20.0, places=2)
        self.assertAlmostEqual(by_market["us"], 30.0, places=2)
        self.assertAlmostEqual(by_market["fund"], 25.0, places=2)
        self.assertAlmostEqual(by_market["unallocated"], 0.0, places=2)
        self.assertEqual(by_source["fund"], "manual_fix")
        self.assertIsNotNone(snapshot_row)
        self.assertAlmostEqual(float(snapshot_row["day_pnl"] or 0.0), 85.0, places=2)

    def test_rebuild_fund_breakdown_script_replaces_fund_row_and_syncs_day_total(self):
        user_id = "u_rebuild_fund"
        self._insert_snapshot("2026-03-03", total_pnl=100.0, day_pnl=100.0, user_id=user_id)
        ok = app_module.db.save_daily_snapshot_market_breakdown(
            date_str="2026-03-03",
            day_pnl_by_market={"a": 10.0, "hk": 20.0, "us": 30.0, "fund": 40.0},
            total_day_pnl=100.0,
            user_id=user_id,
            source="repair",
            confidence=1.0,
        )
        self.assertTrue(ok)

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO portfolio
            (code, name, qty, price, curr, asset_type, user_id, ledger_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            """,
            ("f_110018", "测试基金", 100.0, 1.0, "CNY", "fund", user_id),
        )
        conn.commit()
        conn.close()

        nav_file = Path(tmp_dir.name) / "fund_navs.json"
        nav_file.write_text(
            json.dumps(
                {
                    "funds": {
                        "f_110018": {
                            "currency": "CNY",
                            "navs": {
                                "2026-03-02": 1.00,
                                "2026-03-03": 1.20,
                            },
                        }
                    }
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        script_path = KONA_TOOL / "scripts" / "rebuild_fund_breakdown_from_navs.py"
        self.assertTrue(script_path.exists())
        proc = subprocess.run(
            [
                sys.executable,
                str(script_path),
                "--db-path",
                str(app_module.db.db_path),
                "--user-id",
                user_id,
                "--start-date",
                "2026-03-03",
                "--end-date",
                "2026-03-03",
                "--nav-file",
                str(nav_file),
                "--apply",
                "--sync-day-pnl",
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
            SELECT day_pnl, source
            FROM daily_snapshot_market_breakdowns
            WHERE user_id = ? AND date = ? AND market = 'fund'
            """,
            (user_id, "2026-03-03"),
        )
        fund_row = cursor.fetchone()
        cursor.execute(
            """
            SELECT day_pnl
            FROM daily_snapshots
            WHERE user_id = ? AND date = ?
            """,
            (user_id, "2026-03-03"),
        )
        snapshot_row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(fund_row)
        self.assertAlmostEqual(float(fund_row["day_pnl"] or 0.0), 20.0, places=2)
        self.assertEqual(str(fund_row["source"] or ""), "manual_fix")
        self.assertIsNotNone(snapshot_row)
        self.assertAlmostEqual(float(snapshot_row["day_pnl"] or 0.0), 80.0, places=2)

    def test_rebuild_fund_breakdown_script_skips_ledger_total_sync_when_breakdown_incomplete(self):
        user_id = "u_rebuild_fund_ledger"
        ledger = app_module.db.create_ledger(user_id, "主账本")
        ledger_id = int(ledger["ledger_id"])
        self._insert_snapshot("2026-03-03", total_pnl=100.0, day_pnl=100.0, user_id=user_id)

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO ledger_daily_snapshots
            (user_id, ledger_id, date, total_market_value, total_cost, total_pnl, total_pnl_rate, day_pnl, holdings_count)
            VALUES (?, ?, '2026-03-03', 1000, 900, 100, 11.11, 123.0, 1)
            """,
            (user_id, ledger_id),
        )
        cursor.execute(
            """
            INSERT INTO portfolio
            (code, name, qty, price, curr, asset_type, user_id, ledger_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("f_110018", "测试基金", 100.0, 1.0, "CNY", "fund", user_id, ledger_id),
        )
        conn.commit()
        conn.close()

        nav_file = Path(tmp_dir.name) / "fund_navs_ledger.json"
        nav_file.write_text(
            json.dumps(
                {
                    "funds": {
                        "f_110018": {
                            "currency": "CNY",
                            "navs": {
                                "2026-03-02": 1.00,
                                "2026-03-03": 1.20,
                            },
                        }
                    }
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        script_path = KONA_TOOL / "scripts" / "rebuild_fund_breakdown_from_navs.py"
        proc = subprocess.run(
            [
                sys.executable,
                str(script_path),
                "--db-path",
                str(app_module.db.db_path),
                "--user-id",
                user_id,
                "--ledger-id",
                str(ledger_id),
                "--start-date",
                "2026-03-03",
                "--end-date",
                "2026-03-03",
                "--nav-file",
                str(nav_file),
                "--apply",
                "--sync-day-pnl",
            ],
            cwd=str(KONA_TOOL),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, msg=f"stdout={proc.stdout}\nstderr={proc.stderr}")
        self.assertIn("跳过账本 day_pnl 同步", proc.stdout)

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT day_pnl
            FROM ledger_daily_snapshots
            WHERE user_id = ? AND ledger_id = ? AND date = ?
            """,
            (user_id, ledger_id, "2026-03-03"),
        )
        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertAlmostEqual(float(row["day_pnl"] or 0.0), 123.0, places=2)


if __name__ == "__main__":
    unittest.main()
