import importlib.util
import tempfile
import time
import gzip
import sqlite3
import errno
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
BACKUP_SCRIPT = ROOT / "kona_tool" / "scripts" / "backup_portfolio_db.py"
RESTORE_SCRIPT = ROOT / "kona_tool" / "scripts" / "restore_portfolio_db.py"


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class BackupRestoreScriptTests(unittest.TestCase):
    def test_scripts_exist(self):
        self.assertTrue(BACKUP_SCRIPT.exists(), f"missing script: {BACKUP_SCRIPT}")
        self.assertTrue(RESTORE_SCRIPT.exists(), f"missing script: {RESTORE_SCRIPT}")

    def test_prune_old_backups_by_retention_days(self):
        backup_module = _load_module(BACKUP_SCRIPT, "backup_portfolio_db")
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_dir = Path(tmpdir)
            keep_file = backup_dir / "portfolio_20990101_000000.db.gz"
            old_file = backup_dir / "portfolio_19990101_000000.db.gz"
            keep_file.write_bytes(b"new")
            old_file.write_bytes(b"old")

            old_ts = time.time() - (60 * 60 * 24 * 30)
            new_ts = time.time() - (60 * 60 * 24 * 1)
            old_file.touch()
            keep_file.touch()
            old_file.unlink(missing_ok=True)
            keep_file.unlink(missing_ok=True)
            old_file.write_bytes(b"old")
            keep_file.write_bytes(b"new")
            old_file.touch()
            keep_file.touch()
            # Set custom mtimes after touch/write.
            Path(old_file).stat()
            Path(keep_file).stat()
            import os
            os.utime(old_file, (old_ts, old_ts))
            os.utime(keep_file, (new_ts, new_ts))

            deleted = backup_module.prune_old_backups(str(backup_dir), retention_days=14)
            self.assertIn(str(old_file), deleted)
            self.assertFalse(old_file.exists())
            self.assertTrue(keep_file.exists())

    def test_pick_latest_backup_file(self):
        restore_module = _load_module(RESTORE_SCRIPT, "restore_portfolio_db")
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_dir = Path(tmpdir)
            f1 = backup_dir / "portfolio_20260201_010101.db.gz"
            f2 = backup_dir / "portfolio_20260202_010101.db.gz"
            f1.write_bytes(b"a")
            f2.write_bytes(b"b")
            import os
            os.utime(f1, (100, 100))
            os.utime(f2, (200, 200))

            latest = restore_module.find_latest_backup(str(backup_dir))
            self.assertEqual(latest, str(f2))

    def test_restore_uses_same_directory_temp_file(self):
        restore_module = _load_module(RESTORE_SCRIPT, "restore_portfolio_db")
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            db_path = root / "portfolio.db"
            backup_file = root / "portfolio_20260206_000000.db.gz"
            source_db = root / "source.db"

            conn = sqlite3.connect(source_db)
            try:
                conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)")
                conn.execute("INSERT INTO t(v) VALUES ('ok')")
                conn.commit()
            finally:
                conn.close()

            with open(source_db, "rb") as src, gzip.open(backup_file, "wb") as out:
                out.write(src.read())

            # Simulate cross-device failure when source and target dirs differ.
            real_replace = restore_module.os.replace

            def guarded_replace(src, dst):
                if Path(src).parent != Path(dst).parent:
                    raise OSError(errno.EXDEV, "Invalid cross-device link")
                return real_replace(src, dst)

            restore_module.os.replace = guarded_replace
            try:
                result = restore_module.restore_backup(str(db_path), str(backup_file))
            finally:
                restore_module.os.replace = real_replace

            self.assertEqual(result["status"], "ok")
            self.assertTrue(db_path.exists())


if __name__ == "__main__":
    unittest.main()
