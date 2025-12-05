from lxml import etree
from typing import List, Tuple, Optional
from app.schemas import Meta, Entry
from app.core.logger import logger
from app.formats import FeedFormat
from app.utils.feed import compute_feed_updated_time
from app.utils.time import iso_to_http_date

_FORMAT = FeedFormat.RSS2.value
_ATOM_NS = 'http://www.w3.org/2005/Atom'
_NS = {'atom': _ATOM_NS}

def extract(content: bytes, parsed) -> Tuple[Optional[Meta], List[Entry]]:
    try:
        root = etree.fromstring(content)
        channels = root.xpath('/rss/channel')
        if not channels:
            return None, []

        # Entry
        item_elements = root.xpath('/rss/channel/item')
        entries = [
            Entry(
                format=_FORMAT,
                serialized=etree.tostring(item, encoding='unicode', pretty_print=False)
            )
            for item in item_elements
        ]

        # Meta
        for item in item_elements:
            item.getparent().remove(item)
        
        meta_serialized = etree.tostring(root, encoding='unicode', pretty_print=False)
        meta = Meta(
            format=_FORMAT,
            serialized=meta_serialized,
            updated=compute_feed_updated_time(parsed.feed)
        )

        return meta, entries
    except Exception as e:
        logger.error(f"Failed to extract RSS2 feed: {e}", exc_info=True)
        return None, []

def rebuild(meta: Meta,
            entries: List[Entry],
            self_url: str,
            cutoff_time: str) -> str:
    try:
        root = etree.fromstring(meta.serialized.encode('utf-8'))
        
        channels = root.xpath('/rss/channel')
        if not channels:
            raise ValueError("No channel found in RSS feed")
        
        channel = channels[0]
        
        atom_links = root.xpath('/rss/channel/atom:link[@rel="self"]', namespaces=_NS)
        if atom_links:
            atom_links[0].set('href', self_url)
        else:
            atom_link = etree.Element(f'{{{_ATOM_NS}}}link', nsmap=_NS)
            atom_link.set('rel', 'self')
            atom_link.set('type', 'application/rss+xml')
            atom_link.set('href', self_url)
            channel.insert(0, atom_link)
        
        last_build_dates = root.xpath('/rss/channel/lastBuildDate')
        if last_build_dates:
            # RSS 2.0 requires RFC 822 date format (e.g., 'Wed, 24 Nov 2025 12:00:00 GMT')
            last_build_dates[0].text = iso_to_http_date(cutoff_time)

        for entry_data in entries:
            item_elem = etree.fromstring(entry_data.serialized.encode('utf-8'))
            channel.append(item_elem)
        
        return etree.tostring(root, encoding='utf-8', pretty_print=False, xml_declaration=True).decode('utf-8')
    except Exception as e:
        raise ValueError(f"Failed to rebuild RSS2 feed: {e}")
