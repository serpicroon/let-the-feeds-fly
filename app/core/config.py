import os
import re
from dataclasses import dataclass
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    log_level: str = "INFO"
    database: str = "ltff.db"
    http_timeout: float = 60.0
    cleanup_after_days: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()


SCHEDULED_MIN_INTERVAL = 60


@dataclass(frozen=True)
class ScheduledFeed:
    name: str
    url: str
    interval: int


_SCHEDULED_PATTERN = re.compile(r"^SCHEDULED_FEED_([A-Z][A-Z0-9_]*)_(URL|INTERVAL)$")


@lru_cache
def get_scheduled_feeds() -> list[ScheduledFeed]:
    grouped: dict[str, dict[str, str]] = {}
    for key, value in os.environ.items():
        match = _SCHEDULED_PATTERN.match(key.upper())
        if not match:
            continue
        name, kind = match.group(1), match.group(2)
        grouped.setdefault(name, {})[kind] = value

    feeds: list[ScheduledFeed] = []
    for name in sorted(grouped):
        parts = grouped[name]
        if "URL" not in parts or "INTERVAL" not in parts:
            raise ValueError(
                f"SCHEDULED_FEED_{name} incomplete: both _URL and _INTERVAL are required"
            )
        url = parts["URL"].strip()
        if not url:
            raise ValueError(f"SCHEDULED_FEED_{name}_URL must not be empty")
        try:
            interval = int(parts["INTERVAL"].strip())
        except ValueError:
            raise ValueError(
                f"SCHEDULED_FEED_{name}_INTERVAL must be an integer >= "
                f"{SCHEDULED_MIN_INTERVAL}, got {parts['INTERVAL']!r}"
            )
        if interval < SCHEDULED_MIN_INTERVAL:
            raise ValueError(
                f"SCHEDULED_FEED_{name}_INTERVAL must be >= "
                f"{SCHEDULED_MIN_INTERVAL}, got {interval}"
            )
        feeds.append(ScheduledFeed(name=name, url=url, interval=interval))

    seen: dict[str, str] = {}
    for feed in feeds:
        if feed.url in seen:
            raise ValueError(
                f"Duplicate URL for SCHEDULED_FEED_{seen[feed.url]} "
                f"and SCHEDULED_FEED_{feed.name}: {feed.url}"
            )
        seen[feed.url] = feed.name
    return feeds


def get_scheduled_urls() -> set[str]:
    return {feed.url for feed in get_scheduled_feeds()}
