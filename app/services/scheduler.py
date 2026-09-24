import asyncio
import time

from app.core.config import ScheduledFeed, get_scheduled_feeds
from app.core.db import get_meta
from app.core.logger import logger
from app.services.fetcher import sync_with_upstream


class ScheduledSyncService:
    def __init__(self):
        self._tasks: list[asyncio.Task] = []
        self._running = False

    async def _sync_once(self, feed: ScheduledFeed) -> None:
        start = time.monotonic()
        try:
            meta = await get_meta(feed.url)
            status = await sync_with_upstream(
                feed.url,
                etag=meta.etag if meta else None,
                last_modified=meta.last_modified if meta else None,
            )
            elapsed = time.monotonic() - start
            logger.info(f"Scheduled sync {feed.name} {feed.url}: {status} in {elapsed:.1f}s")
        except Exception as e:
            logger.error(f"Scheduled sync {feed.name} {feed.url} failed: {e}")

    async def _feed_loop(self, feed: ScheduledFeed):
        await self._sync_once(feed)
        while self._running:
            try:
                await asyncio.sleep(feed.interval)
                if not self._running:
                    break
                await self._sync_once(feed)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduled loop {feed.name}: {e}")

    async def start(self):
        if self._running:
            logger.warning("Scheduled sync service is already running")
            return
        feeds = get_scheduled_feeds()
        self._running = True
        if not feeds:
            logger.info("No scheduled feeds configured")
            return
        self._tasks = [asyncio.create_task(self._feed_loop(feed)) for feed in feeds]
        logger.info(f"Scheduled sync started for {len(feeds)} feed(s)")

    async def stop(self):
        if not self._running:
            return
        self._running = False
        tasks, self._tasks = self._tasks, []
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


scheduler_service = ScheduledSyncService()
