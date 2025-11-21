import feedparser
from typing import List, Tuple, Optional
from app.schemas import Entry, Meta
from app.formats import FeedFormat
from app.formats import rss2, atom, jsonfeed

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
        FeedFormat.RSS2: rss2.extract,
        FeedFormat.ATOM: atom.extract,
        FeedFormat.JSON_FEED: jsonfeed.extract
    }
    
    meta, entries = handlers[format](content, parsed)
    
    if not meta:
        return None, [], None
    
    meta.feed = url
    meta.etag = etag
    meta.last_modified = last_modified
    
    for entry in entries:
        entry.feed = url
        entry.discovered_at = discovered_at
    
    return meta, entries, parsed

def rebuild(meta: Meta, entries: List[Entry], format: FeedFormat, self_url: str) -> str:
    handlers = {
        FeedFormat.RSS2: rss2.rebuild,
        FeedFormat.ATOM: atom.rebuild,
        FeedFormat.JSON_FEED: jsonfeed.rebuild
    }
    return handlers[format](meta, entries, self_url)

