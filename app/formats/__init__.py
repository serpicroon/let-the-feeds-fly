from enum import Enum

class FeedFormat(str, Enum):
    RSS2 = "rss2"
    ATOM = "atom"
    JSON_FEED = "jsonfeed"
    
    @property
    def content_type(self) -> str:
        return {
            FeedFormat.RSS2: 'application/rss+xml',
            FeedFormat.ATOM: 'application/atom+xml',
            FeedFormat.JSON_FEED: 'application/json'
        }[self]
    
    @classmethod
    def detect(cls, parsed) -> 'FeedFormat':
        version = parsed.get('version', '')
        if 'atom' in version.lower():
            return cls.ATOM
        elif 'rss' in version.lower():
            return cls.RSS2
        elif 'json' in version.lower():
            return cls.JSON_FEED
        return cls.RSS2

