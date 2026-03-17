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
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('portfolio', 'users', 'daily_snapshots')"
            )
            table_names = {row[0] for row in cursor.fetchall()}

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_daily_snapshots_date_user_unique'"
            )
            index_row = cursor.fetchone()
            conn.close()

        self.assertEqual(table_names, {"portfolio", "users", "daily_snapshots"})
        self.assertIsNotNone(index_row)
