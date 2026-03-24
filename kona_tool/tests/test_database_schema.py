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

    def test_init_database_creates_default_ledger_for_snapshot_only_user(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = str(Path(temp_dir) / "schema.db")
            db = DatabaseManager(db_path)

            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (id, username, password_hash, legacy_needs_password_setup, is_admin, status)
                VALUES ('u_snapshot_only', 'snapshot_only_user', 'hash', 0, 0, 'active')
                """
            )
            cursor.execute(
                """
                INSERT INTO daily_snapshots
                (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
                VALUES ('2026-03-01', 1500, 1000, 500, 0, 0, 80, 20, 'u_snapshot_only')
                """
            )
            cursor.execute(
                """
                INSERT INTO daily_snapshots
                (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
                VALUES ('2026-03-02', 1520, 1100, 420, 0, 0, 100, 20, 'u_snapshot_only')
                """
            )
            conn.commit()
            conn.close()

            db.init_database()

            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, is_default
                FROM investment_ledgers
                WHERE user_id = 'u_snapshot_only'
                ORDER BY id ASC
                """
            )
            ledgers = cursor.fetchall()
            cursor.execute(
                """
                SELECT ledger_id, date
                FROM ledger_daily_snapshots
                WHERE user_id = 'u_snapshot_only'
                ORDER BY date ASC
                """
            )
            rows = cursor.fetchall()
            conn.close()

        self.assertEqual(1, len(ledgers))
        self.assertEqual(1, int(ledgers[0]["is_default"]))
        self.assertEqual(2, len(rows))
        self.assertEqual([str(row["date"]) for row in rows], ["2026-03-01", "2026-03-02"])
        self.assertEqual([int(row["ledger_id"]) for row in rows], [int(ledgers[0]["id"]), int(ledgers[0]["id"])])

    def test_init_database_backfills_default_ledger_history_before_non_default_created(self):
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
            default_ledger_id = int(cursor.lastrowid)
            cursor.execute(
                """
                INSERT INTO investment_ledgers (user_id, name, is_default, sort_order, created_at)
                VALUES ('u_multi', '账本二', 0, 1, '2026-03-10 09:00:00')
                """
            )
            second_ledger_id = int(cursor.lastrowid)
            cursor.execute(
                """
                INSERT INTO daily_snapshots
                (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
                VALUES ('2026-03-01', 1500, 1000, 500, 0, 0, 80, 20, 'u_multi')
                """
            )
            cursor.execute(
                """
                INSERT INTO daily_snapshots
                (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
                VALUES ('2026-03-12', 1520, 1100, 420, 0, 0, 100, 20, 'u_multi')
                """
            )
            conn.commit()
            conn.close()

            db.init_database()

            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT ledger_id, date
                FROM ledger_daily_snapshots
                WHERE user_id = 'u_multi'
                ORDER BY date ASC, ledger_id ASC
                """
            )
            rows = cursor.fetchall()
            conn.close()

        self.assertEqual(1, len(rows))
        self.assertEqual(default_ledger_id, int(rows[0]["ledger_id"]))
        self.assertEqual("2026-03-01", str(rows[0]["date"]))
        self.assertNotEqual(second_ledger_id, int(rows[0]["ledger_id"]))

    def test_init_database_stops_backfill_once_non_default_has_historical_activity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = str(Path(temp_dir) / "schema.db")
            db = DatabaseManager(db_path)

            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (id, username, password_hash, legacy_needs_password_setup, is_admin, status)
                VALUES ('u_multi_active', 'multi_active_user', 'hash', 0, 0, 'active')
                """
            )
            cursor.execute(
                """
                INSERT INTO investment_ledgers (user_id, name, is_default, sort_order)
                VALUES ('u_multi_active', '默认账本', 1, 0)
                """
            )
            default_ledger_id = int(cursor.lastrowid)
            cursor.execute(
                """
                INSERT INTO investment_ledgers (user_id, name, is_default, sort_order, created_at)
                VALUES ('u_multi_active', '副账本', 0, 1, '2026-03-10 09:00:00')
                """
            )
            second_ledger_id = int(cursor.lastrowid)
            cursor.execute(
                """
                INSERT INTO transactions
                (time, code, name, type, price, qty, amount, pnl, user_id, ledger_id)
                VALUES ('2026-03-01 10:00:00', 'sh600000', '测试', 'buy', 10, 1, 10, 0, 'u_multi_active', ?)
                """,
                (second_ledger_id,),
            )
            cursor.execute(
                """
                INSERT INTO daily_snapshots
                (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
                VALUES ('2026-02-28', 1400, 900, 500, 0, 0, 60, 10, 'u_multi_active')
                """
            )
            cursor.execute(
                """
                INSERT INTO daily_snapshots
                (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
                VALUES ('2026-03-01', 1410, 910, 500, 0, 0, 70, 10, 'u_multi_active')
                """
            )
            conn.commit()
            conn.close()

            db.init_database()

            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT ledger_id, date
                FROM ledger_daily_snapshots
                WHERE user_id = 'u_multi_active'
                ORDER BY date ASC, ledger_id ASC
                """
            )
            rows = cursor.fetchall()
            conn.close()

        self.assertEqual(1, len(rows))
        self.assertEqual(default_ledger_id, int(rows[0]["ledger_id"]))
        self.assertEqual("2026-02-28", str(rows[0]["date"]))

    def test_init_database_cleans_orphan_ledger_snapshots(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = str(Path(temp_dir) / "schema.db")
            db = DatabaseManager(db_path)

            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (id, username, password_hash, legacy_needs_password_setup, is_admin, status)
                VALUES ('u_orphan', 'orphan_user', 'hash', 0, 0, 'active')
                """
            )
            cursor.execute(
                """
                INSERT INTO investment_ledgers (user_id, name, is_default, sort_order)
                VALUES ('u_orphan', '待删除账本', 0, 0)
                """
            )
            ledger_id = int(cursor.lastrowid)
            cursor.execute(
                """
                INSERT INTO ledger_daily_snapshots
                (user_id, ledger_id, date, total_market_value, total_cost, total_pnl, total_pnl_rate, day_pnl, holdings_count)
                VALUES ('u_orphan', ?, '2026-03-22', 100.0, 100.0, 5.0, 5.0, 5.0, 1)
                """,
                (ledger_id,),
            )
            cursor.execute(
                "DELETE FROM investment_ledgers WHERE id = ?",
                (ledger_id,),
            )
            conn.commit()
            conn.close()

            db.init_database()

            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(1) AS cnt FROM ledger_daily_snapshots WHERE user_id = 'u_orphan' AND ledger_id = ?",
                (ledger_id,),
            )
            row = cursor.fetchone()
            conn.close()

        self.assertEqual(0, int(row["cnt"]))
