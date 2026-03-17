#!/usr/bin/env python3
"""按 request_id 查后端链路日志。

默认先查本地 app.log。
如果你在服务器上跑，也可以用 --source journalctl 直接查 systemd 日志。
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List


ROOT = Path(__file__).resolve().parents[1]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))

import config  # noqa: E402


REQUEST_SUMMARY_PATTERN = re.compile(
    r"REQUEST request_id=(?P<request_id>\S+) "
    r"method=(?P<method>\S+) path=(?P<path>\S+) status=(?P<status>\S+) "
    r"duration_ms=(?P<duration_ms>\S+)"
)


def _default_log_file() -> Path:
    return Path(getattr(config, "LOG_FILE", KONA_TOOL / "app.log"))


def _read_lines_from_file(log_file: Path) -> List[str]:
    try:
        return log_file.read_text(encoding="utf-8", errors="replace").splitlines()
    except FileNotFoundError:
        raise SystemExit(f"日志文件不存在：{log_file}")


def _read_lines_from_journalctl(unit: str, since: str) -> List[str]:
    cmd = ["journalctl", "-u", unit, "--no-pager", "-o", "short-iso"]
    if since:
        cmd.extend(["--since", since])
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        stderr = (result.stderr or "").strip() or "journalctl 执行失败"
        raise SystemExit(stderr)
    return result.stdout.splitlines()


def _filter_request_lines(lines: Iterable[str], request_id: str) -> List[str]:
    target = str(request_id or "").strip()
    return [line for line in lines if target and target in line]


def _format_summary(matches: List[str], request_id: str) -> List[str]:
    summaries: List[str] = []
    for line in matches:
        matched = REQUEST_SUMMARY_PATTERN.search(line)
        if not matched:
            continue
        stage_count = _extract_field(line, "stage_count")
        stage_total_ms = _extract_field(line, "stage_total_ms")
        stages = _extract_field(line, "stages")
        summary = (
            f"请求 {matched.group('request_id')} "
            f"{matched.group('method')} {matched.group('path')} "
            f"status={matched.group('status')} duration_ms={matched.group('duration_ms')}"
        )
        if stage_count:
            summary += f" stage_count={stage_count}"
        if stage_total_ms:
            summary += f" stage_total_ms={stage_total_ms}"
        if stages:
            summary += f" stages={stages}"
        summaries.append(summary)
    if summaries:
        return summaries
    if matches:
        return [f"找到 {len(matches)} 行相关日志，但没有标准 REQUEST 摘要：{request_id}"]
    return [f"没有找到 request_id={request_id} 的相关日志"]


def _extract_field(line: str, key: str) -> str:
    pattern = rf"{re.escape(key)}=(.+?)(?:\s+[a-zA-Z_]+=?|$)"
    matched = re.search(pattern, line)
    if not matched:
        return ""
    value = matched.group(1).strip()
    if " stages=" in value:
        value = value.split(" stages=", 1)[0].strip()
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="按 request_id 查后端链路日志")
    parser.add_argument("request_id", help="要查的 request_id")
    parser.add_argument(
        "--source",
        choices=("file", "journalctl"),
        default="file",
        help="日志来源，默认查本地 app.log",
    )
    parser.add_argument(
        "--log-file",
        default=str(_default_log_file()),
        help="日志文件路径，默认取 kona_tool/config.py 里的 LOG_FILE",
    )
    parser.add_argument(
        "--unit",
        default="kona",
        help="journalctl 模式下要查的 systemd unit，默认 kona",
    )
    parser.add_argument(
        "--since",
        default="2 hours ago",
        help="journalctl 模式下的时间范围，默认最近 2 小时",
    )
    parser.add_argument(
        "--tail",
        type=int,
        default=20,
        help="最多打印多少条匹配日志，默认 20",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.source == "journalctl":
        lines = _read_lines_from_journalctl(args.unit, args.since)
    else:
        lines = _read_lines_from_file(Path(args.log_file))

    matches = _filter_request_lines(lines, args.request_id)
    summaries = _format_summary(matches, args.request_id)
    print("结论：")
    for line in summaries:
        print(f"- {line}")

    if matches:
        print("\n相关日志：")
        for line in matches[-max(int(args.tail or 0), 1):]:
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
