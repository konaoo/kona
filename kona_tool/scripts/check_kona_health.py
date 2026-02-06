#!/usr/bin/env python3
"""
Health probe for Kona backend.
On failure, sends alert email and exits non-zero.
"""
import json
import os
import socket
import urllib.error
import urllib.request

from alert_sender import send_alert


HEALTH_URL = os.getenv("KONA_HEALTH_URL", "http://127.0.0.1:5003/health")


def main() -> int:
    hostname = socket.gethostname()
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=8) as resp:
            code = resp.getcode()
            payload = resp.read().decode("utf-8", errors="replace")
        if code != 200:
            raise RuntimeError(f"health code={code}, body={payload[:500]}")
        # Basic schema check.
        data = json.loads(payload)
        if data.get("status") != "ok":
            raise RuntimeError(f"health payload status != ok: {payload[:500]}")
        return 0
    except (urllib.error.URLError, urllib.error.HTTPError, RuntimeError, ValueError) as e:
        subject = f"[Kona][ALERT] Health check failed on {hostname}"
        body = (
            f"Health URL: {HEALTH_URL}\n"
            f"Host: {hostname}\n"
            f"Error: {e}\n"
        )
        try:
            send_alert(subject, body)
        except Exception as send_err:  # noqa: BLE001
            print(f"failed to send alert email: {send_err}")
        print(body)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
