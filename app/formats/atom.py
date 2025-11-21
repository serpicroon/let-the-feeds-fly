from lxml import etree
from typing import List, Tuple, Optional
from app.schemas import Meta, Entry
from app.core.logger import logger
from app.formats import FeedFormat
from app.utils.feed import compute_feed_updated_time

_FORMAT = FeedFormat.ATOM.value
_NS = {'atom': 'http://www.w3.org/2005/Atom'}

def extract(content: bytes, parsed) -> Tuple[Optional[Meta], List[Entry]]:
    try:
        root = etree.fromstring(content)

        # Entry
        entry_elements = root.xpath('/atom:feed/atom:entry', namespaces=_NS)
        entries = [
            Entry(
                format=_FORMAT,
                serialized=etree.tostring(entry_elem, encoding='unicode', pretty_print=False)
            )
            for entry_elem in entry_elements
        ]

        # Meta
        for entry_element in entry_elements:
            entry_element.getparent().remove(entry_element)

        meta_serialized = etree.tostring(root, encoding='unicode', pretty_print=False)
        meta = Meta(
            format=_FORMAT,
            serialized=meta_serialized,
            updated=compute_feed_updated_time(parsed.feed)
        )
        
        return meta, entries
    except Exception as e:
        logger.error(f"Failed to extract Atom feed: {e}", exc_info=True)
        return None, []

def rebuild(meta: Meta, entries: List[Entry], self_url: str, cutoff_time: str) -> str:
    try:
        root = etree.fromstring(meta.serialized.encode('utf-8'))
        
        for link in root.xpath('/atom:feed/atom:link[@rel="self"]', namespaces=_NS):
            link.set('href', self_url)
        
        updated_elems = root.xpath('/atom:feed/atom:updated', namespaces=_NS)
        if updated_elems:
            updated_elems[0].text = cutoff_time

        for entry_data in entries:
            entry_elem = etree.fromstring(entry_data.serialized.encode('utf-8'))
            root.append(entry_elem)
        
        return etree.tostring(root, encoding='utf-8', pretty_print=False, xml_declaration=True).decode('utf-8')
    except Exception as e:
        raise ValueError(f"Failed to rebuild Atom feed: {e}")
