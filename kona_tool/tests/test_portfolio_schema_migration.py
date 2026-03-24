import sqlite3
import tempfile
import unittest
from pathlib import Path

import os
import sys

ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))
os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

from core.db import DatabaseManager  # noqa: E402


class PortfolioSchemaMigrationTests(unittest.TestCase):
    def test_init_creates_portfolio_adjustment_ledger_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "ledger.db"
            db = DatabaseManager(str(db_path))

            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='portfolio_adjustment_ledger'"
            )
            table = cursor.fetchone()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='portfolio_legacy_adjustment_states'"
            )
            state_table = cursor.fetchone()
            cursor.execute("PRAGMA index_list(portfolio_adjustment_ledger)")
            indexes = [str(row[1]) for row in cursor.fetchall()]
            cursor.execute("PRAGMA index_list(portfolio_legacy_adjustment_states)")
            state_indexes = [str(row[1]) for row in cursor.fetchall()]
            conn.close()

            self.assertIsNotNone(table)
            self.assertIsNotNone(state_table)
            self.assertIn("idx_portfolio_adjustment_ledger_user_code", indexes)
            self.assertIn("idx_portfolio_legacy_adjustment_states_ignore", state_indexes)

    def test_old_code_unique_schema_migrates_to_user_scoped_unique(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "legacy.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE portfolio (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    qty REAL NOT NULL,
                    price REAL NOT NULL,
                    curr TEXT NOT NULL DEFAULT 'CNY',
                    adjustment REAL DEFAULT 0.0,
                    asset_type TEXT DEFAULT 'a',
                    user_id TEXT,
                    created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
                    updated_at TIMESTAMP DEFAULT (datetime('now','localtime'))
                )
                """
            )
            cursor.execute(
                """
                INSERT INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("gb_tsla", "Tesla", 1.0, 200.0, "USD", 0.0, "us", "u_a"),
            )
            conn.commit()
            conn.close()

            db = DatabaseManager(str(db_path))

            ok_a = db.add_asset(
                {
                    "code": "gb_tsla",
                    "name": "Tesla",
                    "qty": 2.0,
                    "price": 210.0,
                    "curr": "USD",
                    "adjustment": 0.0,
                    "asset_type": "us",
                },
                user_id="u_a",
            )
            ok_b = db.add_asset(
                {
                    "code": "gb_tsla",
                    "name": "Tesla",
                    "qty": 1.0,
                    "price": 220.0,
                    "curr": "USD",
                    "adjustment": 0.0,
                    "asset_type": "us",
                },
                user_id="u_b",
            )

            self.assertTrue(ok_a)
            self.assertTrue(ok_b)

            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(1) AS c FROM portfolio WHERE code = ?",
                ("gb_tsla",),
            )
            count = int(cursor.fetchone()["c"] or 0)
            conn.close()
            self.assertEqual(count, 2)

    def test_add_asset_default_preserves_existing_legacy_adjustment(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "preserve_adjustment.db"
            db = DatabaseManager(str(db_path))

            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("sh600000", "浦发银行", 10.0, 10.0, "CNY", 88.8, "a", "u_keep"),
            )
            conn.commit()
            conn.close()

            ok = db.add_asset(
                {
                    "code": "sh600000",
                    "name": "浦发银行",
                    "qty": 12.0,
                    "price": 11.0,
                    "curr": "CNY",
                    "adjustment": 999.0,
                    "asset_type": "a",
                },
                user_id="u_keep",
            )
            self.assertTrue(ok)

            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT qty, price, adjustment FROM portfolio WHERE code = ? AND user_id = ?",
                ("sh600000", "u_keep"),
            )
            row = cursor.fetchone()
            conn.close()

            self.assertAlmostEqual(float(row["qty"] or 0.0), 12.0, places=6)
            self.assertAlmostEqual(float(row["price"] or 0.0), 11.0, places=6)
            self.assertAlmostEqual(float(row["adjustment"] or 0.0), 88.8, places=6)

    def test_add_asset_requires_explicit_opt_in_to_write_legacy_adjustment(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "explicit_adjustment.db"
            db = DatabaseManager(str(db_path))

            ok = db.add_asset(
                {
                    "code": "sh600001",
                    "name": "测试股票",
                    "qty": 5.0,
                    "price": 9.0,
                    "curr": "CNY",
                    "adjustment": 123.0,
                    "asset_type": "a",
                },
                user_id="u_new",
                allow_legacy_adjustment_write=True,
            )
            self.assertTrue(ok)

            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT adjustment FROM portfolio WHERE code = ? AND user_id = ?",
                ("sh600001", "u_new"),
            )
            row = cursor.fetchone()
            conn.close()

            self.assertAlmostEqual(float(row["adjustment"] or 0.0), 123.0, places=6)


if __name__ == "__main__":
    unittest.main()
