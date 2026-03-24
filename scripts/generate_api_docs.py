#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KONA_TOOL = ROOT / "kona_tool"
API_MD = ROOT / "docs" / "接口总览.md"
WEB_PAGE_PATHS = {"/", "/assets", "/analysis", "/news", "/settings", "/test", "/compare", "/direct_test"}


def _should_include_path(path: str) -> bool:
    return path in WEB_PAGE_PATHS or path.startswith("/api/") or path == "/health"


def _load_routes() -> list[tuple[str, list[str]]]:
    tmp_dir = tempfile.TemporaryDirectory()
    os.environ.setdefault("KONA_DATABASE_PATH", str(Path(tmp_dir.name) / "api_docs.db"))
    os.environ.setdefault("JWT_SECRET", "api_docs_secret")

    if str(KONA_TOOL) not in sys.path:
        sys.path.insert(0, str(KONA_TOOL))

    import app as app_module  # noqa: E402

    app = app_module.app
    routes: list[tuple[str, list[str]]] = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue
        path = str(rule.rule)
        if not _should_include_path(path):
            continue
        methods = sorted(m for m in (rule.methods or set()) if m not in {"HEAD", "OPTIONS"})
        if not methods:
            continue
        routes.append((path, methods))
    routes.sort(key=lambda item: item[0])
    return routes


def _section_name(path: str) -> str:
    if path in WEB_PAGE_PATHS:
        return "Web Pages"
    if path.startswith("/api/auth"):
        return "Auth"
    if path.startswith("/api/admin"):
        return "Admin APIs"
    if path.startswith("/api/analysis") or path.startswith("/api/news"):
        return "Analysis & News"
    if path.startswith("/api/cash_assets") or path.startswith("/api/other_assets") or path.startswith("/api/liabilities"):
        return "Assets (Cash/Other/Liabilities)"
    if path.startswith("/api/snapshot"):
        return "Snapshots"
    if path.startswith("/api/settings"):
        return "Settings"
    if path == "/health":
        return "Health"
    if path.startswith("/api/"):
        return "Core APIs"
    return "Core APIs"


def main() -> int:
    routes = _load_routes()

    sections: dict[str, list[tuple[str, list[str]]]] = {
        "Web Pages": [],
        "Core APIs": [],
        "Auth": [],
        "Admin APIs": [],
        "Analysis & News": [],
        "Assets (Cash/Other/Liabilities)": [],
        "Snapshots": [],
        "Settings": [],
        "Health": [],
    }

    for path, methods in routes:
        sections[_section_name(path)].append((path, methods))

    lines: list[str] = []
    lines.append("# API Reference (Backend)")
    lines.append("")
    lines.append("This file is auto-generated from the live Flask route map.")
    lines.append("Run: `python3 scripts/generate_api_docs.py`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Detailed Request/Response")
    lines.append("")
    lines.append("See `docs/接口详情.md` for parameters and response formats.")
    lines.append("")
    lines.append("---")
    lines.append("")

    for section, items in sections.items():
        if not items:
            continue
        lines.append(f"## {section}")
        lines.append("")
        for path, methods in items:
            method_list = ", ".join(methods)
            lines.append(f"- `{method_list} {path}`")
        if section == "Core APIs":
            lines.append("")
            lines.append("补一条当前投资写入口规则：")
            lines.append("")
            lines.append("- 普通新增持仓：`POST /api/portfolio/add`")
            lines.append("- 普通改成本价 / 数量：`POST /api/portfolio/modify`")
            lines.append("- 分红 / 手续费 / 税：`POST /api/portfolio/adjustment_event`")
            lines.append("- 看单只持仓的交易、收益事件、修正记录：`GET /api/portfolio/transactions?code=...`")
        lines.append("")

    API_MD.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print("Updated", API_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
