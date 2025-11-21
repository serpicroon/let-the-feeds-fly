import json
import hashlib
from typing import Any, Optional
from app.utils.time import normalize_time_struct


def compute_entry_hash(parsed_entry) -> str:
    """
    Compute stable hash for entry identity (not content).
    
    Priority: id > guid > link > title+published > full dump
    
    Args:
        parsed_entry: feedparser entry dict
        
    Returns:
        SHA256 hash string
    """
    core = (
        parsed_entry.get('id') or
        parsed_entry.get('guid') or
        parsed_entry.get('link') or
        parsed_entry.get('title', '') + '|' + parsed_entry.get('published', '')
    )
    if not core:
        core = json.dumps(dict[Any, Any](parsed_entry), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(core.encode('utf-8')).hexdigest()


def compute_feed_updated_time(parsed_feed) -> Optional[str]:
    """
    Compute updated time from feedparser parsed feed.

    Args:
        parsed_feed: feedparser parsed feed dict

    Returns:
        ISO8601 string with 'Z' suffix, or None if not available
    """
    updated_parsed = parsed_feed.get('updated_parsed') or parsed_feed.get('published_parsed')
    return normalize_time_struct(updated_parsed)


def compute_entry_published_time(parsed_entry) -> Optional[str]:
    """
    Extract and normalize published time to ISO8601 with 'Z' suffix.
    
    Args:
        parsed_entry: feedparser entry dict
        
    Returns:
        ISO8601 string with 'Z' suffix, or None if not available
    """
    published_parsed = parsed_entry.get('published_parsed') or parsed_entry.get('updated_parsed')
    return normalize_time_struct(published_parsed)


def compute_entry_guid(parsed_entry) -> Optional[str]:
    """
    Extract GUID from feedparser entry.
    
    Args:
        parsed_entry: feedparser entry dict
        
    Returns:
        GUID string or None
    """
    return parsed_entry.get('id') or parsed_entry.get('guid')

