#!/usr/bin/env python3
"""
Create compressed SQLite backups and prune old backups.
"""
from __future__ import annotations

import gzip
import json
import os
import shutil
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List


DEFAULT_DB_PATH = "/home/ec2-user/portfolio/kona_tool/portfolio.db"
DEFAULT_BACKUP_DIR = "/home/ec2-user/portfolio/kona_tool/archive/backups"


def _now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def prune_old_backups(backup_dir: str, retention_days: int) -> List[str]:
    deleted: List[str] = []
    keep_after = datetime.now(timezone.utc) - timedelta(days=max(1, retention_days))
    path = Path(backup_dir)
    if not path.exists():
        return deleted

    for file in sorted(path.glob("portfolio_*.db.gz")):
        mtime = datetime.fromtimestamp(file.stat().st_mtime, timezone.utc)
        if mtime < keep_after:
            file.unlink(missing_ok=True)
            deleted.append(str(file))
    return deleted


def create_backup(db_path: str, backup_dir: str) -> str:
    db_file = Path(db_path)
    if not db_file.exists():
        raise FileNotFoundError(f"database file does not exist: {db_path}")

    out_dir = Path(backup_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    base_name = f"portfolio_{_now_str()}"
    out_gz = out_dir / f"{base_name}.db.gz"

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
        tmp_db_path = tmp_db.name

    try:
        src = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        dst = sqlite3.connect(tmp_db_path)
        try:
            src.backup(dst)
        finally:
            dst.close()
            src.close()

        with open(tmp_db_path, "rb") as src_file, gzip.open(out_gz, "wb", compresslevel=6) as gz_file:
            shutil.copyfileobj(src_file, gz_file)
    finally:
        Path(tmp_db_path).unlink(missing_ok=True)

    return str(out_gz)


def main() -> int:
    db_path = os.getenv("KONA_DATABASE_PATH", DEFAULT_DB_PATH)
    backup_dir = os.getenv("KONA_BACKUP_DIR", DEFAULT_BACKUP_DIR)
    retention_days = int(os.getenv("KONA_BACKUP_RETENTION_DAYS", "14"))

    backup_file = create_backup(db_path, backup_dir)
    deleted = prune_old_backups(backup_dir, retention_days)

    print(
        json.dumps(
            {
                "status": "ok",
                "backup_file": backup_file,
                "deleted_count": len(deleted),
                "deleted": deleted,
                "retention_days": retention_days,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
