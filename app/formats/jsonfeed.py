import json
from typing import List, Tuple, Optional
from app.schemas import Meta, Entry
from app.core.logger import logger
from app.formats import FeedFormat
from app.utils.feed import compute_feed_updated_time

_FORMAT = FeedFormat.JSON_FEED.value

def extract(content: bytes, parsed) -> Tuple[Optional[Meta], List[Entry]]:
    try:
        root = json.loads(content)
        meta_data = {k: v for k, v in root.items() if k != 'items'}
        meta_serialized = json.dumps(meta_data, ensure_ascii=False, sort_keys=True)
        meta = Meta(
            format=_FORMAT,
            serialized=meta_serialized,
            updated=compute_feed_updated_time(parsed.feed)
        )

        items = parsed.feed.get('items', [])
        entries = [
            Entry(
                format=_FORMAT,
                serialized=json.dumps(item, ensure_ascii=False, sort_keys=True)
            )
            for item in items
        ]
        
        return meta, entries
    except Exception as e:
        logger.error(f"Failed to extract JSONFeed feed: {e}", exc_info=True)
        return None, []

def rebuild(meta: Meta, entries: List[Entry], self_url: str, cutoff_time: str) -> str:
    meta_data = json.loads(meta.serialized)
    meta_data['feed_url'] = self_url
    meta_data['items'] = [json.loads(entry.serialized) for entry in entries]
    return json.dumps(meta_data, ensure_ascii=False, indent=2)

