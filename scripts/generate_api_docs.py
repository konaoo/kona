#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "kona_tool" / "app.py"
API_MD = ROOT / "docs" / "API.md"

route_re = re.compile(r"@app\.route\('([^']+)'(?:,\s*methods=\[([^\]]+)\])?\)")

routes = []
for line in APP.read_text(encoding="utf-8").splitlines():
    m = route_re.search(line.strip())
    if not m:
        continue
    path = m.group(1)
    methods = m.group(2)
    if methods:
        methods = methods.replace("'", "").replace('"', "").replace(" ", "").split(",")
    else:
        methods = ["GET"]
    routes.append((path, methods))

# Build grouped output
sections = {
    "Web Pages": [],
    "Core APIs": [],
    "Auth": [],
    "Analysis & News": [],
    "Assets (Cash/Other/Liabilities)": [],
    "Snapshots": [],
    "Settings": [],
    "Health": [],
}

def add(section, path, methods):
    sections[section].append((path, methods))

for path, methods in routes:
    if path in ["/", "/assets", "/analysis", "/news", "/settings", "/test", "/compare", "/direct_test"]:
        add("Web Pages", path, methods)
    elif path.startswith("/api/auth"):
        add("Auth", path, methods)
    elif path.startswith("/api/analysis") or path.startswith("/api/news"):
        add("Analysis & News", path, methods)
    elif path.startswith("/api/cash_assets") or path.startswith("/api/other_assets") or path.startswith("/api/liabilities"):
        add("Assets (Cash/Other/Liabilities)", path, methods)
    elif path.startswith("/api/snapshot"):
        add("Snapshots", path, methods)
    elif path.startswith("/api/settings"):
        add("Settings", path, methods)
    elif path == "/health":
        add("Health", path, methods)
    elif path.startswith("/api/"):
        add("Core APIs", path, methods)
    else:
        add("Core APIs", path, methods)

lines = []
lines.append("# API Reference (Backend)\n")
lines.append("This file is auto-generated from `kona_tool/app.py`.\n")
lines.append("Run: `python3 scripts/generate_api_docs.py`\n")
lines.append("\n---\n")
lines.append("## Detailed Request/Response\n\nSee `docs/API_DETAILS.md` for parameters and response formats.\n\n---\n")

for section, items in sections.items():
    if not items:
        continue
    lines.append(f"## {section}\n")
    for path, methods in items:
        method_list = ", ".join(methods)
        lines.append(f"- `{method_list} {path}`")
    lines.append("\n")

API_MD.write_text("\n".join(lines), encoding="utf-8")
print("Updated", API_MD)
