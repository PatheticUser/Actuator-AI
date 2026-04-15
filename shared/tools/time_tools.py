"""shared/tools/time_tools.py — Date, Time & Timezone Tools"""

from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from agents import function_tool


@function_tool
def get_current_time(tz: str = "UTC") -> str:
    """Get current date and time in specified timezone.

    Args:
        tz: IANA timezone string, e.g. 'Asia/Karachi', 'US/Eastern', 'Europe/London'.
            Defaults to UTC.
    """
    try:
        zone = ZoneInfo(tz)
    except KeyError:
        return f"[ERROR] Unknown timezone: '{tz}'. Use IANA format like 'Asia/Karachi'."
    now = datetime.now(zone)
    return (
        f"Current time ({tz}):\n"
        f"  Date: {now.strftime('%A, %B %d, %Y')}\n"
        f"  Time: {now.strftime('%I:%M:%S %p')}\n"
        f"  ISO: {now.isoformat()}\n"
        f"  Unix: {int(now.timestamp())}"
    )


@function_tool
def convert_timezone(time_str: str, from_tz: str, to_tz: str) -> str:
    """Convert a datetime between timezones.

    Args:
        time_str: Datetime in ISO format, e.g. '2026-04-13T10:00:00'.
        from_tz: Source timezone, e.g. 'Asia/Karachi'.
        to_tz: Target timezone, e.g. 'US/Eastern'.
    """
    try:
        src_zone = ZoneInfo(from_tz)
        dst_zone = ZoneInfo(to_tz)
    except KeyError as e:
        return f"[ERROR] Unknown timezone: {e}"

    try:
        dt = datetime.fromisoformat(time_str).replace(tzinfo=src_zone)
        converted = dt.astimezone(dst_zone)
        return (
            f"Timezone conversion:\n"
            f"  From: {dt.strftime('%Y-%m-%d %I:%M %p')} ({from_tz})\n"
            f"  To:   {converted.strftime('%Y-%m-%d %I:%M %p')} ({to_tz})\n"
            f"  Offset difference: {(converted.utcoffset() - dt.utcoffset())}"
        )
    except ValueError as e:
        return f"[ERROR] Invalid datetime format: {e}. Use ISO format like '2026-04-13T10:00:00'."


@function_tool
def time_until(target_date: str) -> str:
    """Calculate time remaining until a target date.

    Args:
        target_date: Target date in YYYY-MM-DD format.
    """
    try:
        target = datetime.strptime(target_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = target - now

        if delta.total_seconds() < 0:
            abs_delta = abs(delta)
            return f"{target_date} was {abs_delta.days} days ago."

        hours, remainder = divmod(delta.seconds, 3600)
        minutes = remainder // 60
        return (
            f"Time until {target_date}:\n"
            f"  {delta.days} days, {hours} hours, {minutes} minutes\n"
            f"  ({int(delta.total_seconds())} seconds total)"
        )
    except ValueError:
        return "[ERROR] Use YYYY-MM-DD format."


@function_tool
def business_hours_check(tz: str = "Asia/Karachi") -> str:
    """Check if current time is within business hours (9 AM - 6 PM Mon-Fri).

    Args:
        tz: Timezone to check against. Default: Asia/Karachi.
    """
    try:
        zone = ZoneInfo(tz)
    except KeyError:
        return f"[ERROR] Unknown timezone: '{tz}'."

    now = datetime.now(zone)
    is_weekday = now.weekday() < 5
    is_hours = 9 <= now.hour < 18

    status = "OPEN" if (is_weekday and is_hours) else "CLOSED"
    return (
        f"Business hours ({tz}):\n"
        f"  Current: {now.strftime('%A %I:%M %p')}\n"
        f"  Status: {status}\n"
        f"  Hours: Mon-Fri 9:00 AM - 6:00 PM"
    )
