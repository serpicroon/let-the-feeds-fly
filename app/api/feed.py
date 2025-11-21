from fastapi import APIRouter, HTTPException, Query, Request, Response, Depends
from datetime import datetime, timezone, timedelta
from email.utils import formatdate, parsedate_to_datetime
from typing import Literal

from app.core.config import get_settings
from app.core.logger import logger
from app.db import get_meta, get_mature_entries, compute_hash
from app.services.fetcher import sync_with_upstream
from app.formats import FeedFormat
from app.formats.handler import rebuild

router = APIRouter()
settings = get_settings()

DELAY_UNITS = {
    "minute": 60,
    "hour": 3600,
    "day": 86400
}

@router.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Let the Feeds Fly",
        "version": "0.1.0",
        "usage": "GET /feed?url=<rss_url>&delay=<number>&unit=<minute|hour|day>&limit=<number>"
    }

@router.get("/feed")
async def get_delayed_feed(
    request: Request,
    url: str = Query(..., description="The upstream RSS feed URL"),
    delay: int = Query(1, ge=0, description="Delay duration"),
    unit: Literal["minute", "hour", "day"] = Query("hour", description="Time unit for delay"),
    limit: int = Query(20, ge=1, le=200, description="Maximum number of entries to return")
):
    """
    Get a delayed RSS feed.
    
    - **url**: The upstream RSS feed URL (required)
    - **delay**: Delay duration (default: 1, must be >= 0)
    - **unit**: Time unit - minute, hour, or day (default: hour)
    - **limit**: Maximum number of entries to return (default: 20, max: 200)
    
    Returns the feed with only "mature" entries (published_at <= now - delay).
    """
    delay_seconds = delay * DELAY_UNITS[unit]
    
    meta = await get_meta(url)
    
    try:
        status_code = await sync_with_upstream(
            url,
            etag=meta.etag if meta else None,
            last_modified=meta.last_modified if meta else None
        )
        
        if status_code >= 200 and status_code < 300:
            meta = await get_meta(url)

    except Exception as e:
        logger.error(f"Failed to sync feed {url}: {e}", exc_info=True)
    
    if not meta:
        raise HTTPException(status_code=502, detail="No feed data available")
    
    cutoff = (datetime.now(timezone.utc) - timedelta(seconds=delay_seconds)).isoformat()
    entries = await get_mature_entries(url, cutoff, limit=limit)
    
    self_url = str(request.url)
    
    # Compute ETag
    content_etag = compute_hash(
        meta.hash + '|' + '|'.join([e.hash for e in entries])
    )
    
    # Compute Last-Modified (ISO format)
    last_modified_iso = meta.updated_at or meta.created_at
    if entries and last_modified_iso:
        entry_times = [e.discovered_at for e in entries if e.discovered_at]
        if entry_times:
            last_modified_iso = max(last_modified_iso, max(entry_times))
    
    # Convert to HTTP-date format (RFC 1123)
    last_modified_http = None
    if last_modified_iso:
        try:
            dt = datetime.fromisoformat(last_modified_iso.replace('Z', '+00:00'))
            last_modified_http = formatdate(timeval=dt.timestamp(), localtime=False, usegmt=True)
        except (ValueError, AttributeError):
            pass
    
    # Check client cache (ETag)
    client_etag = request.headers.get('If-None-Match')
    if client_etag and client_etag.strip('"') == content_etag:
        return Response(
            status_code=304,
            headers={
                'ETag': f'"{content_etag}"',
                'Last-Modified': last_modified_http or ''
            }
        )
    
    # Check client cache (Last-Modified)
    client_last_modified = request.headers.get('If-Modified-Since')
    if client_last_modified and last_modified_http:
        try:
            client_dt = parsedate_to_datetime(client_last_modified)
            server_dt = parsedate_to_datetime(last_modified_http)
            if client_dt >= server_dt:
                return Response(
                    status_code=304,
                    headers={
                        'ETag': f'"{content_etag}"',
                        'Last-Modified': last_modified_http or ''
                    }
                )
        except (ValueError, TypeError):
            pass
    
    # Rebuild feed
    format = FeedFormat(meta.format)
    output = rebuild(meta, entries, format, self_url)
    
    return Response(
        content=output,
        media_type=format.content_type,
        headers={
            'ETag': f'"{content_etag}"',
            'Last-Modified': last_modified_http or ''
        }
    )

