import httpx
from typing import Optional
from app.core.db import upsert_meta, upsert_entry, now_iso
from app.formats.handler import extract
from app.core.logger import logger
from app.core.config import get_settings

settings = get_settings()

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
    
    await upsert_meta(meta)

    for idx, entry in enumerate(entries):
        try:
            await upsert_entry(entry)
        except Exception as e:
            logger.error(f"Failed to process entry {idx} from {url}: {e}", exc_info=True)
            continue
    
    logger.info(f"Successfully synced {len(entries)} entries from {url}")
    return 200
