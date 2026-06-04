"""Delivery helpers for sharing generated digests."""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def deliver_digest(
    digest_path: Path,
    *,
    channel: str,
    subject: str | None = None,
) -> list[str]:
    """Deliver a digest to one or more channels.

    Returns a list of channel labels that were delivered successfully.
    """
    text = digest_path.read_text(encoding="utf-8")
    delivered: list[str] = []
    if channel in ("telegram", "both"):
        send_telegram(text)
        delivered.append("telegram")
    if channel in ("email", "both"):
        send_email(text, subject=subject or "Quant Research Digest")
        delivered.append("email")
    return delivered


def send_telegram(text: str) -> None:
    """Send the digest text to Telegram."""
    bot_token = _require_env("QUANTNEWS_TELEGRAM_BOT_TOKEN")
    chat_id = _require_env("QUANTNEWS_TELEGRAM_CHAT_ID")
    payload = urlencode(
        {
            "chat_id": chat_id,
            "text": _truncate_telegram_text(text),
            "disable_web_page_preview": "true",
        }
    ).encode("utf-8")
    request = Request(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urlopen(request, timeout=20) as response:
        response.read()


def send_email(text: str, *, subject: str) -> None:
    """Send the digest via SMTP as a plain-text email."""
    host = _require_env("QUANTNEWS_SMTP_HOST")
    port = int(os.getenv("QUANTNEWS_SMTP_PORT", "587"))
    username = _require_env("QUANTNEWS_SMTP_USERNAME")
    password = _require_env("QUANTNEWS_SMTP_PASSWORD")
    from_addr = _require_env("QUANTNEWS_EMAIL_FROM")
    to_addrs = [
        addr.strip()
        for addr in _require_env("QUANTNEWS_EMAIL_TO").split(",")
        if addr.strip()
    ]

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_addr
    message["To"] = ", ".join(to_addrs)
    message.set_content(text)

    with smtplib.SMTP(host, port, timeout=20) as smtp:
        smtp.starttls()
        smtp.login(username, password)
        smtp.send_message(message)


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _truncate_telegram_text(text: str, limit: int = 3900) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
