import httpx
import json
import hashlib
import time
from datetime import datetime, timezone
from typing import Optional
from app.db import upsert_meta, upsert_entry, now_iso
from app.schemas import Entry
from app.formats import FeedFormat
from app.formats.handler import extract
from app.core.logger import logger
from app.core.config import get_settings

settings = get_settings()

def compute_entry_hash(entry) -> str:
    core = (
        entry.get('id') or
        entry.get('guid') or
        entry.get('link') or
        (entry.get('title', '') + '|' + entry.get('published', ''))
    )
    if not core:
        core = json.dumps(dict(entry), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(core.encode('utf-8')).hexdigest()

def compute_entry_published_time(entry, discovered_at: str) -> str:
    published_parsed = entry.get('published_parsed') or entry.get('updated_parsed')
    if published_parsed:
        try:
            return datetime.fromtimestamp(time.mktime(published_parsed), timezone.utc).isoformat()
        except:
            return discovered_at
    return discovered_at

def enrich_entry(entry: Entry, parsed_entry) -> Entry:
    entry.guid = parsed_entry.get('id') or parsed_entry.get('guid')
    entry.hash = compute_entry_hash(parsed_entry)
    entry.published_at = compute_entry_published_time(parsed_entry, entry.discovered_at)
    return entry

async def sync_with_upstream(
    url: str,
    etag: Optional[str] = None,
    last_modified: Optional[str] = None
) -> int:
    logger.info(f"Fetching feed: {url}")
    
    headers = {}
    if etag:
        headers['If-None-Match'] = etag
    if last_modified:
        headers['If-Modified-Since'] = last_modified
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=settings.http_timeout) as client:
        try:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 304:
                logger.info(f"Feed not modified: {url}")
                return 304
            
            response.raise_for_status()
            content = response.content
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching {url}: {e}")
            raise e
    
    response_etag = response.headers.get('ETag')
    response_last_modified = response.headers.get('Last-Modified')
    
    meta, entries, parsed = extract(
        content,
        url, 
        discovered_at=now_iso(),
        etag=response_etag,
        last_modified=response_last_modified
    )
    
    if not meta or not parsed:
        logger.error(f"Failed to extract feed metadata from {url}")
        raise ValueError("Failed to extract feed metadata")
    
    if parsed.bozo:
        logger.warning(f"Feedparser reported error for {url}: {parsed.bozo_exception}")
    
    if not parsed.entries:
        logger.info(f"No entries found in {url}")
    
    await upsert_meta(meta)
    
    for idx, entry in enumerate(entries):
        if idx < len(parsed.entries):
            enrich_entry(entry, parsed.entries[idx])
            await upsert_entry(entry)
    
    return 200
