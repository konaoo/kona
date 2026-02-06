#!/usr/bin/env python3
"""
Restore SQLite database from the latest compressed backup.
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


DEFAULT_DB_PATH = "/home/ec2-user/portfolio/kona_tool/portfolio.db"
DEFAULT_BACKUP_DIR = "/home/ec2-user/portfolio/kona_tool/archive/backups"


def find_latest_backup(backup_dir: str) -> str:
    path = Path(backup_dir)
    files = sorted(path.glob("portfolio_*.db.gz"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"no backup file found in {backup_dir}")
    return str(files[-1])


def _validate_sqlite(db_file: str) -> None:
    conn = sqlite3.connect(db_file)
    try:
        row = conn.execute("PRAGMA quick_check;").fetchone()
        if not row or row[0] != "ok":
            raise RuntimeError(f"sqlite quick_check failed: {row}")
    finally:
        conn.close()


def restore_backup(db_path: str, backup_file: str) -> dict:
    db = Path(db_path)
    if not Path(backup_file).exists():
        raise FileNotFoundError(f"backup file does not exist: {backup_file}")

    if db.exists():
        pre_restore = db.with_suffix(
            db.suffix + f".pre_restore_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        )
        shutil.copy2(db, pre_restore)
    else:
        pre_restore = None

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_db = tmp.name

    try:
        with gzip.open(backup_file, "rb") as gz, open(tmp_db, "wb") as out:
            shutil.copyfileobj(gz, out)
        _validate_sqlite(tmp_db)
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        os.replace(tmp_db, db_path)
    finally:
        Path(tmp_db).unlink(missing_ok=True)

    return {
        "status": "ok",
        "restored_from": backup_file,
        "db_path": db_path,
        "pre_restore_copy": str(pre_restore) if pre_restore else "",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", default=os.getenv("KONA_DATABASE_PATH", DEFAULT_DB_PATH))
    parser.add_argument("--backup-dir", default=os.getenv("KONA_BACKUP_DIR", DEFAULT_BACKUP_DIR))
    parser.add_argument("--backup-file", default="")
    args = parser.parse_args()

    backup_file: str = args.backup_file or find_latest_backup(args.backup_dir)
    result = restore_backup(args.db_path, backup_file)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
