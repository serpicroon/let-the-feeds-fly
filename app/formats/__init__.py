from enum import Enum


class FeedFormat(str, Enum):
    ATOM = "atom"
    RSS2 = "rss2"
    JSON_FEED = "jsonfeed"
    
    @property
    def content_type(self) -> str:
        return {
            FeedFormat.ATOM: 'application/atom+xml; charset=utf-8',
            FeedFormat.RSS2: 'application/rss+xml; charset=utf-8',
            FeedFormat.JSON_FEED: 'application/json; charset=utf-8'
        }[self]
    
    @classmethod
    def detect(cls, parsed) -> 'FeedFormat':
        """Detect feed format from feedparser output"""
        version = getattr(parsed, 'version', '').lower()

        if not version:
            raise ValueError("Unable to detect feed format: no version found")

        for format in cls:
            if format.value == version:
                return format

        if 'atom' in version:
            return cls.ATOM
        elif 'rss' in version:
            return cls.RSS2
        elif 'json' in version:
            return cls.JSON_FEED

        raise ValueError(f"Unsupported feed format: {version}")

