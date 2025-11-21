from lxml import etree
from typing import List, Tuple, Optional
from app.schemas import Meta, Entry
from app.core.logger import logger
from app.formats import FeedFormat

_FORMAT = FeedFormat.ATOM.value

def extract(content: bytes, parsed) -> Tuple[Optional[Meta], List[Entry]]:
    try:
        root = etree.fromstring(content)
        entry_elements = root.xpath('/feed/entry')
        
        for entry_elem in entry_elements:
            entry_elem.getparent().remove(entry_elem)
        
        meta_serialized = etree.tostring(root, encoding='unicode', pretty_print=False)
        updated = parsed.feed.get('updated') or parsed.feed.get('published')
        
        meta = Meta(
            format=_FORMAT,
            serialized=meta_serialized,
            updated=updated
        )
        
        root = etree.fromstring(content)
        entry_elements = root.xpath('/feed/entry')
        
        entries = [
            Entry(
                format=_FORMAT,
                serialized=etree.tostring(entry_elem, encoding='unicode', pretty_print=False)
            )
            for entry_elem in entry_elements
        ]
        
        return meta, entries
    except Exception as e:
        logger.error(f"Failed to extract Atom feed: {e}", exc_info=True)
        return None, []

def rebuild(meta: Meta, entries: List[Entry], self_url: str) -> str:
    try:
        root = etree.fromstring(meta.serialized.encode('utf-8'))
        
        for link in root.xpath('/feed/link[@rel="self"]'):
            link.set('href', self_url)
        
        updated_elems = root.xpath('/feed/updated')
        if updated_elems:
            from datetime import datetime, timezone
            updated_elems[0].text = datetime.now(timezone.utc).isoformat() + 'Z'
        
        for entry_data in entries:
            entry_elem = etree.fromstring(entry_data.serialized.encode('utf-8'))
            root.append(entry_elem)
        
        return etree.tostring(root, encoding='utf-8', pretty_print=False, xml_declaration=True).decode('utf-8')
    except Exception as e:
        raise ValueError(f"Failed to rebuild Atom feed: {e}")
