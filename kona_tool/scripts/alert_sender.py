#!/usr/bin/env python3
"""
Send operational alert emails using existing SMTP env vars.

Usage:
  python3 alert_sender.py --subject "..." --body "..."
"""
import argparse
import os
import smtplib
import ssl
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr


def _split_csv(value: str) -> list[str]:
    return [x.strip() for x in value.split(",") if x.strip()]


def send_alert(subject: str, body: str) -> None:
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_pass = os.getenv("SMTP_PASS", "").strip()
    smtp_from = os.getenv("SMTP_FROM", smtp_user).strip()
    smtp_from_name = os.getenv("SMTP_FROM_NAME", "Kona Alerts").strip()
    smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() != "false"

    recipients = _split_csv(os.getenv("ALERT_NOTIFY_TO", ""))
    if not recipients and smtp_from:
        recipients = [smtp_from]

    if not smtp_host or not smtp_user or not smtp_pass:
        raise RuntimeError("SMTP is not configured for alert sending")
    if not recipients:
        raise RuntimeError("No recipients configured. Set ALERT_NOTIFY_TO")

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    if smtp_from_name:
        msg["From"] = formataddr((str(Header(smtp_from_name, "utf-8")), smtp_from))
    else:
        msg["From"] = smtp_from
    msg["To"] = ", ".join(recipients)

    server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
    try:
        if smtp_use_tls:
            server.starttls(context=ssl.create_default_context())
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_from, recipients, msg.as_string())
    finally:
        server.quit()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", required=True)
    parser.add_argument("--body", required=True)
    args = parser.parse_args()
    send_alert(args.subject, args.body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
