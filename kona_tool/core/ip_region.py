"""IP 归属地解析与地区文本规范化。"""

from __future__ import annotations

import ipaddress
import json
import re
import urllib.request
from functools import lru_cache
from typing import Any, Dict

_ZH_PATTERN = re.compile(r"[\u4e00-\u9fff]")
_NORMALIZED_PATTERN = re.compile(r"^[\u4e00-\u9fff]{2,}(?:-[\u4e00-\u9fff]{2,})?$")
_SEPARATORS = re.compile(r"[—–_]")
_SPACES = re.compile(r"\s+")

_PROVINCE_SUFFIXES = (
    "特别行政区",
    "壮族自治区",
    "回族自治区",
    "维吾尔自治区",
    "自治区",
    "省",
    "市",
    "州",
)
_CITY_SUFFIXES = (
    "自治州",
    "地区",
    "特别行政区",
    "市",
    "盟",
    "州",
)


def is_public_ip(ip: str) -> bool:
    value = str(ip or "").strip()
    if not value:
        return False
    try:
        ip_obj = ipaddress.ip_address(value)
    except ValueError:
        return False
    return not (
        ip_obj.is_private
        or ip_obj.is_loopback
        or ip_obj.is_link_local
        or ip_obj.is_multicast
        or ip_obj.is_reserved
        or ip_obj.is_unspecified
    )


def _http_json(url: str, timeout: float = 1.2) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "kona-ip-geo/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read().decode("utf-8", errors="ignore")
    payload = json.loads(raw or "{}")
    return payload if isinstance(payload, dict) else {}


def _trim_suffix(value: str, suffixes: tuple[str, ...]) -> str:
    result = value
    for suffix in suffixes:
        if result.endswith(suffix) and len(result) > len(suffix):
            result = result[: -len(suffix)]
            break
    return result


def _clean_component(raw: Any, suffixes: tuple[str, ...]) -> str:
    value = str(raw or "").strip()
    if not value:
        return ""
    value = _SEPARATORS.sub("-", value)
    value = _SPACES.sub("", value)
    value = value.replace("·", "").replace("•", "").replace(".", "")
    value = _trim_suffix(value, suffixes)
    return value


def normalize_region_parts(province: Any, city: Any) -> str:
    p = _clean_component(province, _PROVINCE_SUFFIXES)
    c = _clean_component(city, _CITY_SUFFIXES)
    if not _ZH_PATTERN.search(p):
        p = ""
    if not _ZH_PATTERN.search(c):
        c = ""
    if p and c and p != c:
        return f"{p}-{c}"[:120]
    if p:
        return p[:120]
    if c:
        return c[:120]
    return ""


def normalize_region_text(raw: Any) -> str:
    value = str(raw or "").strip()
    if not value:
        return ""
    value = _SEPARATORS.sub("-", value)
    if "-" in value:
        parts = [part for part in value.split("-") if str(part or "").strip()]
        if len(parts) >= 2:
            return normalize_region_parts(parts[0], parts[1])
    return normalize_region_parts(value, "")


def is_normalized_region(value: Any) -> bool:
    raw = str(value or "").strip()
    return bool(raw and _NORMALIZED_PATTERN.fullmatch(raw))


def _resolve_from_ip_api(ip: str) -> str:
    payload = _http_json(f"http://ip-api.com/json/{ip}?lang=zh-CN", timeout=1.0)
    if str(payload.get("status") or "").lower() != "success":
        return ""
    return normalize_region_parts(payload.get("regionName"), payload.get("city"))


def _resolve_from_ipwho(ip: str) -> str:
    payload = _http_json(f"https://ipwho.is/{ip}", timeout=1.2)
    if payload.get("success") is False:
        return ""
    return normalize_region_parts(payload.get("region"), payload.get("city"))


@lru_cache(maxsize=4096)
def resolve_ip_region(ip: str) -> str:
    safe_ip = str(ip or "").strip()
    if not is_public_ip(safe_ip):
        return ""
    try:
        resolved = _resolve_from_ip_api(safe_ip)
        if resolved:
            return resolved
    except Exception:
        pass
    try:
        resolved = _resolve_from_ipwho(safe_ip)
        if resolved:
            return resolved
    except Exception:
        pass
    return ""
