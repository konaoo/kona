import os
import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))

_tmp_dir = tempfile.TemporaryDirectory()
os.environ["KONA_DATABASE_PATH"] = str(Path(_tmp_dir.name) / "test_rebind.db")
os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

import app as app_module  # noqa: E402


def _seed_user(user_id: str, username: str, is_admin: int = 0):
    conn = app_module.db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO users (id, username, password_hash, legacy_needs_password_setup, is_admin, status)
        VALUES (?, ?, ?, 0, ?, 'active')
        """,
        (user_id, username, "scrypt$16384$8$1$U0FMVA==$SEFTSA==", is_admin),
    )
    conn.commit()
    conn.close()


class DataRebindTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app_module.app.testing = True
        cls.client = app_module.app.test_client()

    def setUp(self):
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        for t in ["portfolio", "transactions", "cash_assets", "other_assets", "liabilities", "daily_snapshots", "users"]:
            cursor.execute(f"DELETE FROM {t}")
        conn.commit()
        conn.close()

    def test_preview_and_execute_rebind(self):
        _seed_user("u_admin", "admin_user", is_admin=1)
        _seed_user("u_target", "target_user", is_admin=0)
        token = app_module.generate_token("u_admin", "admin_user")
        headers = {"Authorization": f"Bearer {token}"}

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO cash_assets (name, amount, curr, user_id) VALUES (?, ?, ?, ?)",
            ("现金A", 100.0, "CNY", ""),
        )
        cursor.execute(
            "INSERT INTO other_assets (name, amount, curr, user_id) VALUES (?, ?, ?, ?)",
            ("其他A", 50.0, "CNY", "u_legacy"),
        )
        cursor.execute(
            """
            INSERT INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES (?, 10, 2, 8, 0, 0, 1, 1, ?)
            """,
            ("2026-02-12", ""),
        )
        conn.commit()
        conn.close()

        preview = self.client.get(
            "/api/admin/data/rebind/preview?target_user_id=u_target",
            headers=headers,
        )
        self.assertEqual(preview.status_code, 200)
        p = preview.get_json()
        self.assertGreater(p.get("total", 0), 0)

        execute = self.client.post(
            "/api/admin/data/rebind/execute",
            headers=headers,
            json={"target_user_id": "u_target"},
        )
        self.assertEqual(execute.status_code, 200)
        result = execute.get_json().get("result", {})
        self.assertGreater(result.get("total", 0), 0)

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(1) AS c FROM cash_assets WHERE user_id = ?", ("u_target",))
        cash_count = int(cursor.fetchone()["c"])
        cursor.execute("SELECT COUNT(1) AS c FROM other_assets WHERE user_id = ?", ("u_target",))
        other_count = int(cursor.fetchone()["c"])
        cursor.execute("SELECT COUNT(1) AS c FROM daily_snapshots WHERE user_id = ?", ("u_target",))
        snap_count = int(cursor.fetchone()["c"])
        conn.close()

        self.assertEqual(cash_count, 1)
        self.assertEqual(other_count, 1)
        self.assertEqual(snap_count, 1)


if __name__ == "__main__":
    unittest.main()
