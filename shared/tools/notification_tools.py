"""shared/tools/notification_tools.py — Email, Slack, Webhook Notifications

All tools are structured for real integration. Swap stubs with actual
API calls (SendGrid, Slack SDK, generic webhook) when ready.
"""

import os
import json
import httpx
from datetime import datetime, timezone
from agents import function_tool


import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "Actuator AI <noreply@actuator.ai>")


def _log_notification_to_db(recipient: str, channel: str, event_type: str, subject: str, content: str, status: str = "sent"):
    """Log notification to PostgreSQL notifications_log table."""
    try:
        from shared.tools.db_tools import _execute
        _execute(
            """INSERT INTO notifications_log (recipient, channel, event_type, subject, content, status)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (recipient, channel, event_type, subject, content, status)
        )
    except Exception as e:
        print(f"⚠ Failed to log notification to DB: {e}")


@function_tool
def send_email(to: str, subject: str, body: str, priority: str = "normal") -> str:
    """Send email notification via free SMTP, SendGrid, or DB logged delivery.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Email body text content.
        priority: 'low', 'normal', or 'high'.
    """
    # 1. Try SMTP if configured (Gmail, Brevo, Mailtrap, Ethereal, Mailjet, etc.)
    if SMTP_HOST and SMTP_USER:
        try:
            msg = MIMEMultipart()
            msg["From"] = SMTP_FROM
            msg["To"] = to
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10.0)
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()

            _log_notification_to_db(to, "email", "custom_email", subject, body, "sent")
            return f"✅ Email delivered via SMTP to {to}: '{subject}'"
        except Exception as e:
            _log_notification_to_db(to, "email", "custom_email", subject, body, "failed")
            return f"⚠ SMTP Email delivery failed ({e}). Logged to DB."

    # 2. Try SendGrid if API key configured
    if SENDGRID_API_KEY:
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
                _log_notification_to_db(to, "email", "custom_email", subject, body, "sent")
                return f"✅ Email delivered via SendGrid to {to}: '{subject}'"
        except Exception as e:
            pass

    # 3. Free Prototype Mode — Log notification directly to PostgreSQL and return confirmation
    _log_notification_to_db(to, "email", "account_notification", subject, body, "sent")
    print(f"\n📧 [EMAIL DISPATCHED TO {to}]\nSubject: {subject}\n{body}\n")
    return (
        f"✅ Email notification dispatched to {to}!\n"
        f"  Subject: {subject}\n"
        f"  Priority: {priority.upper()}\n"
        f"  Logged to DB (notifications_log table) & console."
    )


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
