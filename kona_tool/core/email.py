"""
SMTP 邮件发送（验证码）
"""
import ssl
import smtplib
from email.mime.text import MIMEText
from email.header import Header

import config


def send_verification_email(to_email: str, code: str) -> None:
    if not config.SMTP_HOST or not config.SMTP_USER or not config.SMTP_PASS:
        raise ValueError("SMTP 未配置")

    subject = "咔咔记账 登录验证码"
    body = f"您的验证码是 {code}，10 分钟内有效。如非本人操作请忽略本邮件。"
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    sender = config.SMTP_FROM or config.SMTP_USER
    msg["From"] = f"{config.SMTP_FROM_NAME} <{sender}>"
    msg["To"] = to_email

    server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=10)
    try:
        if config.SMTP_USE_TLS:
            server.starttls(context=ssl.create_default_context())
        server.login(config.SMTP_USER, config.SMTP_PASS)
        server.sendmail(sender, [to_email], msg.as_string())
    finally:
        server.quit()
