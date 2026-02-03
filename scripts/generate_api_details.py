#!/usr/bin/env python3
from pathlib import Path
import re

APP = Path(__file__).resolve().parents[1] / "kona_tool" / "app.py"
OUT = Path(__file__).resolve().parents[1] / "docs" / "API_DETAILS.md"

route_re = re.compile(r"@app\.route\('([^']+)'(?:,\s*methods=\[([^\]]+)\])?\)")
def_re = re.compile(r"def\s+(\w+)\s*\(")

lines = APP.read_text(encoding="utf-8").splitlines()

routes = []
current_route = None
current_methods = None
current_def = None
current_block = []

for i, line in enumerate(lines):
    m = route_re.search(line.strip())
    if m:
        current_route = m.group(1)
        methods = m.group(2)
        if methods:
            methods = methods.replace("'", "").replace('"', "").replace(" ", "").split(",")
        else:
            methods = ["GET"]
        current_methods = methods
        # continue to find def
        continue

    if current_route and current_def is None:
        d = def_re.search(line.strip())
        if d:
            current_def = d.group(1)
            current_block = [line]
        continue

    if current_def:
        # collect until next def at same indent or EOF
        if line.startswith("def "):
            routes.append((current_route, current_methods, current_def, current_block))
            current_route = None
            current_methods = None
            current_def = None
            current_block = []
        else:
            current_block.append(line)

# finalize
if current_def:
    routes.append((current_route, current_methods, current_def, current_block))

# helpers
args_get_re = re.compile(r"request\.args\.get\('([^']+)'\s*(?:,\s*([^,\)]+))?(?:,\s*type=([^\)]+))?\)")
json_req_re = re.compile(r"if\s+not\s+data\s+or\s+(.+):")
json_field_re = re.compile(r"'([^']+)'\s+not\s+in\s+data")
data_get_re = re.compile(r"data\.get\('([^']+)'\b")
request_files_re = re.compile(r"request\.files")

md = []
md.append("# API Details (Auto Generated)\n")
md.append("Generated from `kona_tool/app.py` by `scripts/generate_api_details.py`.\n")
md.append("This is a best-effort extraction; verify against code for edge cases.\n")
md.append("\n---\n")

for path, methods, func, block in routes:
    block_text = "\n".join(block)
    md.append(f"## `{path}`")
    md.append("")
    md.append(f"**Methods**: {', '.join(methods)}")

    # query params
    params = []
    for m in args_get_re.finditer(block_text):
        name = m.group(1)
        default = m.group(2)
        ptype = m.group(3)
        params.append((name, default, ptype))
    if params:
        md.append("\n**Query Params**")
        for name, default, ptype in params:
            parts = [f"- `{name}`"]
            if default:
                parts.append(f"default: {default}")
            if ptype:
                parts.append(f"type: {ptype}")
            md.append("  " + ", ".join(parts))

    # body params
    required = []
    for m in json_req_re.finditer(block_text):
        cond = m.group(1)
        required.extend(json_field_re.findall(cond))
    required = list(dict.fromkeys(required))
    optional = []
    for m in data_get_re.finditer(block_text):
        optional.append(m.group(1))
    optional = [o for o in dict.fromkeys(optional) if o not in required]

    if required or optional or request_files_re.search(block_text):
        md.append("\n**Request Body**")
        if request_files_re.search(block_text):
            md.append("- multipart/form-data (file upload)")
        if required:
            md.append("- required: " + ", ".join(required))
        if optional:
            md.append("- optional: " + ", ".join(optional))

    # simple response keys
    resp_keys = []
    for line in block:
        if "return jsonify" in line and "{" in line:
            keys = re.findall(r"'([^']+)'\s*:", line)
            resp_keys.extend(keys)
    resp_keys = list(dict.fromkeys(resp_keys))
    if resp_keys:
        md.append("\n**Response (keys)**")
        md.append("- " + ", ".join(resp_keys))

    md.append("\n---\n")

OUT.write_text("\n".join(md), encoding="utf-8")
print("Updated", OUT)
