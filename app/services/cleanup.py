import asyncio
from typing import Optional

from app.core.db import cleanup_old_entries, cleanup_orphan_meta
from app.core.config import get_settings
from app.core.logger import logger

settings = get_settings()

CLEANUP_INTERVAL_SECONDS = 24 * 60 * 60


class CleanupService:
    """Background service for cleaning up old entries and orphan meta records."""
    
    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._running = False
    
    async def run_cleanup(self) -> tuple[int, int]:
        """Execute cleanup once.
        
        Returns:
            Tuple of (deleted entries count, deleted meta count)
        """
        try:
            entries_deleted = await cleanup_old_entries(settings.cleanup_after_days)
            meta_deleted = await cleanup_orphan_meta()
            return entries_deleted, meta_deleted
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return 0, 0
    
    async def _cleanup_loop(self):
        """Background loop that runs cleanup periodically."""
        entries_deleted, meta_deleted = await self.run_cleanup()
        
        while self._running:
            try:
                await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
                if not self._running:
                    break
                    
                entries_deleted, meta_deleted = await self.run_cleanup()
                logger.info(f"Scheduled cleanup completed: {entries_deleted} entries, {meta_deleted} meta records removed")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                # Continue running even if one cleanup fails
    
    async def start(self):
        """Start the background cleanup task."""
        if self._running:
            logger.warning("Cleanup service is already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._cleanup_loop())
    
    async def stop(self):
        """Stop the background cleanup task."""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None


cleanup_service = CleanupService()
