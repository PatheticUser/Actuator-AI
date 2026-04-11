"""
shared/tools/time_tools.py — Date & Time Tools
"""

import os
from datetime import datetime
from agents import function_tool


@function_tool
def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.now().strftime("%I:%M %p on %A, %B %d, %Y")


@function_tool
def get_current_date() -> str:
    """Get today's date."""
    return datetime.now().strftime("%Y-%m-%d (%A)")
