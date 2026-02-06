#!/usr/bin/env python3
"""
Check /api/system/price_health and alert when thresholds are exceeded.

Rules:
- network_fail delta in 5-minute window >= threshold
- stale_hits delta in 5-minute window >= threshold
- any source has consecutive_fail >= threshold or circuit_open=true
"""
import json
import os
import socket
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

try:
    from alert_sender import send_alert
except ModuleNotFoundError:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from alert_sender import send_alert


PRICE_HEALTH_URL = os.getenv("PRICE_HEALTH_URL", "http://127.0.0.1:5003/api/system/price_health")
STATE_FILE = os.getenv("PRICE_HEALTH_STATE_FILE", "/tmp/kona_price_health_state.json")

NETWORK_FAIL_DELTA_THRESHOLD = int(os.getenv("PRICE_HEALTH_NETWORK_FAIL_DELTA_THRESHOLD", "20"))
STALE_HITS_DELTA_THRESHOLD = int(os.getenv("PRICE_HEALTH_STALE_HITS_DELTA_THRESHOLD", "30"))
SOURCE_CONSEC_FAIL_THRESHOLD = int(os.getenv("PRICE_HEALTH_SOURCE_CONSEC_FAIL_THRESHOLD", "5"))


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def load_state(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def save_state(path: str, state: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")


def build_alert_messages(current: Dict[str, Any], previous: Dict[str, Any]) -> List[str]:
    alerts: List[str] = []
    runtime = current.get("runtime") or {}
    prev_runtime = previous.get("runtime") or {}

    cur_network_fail = _safe_int(runtime.get("network_fail"), 0)
    cur_stale_hits = _safe_int(runtime.get("stale_hits"), 0)

    if prev_runtime:
        prev_network_fail = _safe_int(prev_runtime.get("network_fail"), cur_network_fail)
        prev_stale_hits = _safe_int(prev_runtime.get("stale_hits"), cur_stale_hits)
    else:
        prev_network_fail = cur_network_fail
        prev_stale_hits = cur_stale_hits

    network_fail_delta = max(0, cur_network_fail - prev_network_fail)
    stale_hits_delta = max(0, cur_stale_hits - prev_stale_hits)

    if network_fail_delta >= NETWORK_FAIL_DELTA_THRESHOLD:
        alerts.append(
            f"network_fail delta in window is {network_fail_delta} "
            f"(threshold {NETWORK_FAIL_DELTA_THRESHOLD})"
        )
    if stale_hits_delta >= STALE_HITS_DELTA_THRESHOLD:
        alerts.append(
            f"stale_hits delta in window is {stale_hits_delta} "
            f"(threshold {STALE_HITS_DELTA_THRESHOLD})"
        )

    sources = current.get("sources") or {}
    for source_name, source_info in sources.items():
        consecutive_fail = _safe_int((source_info or {}).get("consecutive_fail"), 0)
        circuit_open = bool((source_info or {}).get("circuit_open", False))
        if consecutive_fail >= SOURCE_CONSEC_FAIL_THRESHOLD:
            alerts.append(
                f"{source_name} consecutive_fail={consecutive_fail} "
                f"(threshold {SOURCE_CONSEC_FAIL_THRESHOLD})"
            )
        if circuit_open:
            alerts.append(f"{source_name} circuit_open=true")

    return alerts


def _fetch_price_health(url: str) -> Dict[str, Any]:
    with urllib.request.urlopen(url, timeout=10) as resp:
        code = resp.getcode()
        payload = resp.read().decode("utf-8", errors="replace")
    if code != 200:
        raise RuntimeError(f"price_health code={code}, body={payload[:500]}")
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise RuntimeError(f"price_health payload is not object: {payload[:500]}")
    return data


def main() -> int:
    hostname = socket.gethostname()
    now_utc = datetime.now(timezone.utc).isoformat()
    previous_state = load_state(STATE_FILE)

    try:
        current_payload = _fetch_price_health(PRICE_HEALTH_URL)
    except (urllib.error.URLError, urllib.error.HTTPError, RuntimeError, ValueError) as e:
        subject = f"[Kona][ALERT] Price health probe failed on {hostname}"
        body = (
            f"Host: {hostname}\n"
            f"Time(UTC): {now_utc}\n"
            f"URL: {PRICE_HEALTH_URL}\n"
            f"Error: {e}\n"
        )
        try:
            send_alert(subject, body)
        except Exception as send_err:  # noqa: BLE001
            print(f"failed to send alert email: {send_err}")
        print(body)
        return 1

    alerts = build_alert_messages(current_payload, previous_state)
    save_state(
        STATE_FILE,
        {
            "runtime": current_payload.get("runtime") or {},
            "updated_at": now_utc,
        },
    )

    if not alerts:
        return 0

    subject = f"[Kona][ALERT] Price health degraded on {hostname}"
    body = (
        f"Host: {hostname}\n"
        f"Time(UTC): {now_utc}\n"
        f"URL: {PRICE_HEALTH_URL}\n\n"
        "Triggered rules:\n"
        + "\n".join(f"- {line}" for line in alerts)
        + "\n\nCurrent payload:\n"
        + json.dumps(current_payload, ensure_ascii=False, indent=2)
    )
    try:
        send_alert(subject, body)
    except Exception as send_err:  # noqa: BLE001
        print(f"failed to send alert email: {send_err}")
    print(body)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
