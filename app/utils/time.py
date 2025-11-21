import datetime
import calendar
from datetime import datetime, timezone
from typing import Optional


def normalize_time_struct(time_struct) -> Optional[str]:
    """
    Convert time.struct_time (9-tuple) to ISO8601 string with 'Z' suffix.
    
    Feedparser auto-detects and parses date formats into a standard Python 
    9-tuple in UTC. This function converts it to ISO8601 format.
    
    Args:
        time_struct: A time.struct_time object (9-tuple) from feedparser
        
    Returns:
        ISO8601 string with 'Z' suffix, or None if conversion fails
        
    Example:
        >>> t = time.struct_time((2025, 11, 24, 12, 30, 45, 6, 328, 0))
        >>> normalize_time_struct(t)
        '2025-11-24T12:30:45Z'
    """
    if not time_struct:
        return None
    
    try:
        timestamp = calendar.timegm(time_struct)
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    except (ValueError, TypeError, OverflowError):
        return None


def get_cutoff_time(delay_seconds: int) -> str:
    """
    Calculate cutoff time (now - delay_seconds) in unified ISO8601 format.
    
    Args:
        delay_seconds: Number of seconds to subtract from current time
        
    Returns:
        ISO8601 string with 'Z' suffix, no microseconds
        
    Example:
        >>> get_cutoff_time(3600)  # 1 hour ago
        '2025-11-24T11:30:45Z'
    """
    from datetime import timedelta
    cutoff_dt = datetime.now(timezone.utc) - timedelta(seconds=delay_seconds)
    return cutoff_dt.replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def get_latest_iso_time(*time_strings: str) -> Optional[str]:
    """
    Get the latest time from multiple ISO8601 time strings.
    
    Args:
        *time_strings: Variable number of ISO8601 time strings (can be None)
        
    Returns:
        The latest time string, or None if all inputs are None/invalid
        
    Example:
        >>> get_latest_iso_time('2025-11-24T10:00:00Z', '2025-11-24T12:00:00Z')
        '2025-11-24T12:00:00Z'
        >>> get_latest_iso_time('2025-11-24T10:00:00Z', None, '2025-11-24T08:00:00Z')
        '2025-11-24T10:00:00Z'
    """
    valid_times = [t for t in time_strings if t]
    if not valid_times:
        return None
    return max(valid_times)


def iso_to_http_date(iso_time: str) -> Optional[str]:
    """
    Convert ISO8601 time string to HTTP-date format (RFC 1123).
    
    Args:
        iso_time: ISO8601 time string (e.g., '2025-11-24T12:30:45Z')
        
    Returns:
        RFC 1123 formatted string (e.g., 'Wed, 24 Nov 2025 12:30:45 GMT'),
        or None if conversion fails
        
    Example:
        >>> iso_to_http_date('2025-11-24T12:30:45Z')
        'Wed, 24 Nov 2025 12:30:45 GMT'
    """
    if not iso_time:
        return None
    
    try:
        from email.utils import formatdate
        dt = datetime.fromisoformat(iso_time.replace('Z', '+00:00'))
        return formatdate(timeval=dt.timestamp(), localtime=False, usegmt=True)
    except (ValueError, AttributeError):
        return None