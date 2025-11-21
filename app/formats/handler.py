import feedparser
from typing import List, Tuple, Optional
from app.schemas import Entry, Meta
from app.formats import FeedFormat
from app.formats import rss2, atom, jsonfeed
from app.utils.feed import compute_entry_hash, compute_entry_published_time, compute_entry_guid

def extract(
    content: bytes, 
    url: str, 
    discovered_at: str,
    etag: str = None,
    last_modified: str = None
) -> Tuple[Optional[Meta], List[Entry], object]:
    parsed = feedparser.parse(content)
    
    if not parsed.feed:
        return None, [], None
    
    format = FeedFormat.detect(parsed)
    
    handlers = {
        FeedFormat.ATOM: atom.extract,
        FeedFormat.RSS2: rss2.extract,
        FeedFormat.JSON_FEED: jsonfeed.extract
    }
    
    meta, entries = handlers[format](content, parsed)
    
    if not meta:
        return None, [], None
    
    meta.feed = url
    meta.etag = etag
    meta.last_modified = last_modified
    meta.updated = meta.updated or discovered_at

    for idx, entry in enumerate(entries):
        parsed_entry = parsed.entries[idx]
        entry.feed = url
        entry.guid = compute_entry_guid(parsed_entry)
        entry.hash = compute_entry_hash(parsed_entry)
        entry.published_at = compute_entry_published_time(parsed_entry) or discovered_at
        entry.discovered_at = discovered_at

    return meta, entries, parsed

def rebuild(meta: Meta,
            entries: List[Entry],
            format: FeedFormat,
            self_url: str,
            cutoff_time: str) -> str:
    handlers = {
        FeedFormat.ATOM: atom.rebuild,
        FeedFormat.RSS2: rss2.rebuild,
        FeedFormat.JSON_FEED: jsonfeed.rebuild
    }
    return handlers[format](meta, entries, self_url, cutoff_time)

