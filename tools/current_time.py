from datetime import datetime, timezone

from langchain_core.tools import tool

from core.logging import log_call

@tool
@log_call("tools.current_time")
def current_time() -> str:
    """Return the current UTC date and time. Use this if the user asks what day/time it is, or needs today's date for a calculation."""
    
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
