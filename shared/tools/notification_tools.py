"""shared/tools/notification_tools.py — Email, Slack, Webhook Notifications

All tools are structured for real integration. Swap stubs with actual
API calls (SendGrid, Slack SDK, generic webhook) when ready.
"""

import os
import json
import httpx
from datetime import datetime, timezone
from agents import function_tool


SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")


@function_tool
def send_email(to: str, subject: str, body: str, priority: str = "normal") -> str:
    """Send email notification via SendGrid.

    Args:
        to: Recipient email.
        subject: Email subject line.
        body: Email body text.
        priority: 'low', 'normal', or 'high'.
    """
    if not SENDGRID_API_KEY:
        # Structured stub — logs what WOULD be sent
        return (
            f"[EMAIL QUEUED — SendGrid not configured]\n"
            f"  To: {to}\n"
            f"  Subject: {subject}\n"
            f"  Priority: {priority}\n"
            f"  Body preview: {body[:150]}\n"
            f"  Timestamp: {datetime.now(timezone.utc).isoformat()}\n"
            f"  → Set SENDGRID_API_KEY in .env to enable delivery."
        )

    try:
        response = httpx.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {SENDGRID_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "personalizations": [{"to": [{"email": to}]}],
                "from": {"email": "noreply@actuator.ai"},
                "subject": subject,
                "content": [{"type": "text/plain", "value": body}],
            },
            timeout=10.0,
        )
        if response.status_code in (200, 202):
            return f"Email sent to {to}: {subject}"
        return f"[ERROR] SendGrid returned {response.status_code}: {response.text}"
    except Exception as e:
        return f"[ERROR] Email failed: {e}"


@function_tool
def send_slack_message(channel: str, message: str, mention: str = "") -> str:
    """Send Slack message to channel or user.

    Args:
        channel: Slack channel name (without #).
        message: Message text. Supports Slack markdown.
        mention: Optional user to @mention (e.g., '@ahmed').
    """
    full_msg = f"{mention} {message}".strip() if mention else message

    if not SLACK_WEBHOOK_URL:
        return (
            f"[SLACK QUEUED — Webhook not configured]\n"
            f"  Channel: #{channel}\n"
            f"  Message: {full_msg[:200]}\n"
            f"  Timestamp: {datetime.now(timezone.utc).isoformat()}\n"
            f"  → Set SLACK_WEBHOOK_URL in .env to enable delivery."
        )

    try:
        response = httpx.post(
            SLACK_WEBHOOK_URL,
            json={"channel": f"#{channel}", "text": full_msg},
            timeout=10.0,
        )
        if response.status_code == 200:
            return f"Slack message sent to #{channel}"
        return f"[ERROR] Slack returned {response.status_code}"
    except Exception as e:
        return f"[ERROR] Slack failed: {e}"


@function_tool
def fire_webhook(url: str, event_type: str, payload: str) -> str:
    """Fire a generic webhook with JSON payload.

    Args:
        url: Webhook endpoint URL.
        event_type: Event type header, e.g. 'ticket.created'.
        payload: JSON string payload.
    """
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return "[ERROR] Invalid JSON payload."

    try:
        response = httpx.post(
            url,
            json=data,
            headers={
                "Content-Type": "application/json",
                "X-Event-Type": event_type,
                "X-Source": "actuator-ai",
            },
            timeout=10.0,
        )
        return (
            f"Webhook fired:\n"
            f"  URL: {url}\n"
            f"  Event: {event_type}\n"
            f"  Status: {response.status_code}\n"
            f"  Response: {response.text[:200]}"
        )
    except Exception as e:
        return f"[ERROR] Webhook failed: {e}"
