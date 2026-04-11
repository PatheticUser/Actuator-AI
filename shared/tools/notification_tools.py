"""shared/tools/notification_tools.py — Notification Tools (stubs)"""
from agents import function_tool


@function_tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email notification. (Stub — integrate with SMTP/SendGrid)."""
    return f"[Stub] Email to {to}: {subject}"

@function_tool
def send_slack(channel: str, message: str) -> str:
    """Send a Slack message. (Stub — integrate with Slack webhook)."""
    return f"[Stub] Slack #{channel}: {message}"
