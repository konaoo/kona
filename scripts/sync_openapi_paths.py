#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OPENAPI_FILE = ROOT / "docs" / "openapi.yaml"
KONA_TOOL = ROOT / "kona_tool"

_PATH_LINE_RE = re.compile(r"^  (/[^:]+):\s*$", re.MULTILINE)
_PARAM_RE = re.compile(r"\{([^}]+)\}")


def _normalize_path(path: str) -> str:
    def _repl(match: re.Match[str]) -> str:
        raw = match.group(1)
        if ":" in raw:
            raw = raw.split(":", 1)[1]
        return "{" + raw + "}"

    return re.sub(r"<([^>]+)>", _repl, path)


def _load_routes():
    tmp_dir = tempfile.TemporaryDirectory()
    os.environ.setdefault("KONA_DATABASE_PATH", str(Path(tmp_dir.name) / "openapi_sync.db"))
    os.environ.setdefault("JWT_SECRET", "openapi_sync_secret")

    if str(KONA_TOOL) not in sys.path:
        sys.path.insert(0, str(KONA_TOOL))

    import app as app_module  # noqa: E402

    app = app_module.app
    routes: dict[str, set[str]] = {}
    for rule in app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue
        raw_path = str(rule.rule)
        path = _normalize_path(raw_path)
        if not (path.startswith("/api/") or path == "/health"):
            continue
        methods = sorted(m for m in rule.methods or [] if m not in {"HEAD", "OPTIONS"})
        if not methods:
            continue
        routes.setdefault(path, set()).update(methods)
    return routes


def _load_existing_paths(text: str) -> set[str]:
    return {m.group(1) for m in _PATH_LINE_RE.finditer(text)}


def _build_stub(path: str, methods: list[str]) -> list[str]:
    lines: list[str] = []
    lines.append(f"  {path}:")
    param_names = _PARAM_RE.findall(path)
    if param_names:
        lines.append("    parameters:")
        for name in param_names:
            lines.append("      - in: path")
            lines.append(f"        name: {name}")
            lines.append("        required: true")
            lines.append("        schema:")
            lines.append("          type: string")
    for method in methods:
        lines.append(f"    {method.lower()}:")
        lines.append("      summary: TODO")
        lines.append("      responses:")
        lines.append('        "200":')
        lines.append("          description: OK")
        lines.append("          content:")
        lines.append("            application/json:")
        lines.append("              schema:")
        lines.append("                type: object")
    return lines


def main() -> int:
    if not OPENAPI_FILE.exists():
        raise SystemExit(f"openapi.yaml not found: {OPENAPI_FILE}")

    raw_text = OPENAPI_FILE.read_text(encoding="utf-8")
    marker = "  # AUTO-GENERATED PATH STUBS"
    text = raw_text
    if marker in text:
        text = text.split(marker)[0].rstrip()
    existing = _load_existing_paths(text)
    routes = _load_routes()

    missing = []
    for path, methods in sorted(routes.items()):
        if path in existing:
            continue
        missing.append((path, sorted(methods)))

    if not missing:
        OPENAPI_FILE.write_text(text.rstrip() + "\n", encoding="utf-8")
        print("No missing paths.")
        return 0

    stub_lines = []
    stub_lines.append("")
    stub_lines.append("  # AUTO-GENERATED PATH STUBS (请补 summary/fields)")
    for path, methods in missing:
        stub_lines.extend(_build_stub(path, methods))
        stub_lines.append("")

    OPENAPI_FILE.write_text(text.rstrip() + "\n" + "\n".join(stub_lines), encoding="utf-8")
    print(f"Added {len(missing)} path stubs to {OPENAPI_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
