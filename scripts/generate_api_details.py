#!/usr/bin/env python3
from __future__ import annotations

import inspect
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KONA_TOOL = ROOT / "kona_tool"
OUT = ROOT / "docs" / "接口详情.md"
WEB_PAGE_PATHS = {"/", "/assets", "/analysis", "/news", "/settings", "/test", "/compare", "/direct_test"}

ARGS_GET_RE = re.compile(r"request\.args\.get\('([^']+)'\s*(?:,\s*([^,\)]+))?(?:,\s*type=([^\)]+))?\)")
JSON_REQ_RE = re.compile(r"if\s+not\s+data\s+or\s+(.+):")
JSON_FIELD_RE = re.compile(r"'([^']+)'\s+not\s+in\s+data")
DATA_GET_RE = re.compile(r"data\.get\('([^']+)'\b")
REQUEST_FILES_RE = re.compile(r"request\.files")
RETURN_JSONIFY_RE = re.compile(r"return\s+jsonify\((\{.*?\})\)", re.DOTALL)
RETURN_DICT_RE = re.compile(r"return\s+(\{.*?\})(?:,\s*\d+)?", re.DOTALL)
DICT_KEY_RE = re.compile(r"'([^']+)'\s*:")

ROUTE_NOTES = {
    "/api/portfolio/add": [
        "当前普通新增持仓不再接收 legacy `adjustment` 写入。",
    ],
    "/api/portfolio/update": [
        "当前普通更新不再允许 `field=adjustment`。",
    ],
    "/api/portfolio/modify": [
        "当前主用途是修改持仓数量和成本价，不再把 `adjustment` 当必填参数。",
    ],
    "/api/portfolio/adjustment_event": [
        "当前主用途是记录分红、手续费、税这类现金收益事件。",
    ],
    "/api/portfolio/transactions": [
        "这里返回的是单只持仓的交易、收益事件和修正记录混合视图。",
    ],
    "/api/snapshot/save": [
        "这条是快照接口，不是当前普通投资写入口。",
    ],
}


def _load_app():
    tmp_dir = tempfile.TemporaryDirectory()
    os.environ.setdefault("KONA_DATABASE_PATH", str(Path(tmp_dir.name) / "api_details.db"))
    os.environ.setdefault("JWT_SECRET", "api_details_secret")

    if str(KONA_TOOL) not in sys.path:
        sys.path.insert(0, str(KONA_TOOL))

    import app as app_module  # noqa: E402

    return tmp_dir, app_module.app


def _should_include_path(path: str) -> bool:
    return path in WEB_PAGE_PATHS or path.startswith("/api/") or path == "/health"


def _joined_sources(view_func) -> str:
    chunks: list[str] = []
    seen_ids: set[int] = set()

    def _append(func) -> None:
        if not callable(func):
            return
        func_id = id(func)
        if func_id in seen_ids:
            return
        seen_ids.add(func_id)
        try:
            chunks.append(inspect.getsource(func))
        except (OSError, TypeError):
            return

    inner = inspect.unwrap(view_func)
    _append(inner)
    try:
        closure_vars = inspect.getclosurevars(inner)
    except TypeError:
        closure_vars = None
    if closure_vars:
        for value in closure_vars.nonlocals.values():
            _append(value)

    return "\n".join(chunks)


def _extract_query_params(source: str) -> list[tuple[str, str | None, str | None]]:
    params: list[tuple[str, str | None, str | None]] = []
    seen: set[str] = set()
    for match in ARGS_GET_RE.finditer(source):
        name = match.group(1)
        if name in seen:
            continue
        seen.add(name)
        default = match.group(2).strip() if match.group(2) else None
        ptype = match.group(3).strip() if match.group(3) else None
        params.append((name, default, ptype))
    return params


def _extract_body_params(source: str) -> tuple[list[str], list[str], bool]:
    required: list[str] = []
    for match in JSON_REQ_RE.finditer(source):
        required.extend(JSON_FIELD_RE.findall(match.group(1)))
    required = list(dict.fromkeys(required))

    optional: list[str] = []
    for match in DATA_GET_RE.finditer(source):
        optional.append(match.group(1))
    optional = [name for name in dict.fromkeys(optional) if name not in required]
    has_files = bool(REQUEST_FILES_RE.search(source))
    return required, optional, has_files


def _extract_response_keys(source: str) -> list[str]:
    keys: list[str] = []
    for pattern in (RETURN_JSONIFY_RE, RETURN_DICT_RE):
        for match in pattern.finditer(source):
            keys.extend(DICT_KEY_RE.findall(match.group(1)))
    return list(dict.fromkeys(keys))


def main() -> int:
    tmp_dir, app = _load_app()
    try:
        routes: list[tuple[str, list[str], object]] = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint == "static":
                continue
            path = str(rule.rule)
            if not _should_include_path(path):
                continue
            methods = sorted(m for m in (rule.methods or set()) if m not in {"HEAD", "OPTIONS"})
            if not methods:
                continue
            view_func = app.view_functions[rule.endpoint]
            routes.append((path, methods, view_func))
        routes.sort(key=lambda item: item[0])

        md: list[str] = []
        md.append("# API Details (Auto Generated)\n")
        md.append("> 注意：\n")
        md.append(">\n")
        md.append("> 这份文件是自动抽取结果，不是投资口径主文档。\n")
        md.append("> 如果这里和实际代码冲突，优先看：\n")
        md.append(">\n")
        md.append("> - [投资持仓修正与收益事件迁移说明](/Users/kona/Desktop/kaka/kona_repo/docs/投资持仓修正与收益事件迁移说明.md)\n")
        md.append("> - [OpenAPI 文件](/Users/kona/Desktop/kaka/kona_repo/docs/openapi.yaml)\n")
        md.append("\n")
        md.append("Generated from the live Flask route map by `scripts/generate_api_details.py`.\n")
        md.append("This is a best-effort extraction; verify against code for edge cases.\n")
        md.append("\n---\n")

        for path, methods, view_func in routes:
            source = _joined_sources(view_func)
            query_params = _extract_query_params(source)
            required, optional, has_files = _extract_body_params(source)
            response_keys = _extract_response_keys(source)

            md.append(f"## `{path}`")
            md.append("")
            md.append(f"**Methods**: {', '.join(methods)}")

            notes = ROUTE_NOTES.get(path) or []
            if notes:
                md.append("\n**说明**")
                for note in notes:
                    md.append(f"- {note}")

            if query_params:
                md.append("\n**Query Params**")
                for name, default, ptype in query_params:
                    parts = [f"- `{name}`"]
                    if default:
                        parts.append(f"default: {default}")
                    if ptype:
                        parts.append(f"type: {ptype}")
                    md.append("  " + ", ".join(parts))

            if required or optional or has_files:
                md.append("\n**Request Body**")
                if has_files:
                    md.append("- multipart/form-data (file upload)")
                if required:
                    md.append("- required: " + ", ".join(required))
                if optional:
                    md.append("- optional: " + ", ".join(optional))

            if response_keys:
                md.append("\n**Response (keys)**")
                md.append("- " + ", ".join(response_keys))

            md.append("\n---\n")

        OUT.write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")
        print("Updated", OUT)
        return 0
    finally:
        tmp_dir.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
