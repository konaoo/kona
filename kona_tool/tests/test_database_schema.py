import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))

from core.db import DatabaseManager  # noqa: E402


class DatabaseSchemaTests(unittest.TestCase):
    def test_init_database_still_creates_core_tables_and_indexes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = str(Path(temp_dir) / "schema.db")
            db = DatabaseManager(db_path)
            conn = db.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('portfolio', 'users', 'daily_snapshots', 'ai_credit_ledger')"
            )
            table_names = {row[0] for row in cursor.fetchall()}

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_daily_snapshots_date_user_unique'"
            )
            index_row = cursor.fetchone()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_ai_credit_ledger_user_created'"
            )
            ai_credit_index_row = cursor.fetchone()
            conn.close()

        self.assertEqual(
            table_names,
            {"portfolio", "users", "daily_snapshots", "ai_credit_ledger"},
        )
        self.assertIsNotNone(index_row)
        self.assertIsNotNone(ai_credit_index_row)

    def test_init_database_backfills_single_ledger_history_into_ledger_snapshots(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = str(Path(temp_dir) / "schema.db")
            db = DatabaseManager(db_path)

            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (id, username, password_hash, legacy_needs_password_setup, is_admin, status)
                VALUES ('u_single', 'single_user', 'hash', 0, 0, 'active')
                """
            )
            cursor.execute(
                """
                INSERT INTO investment_ledgers (user_id, name, is_default, sort_order)
                VALUES ('u_single', '唯一账本', 1, 0)
                """
            )
            ledger_id = int(cursor.lastrowid)
            cursor.execute(
                """
                INSERT INTO daily_snapshots
                (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
                VALUES ('2026-03-01', 1500, 1000, 500, 0, 0, 80, 20, 'u_single')
                """
            )
            cursor.execute(
                """
                INSERT INTO daily_snapshots
                (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
                VALUES ('2026-03-02', 1520, 1100, 420, 0, 0, 100, 20, 'u_single')
                """
            )
            conn.commit()
            conn.close()

            db.init_database()

            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT ledger_id, date, total_market_value, total_cost, total_pnl, total_pnl_rate, day_pnl
                FROM ledger_daily_snapshots
                WHERE user_id = 'u_single'
                ORDER BY date ASC
                """
            )
            rows = cursor.fetchall()
            conn.close()

        self.assertEqual(2, len(rows))
        self.assertEqual([ledger_id, ledger_id], [int(row["ledger_id"]) for row in rows])
        self.assertEqual(["2026-03-01", "2026-03-02"], [str(row["date"]) for row in rows])
        self.assertAlmostEqual(1000.0, float(rows[0]["total_market_value"]), places=2)
        self.assertAlmostEqual(1000.0, float(rows[0]["total_cost"]), places=2)
        self.assertAlmostEqual(80.0, float(rows[0]["total_pnl"]), places=2)
        self.assertAlmostEqual(8.0, float(rows[0]["total_pnl_rate"]), places=2)
        self.assertAlmostEqual(20.0, float(rows[0]["day_pnl"]), places=2)

    def test_init_database_does_not_guess_history_for_multi_ledger_user(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = str(Path(temp_dir) / "schema.db")
            db = DatabaseManager(db_path)

            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (id, username, password_hash, legacy_needs_password_setup, is_admin, status)
                VALUES ('u_multi', 'multi_user', 'hash', 0, 0, 'active')
                """
            )
            cursor.execute(
                """
                INSERT INTO investment_ledgers (user_id, name, is_default, sort_order)
                VALUES ('u_multi', '账本一', 1, 0)
                """
            )
            cursor.execute(
                """
                INSERT INTO investment_ledgers (user_id, name, is_default, sort_order)
                VALUES ('u_multi', '账本二', 0, 1)
                """
            )
            cursor.execute(
                """
                INSERT INTO daily_snapshots
                (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
                VALUES ('2026-03-01', 1500, 1000, 500, 0, 0, 80, 20, 'u_multi')
                """
            )
            conn.commit()
            conn.close()

            db.init_database()

            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(1) AS cnt FROM ledger_daily_snapshots WHERE user_id = 'u_multi'"
            )
            row = cursor.fetchone()
            conn.close()

        self.assertEqual(0, int(row["cnt"]))
