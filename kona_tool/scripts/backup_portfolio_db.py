#!/usr/bin/env python3
"""
Create compressed SQLite backups and prune old backups.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List


SCRIPT_DIR = Path(__file__).resolve().parent
APP_DIR = SCRIPT_DIR.parent
DEFAULT_DB_PATH = str(APP_DIR / "portfolio.db")
DEFAULT_BACKUP_DIR = str(APP_DIR / "archive" / "backups")


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


def maintain_repair_backups(backup_dir: str, retention_days: int = 14) -> dict:
    """压缩已完成的修复备份；只清理过期自动对账备份，人工备份永久保留。"""
    root = Path(backup_dir)
    result = {"compressed": [], "deleted": []}
    if not root.exists():
        return result
    now = datetime.now(timezone.utc).timestamp()
    for source in sorted(root.glob("portfolio-before-*.db")):
        if source.is_symlink() or now - source.stat().st_mtime < 3600:
            continue
        before = source.stat()
        target = source.with_suffix(".db.gz")
        if target.exists():
            raise FileExistsError(f"备份压缩目标已存在，保留原文件: {target}")
        digest = hashlib.sha256()
        with tempfile.NamedTemporaryFile(dir=root, suffix=".gz.part", delete=False) as tmp:
            temp_path = Path(tmp.name)
        try:
            with source.open("rb") as src, gzip.open(temp_path, "wb", compresslevel=1) as out:
                while chunk := src.read(1024 * 1024):
                    digest.update(chunk)
                    out.write(chunk)
            verified = hashlib.sha256()
            with gzip.open(temp_path, "rb") as check:
                while chunk := check.read(1024 * 1024):
                    verified.update(chunk)
            after = source.stat()
            if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
                raise RuntimeError(f"备份仍在变化，保留原文件: {source}")
            if digest.digest() != verified.digest():
                raise RuntimeError(f"压缩校验失败，保留原文件: {source}")
            os.utime(temp_path, (before.st_atime, before.st_mtime))
            os.replace(temp_path, target)
            source.unlink()
            result["compressed"].append(str(target))
        finally:
            temp_path.unlink(missing_ok=True)
    candidates = sorted(
        (p for p in root.glob("portfolio-before-fund-nav-reconcile-*.db.gz") if not p.is_symlink()),
        key=lambda p: p.stat().st_mtime,
    )
    cutoff = now - max(1, retention_days) * 86400
    # 即使任务长期未执行，也至少保留最新一份自动对账备份。
    for path in candidates[:-1]:
        if path.stat().st_mtime < cutoff:
            with gzip.open(path, "rb") as check:
                while check.read(1024 * 1024):
                    pass
            path.unlink()
            result["deleted"].append(str(path))
    return result


def main() -> int:
    db_path = os.getenv("KONA_DATABASE_PATH", DEFAULT_DB_PATH)
    backup_dir = os.getenv("KONA_BACKUP_DIR", DEFAULT_BACKUP_DIR)
    retention_days = int(os.getenv("KONA_BACKUP_RETENTION_DAYS", "14"))

    backup_file = create_backup(db_path, backup_dir)
    repair_maintenance = maintain_repair_backups(
        os.getenv("KONA_REPAIR_BACKUP_DIR", str(Path(db_path).resolve().parent.parent / "backups")),
        int(os.getenv("KONA_REPAIR_BACKUP_RETENTION_DAYS", "14")),
    )
    deleted = prune_old_backups(backup_dir, retention_days)

    print(
        json.dumps(
            {
                "status": "ok",
                "backup_file": backup_file,
                "deleted_count": len(deleted),
                "deleted": deleted,
                "retention_days": retention_days,
                "repair_maintenance": repair_maintenance,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
