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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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


if __name__ == "__main__":
    unittest.main()
