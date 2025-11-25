import aiosqlite
import hashlib
from datetime import datetime, timezone
from typing import List, Optional
from app.core.logger import logger
from app.schemas import Meta, Entry

from app.core.config import get_settings

settings = get_settings()

async def init_db():
    async with aiosqlite.connect(settings.database) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feed TEXT NOT NULL UNIQUE,
            format TEXT NOT NULL,
            hash TEXT NOT NULL,
            etag TEXT,
            last_modified TEXT,
            updated TEXT,
            serialized TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feed TEXT NOT NULL,
                format TEXT NOT NULL,
                guid TEXT,
                hash TEXT NOT NULL,
                serialized TEXT NOT NULL,
                published_at TEXT NOT NULL,
                discovered_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)
        
        await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_meta_feed ON meta(feed);")
        
        await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_entries_feed_hash ON entries(feed, hash);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_entries_feed_published_discovered ON entries(feed, published_at DESC, discovered_at DESC);")
        
        await db.commit()
        logger.info("Database initialized successfully.")

def compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def now_iso() -> str:
    """Return current UTC time in ISO8601 with 'Z' suffix, no microseconds"""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

async def upsert_meta(meta: Meta) -> None:
    hash_value = compute_hash(meta.serialized)
    now = now_iso()
    
    async with aiosqlite.connect(settings.database) as db:
        async with db.execute("SELECT hash, updated_at FROM meta WHERE feed = ?", (meta.feed,)) as cursor:
            existing = await cursor.fetchone()
        
        if existing:
            old_hash, old_updated_at = existing
            if old_hash != hash_value:
                await db.execute("""
                    UPDATE meta SET
                        format = ?, hash = ?, etag = ?, last_modified = ?,
                        updated = ?, serialized = ?, updated_at = ?
                    WHERE feed = ?
                """, (meta.format, hash_value, meta.etag, meta.last_modified,
                      meta.updated, meta.serialized, now, meta.feed))
            else:
                await db.execute("""
                    UPDATE meta SET etag = ?, last_modified = ?
                    WHERE feed = ?
                """, (meta.etag, meta.last_modified, meta.feed))
        else:
            await db.execute("""
                INSERT INTO meta (feed, format, hash, etag, last_modified, updated, serialized, updated_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (meta.feed, meta.format, hash_value, meta.etag, meta.last_modified,
                  meta.updated, meta.serialized, now, now))
        
        await db.commit()

async def get_meta(feed: str) -> Optional[Meta]:
    async with aiosqlite.connect(settings.database) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM meta WHERE feed = ?", (feed,)) as cursor:
            row = await cursor.fetchone()
            return Meta(**dict(row)) if row else None

async def upsert_entry(entry: Entry) -> None:
    now = now_iso()
    
    async with aiosqlite.connect(settings.database) as db:
        async with db.execute(
            "SELECT serialized, published_at FROM entries WHERE feed = ? AND hash = ?", 
            (entry.feed, entry.hash)
        ) as cursor:
            existing = await cursor.fetchone()
        
        if existing:
            old_serialized, old_published_at = existing
            if old_serialized != entry.serialized or old_published_at != entry.published_at:
                await db.execute("""
                    UPDATE entries SET serialized = ?, published_at = ?
                    WHERE feed = ? AND hash = ?
                """, (entry.serialized, entry.published_at, entry.feed, entry.hash))
        else:
            await db.execute("""
                INSERT INTO entries (feed, format, guid, hash, serialized, published_at, discovered_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (entry.feed, entry.format, entry.guid, entry.hash,
                  entry.serialized, entry.published_at, entry.discovered_at, now))
        
        await db.commit()

async def get_mature_entries(feed: str, cutoff: str, limit: int = 200) -> List[Entry]:
    async with aiosqlite.connect(settings.database) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM entries
            WHERE feed = ? AND published_at <= ?
            ORDER BY discovered_at DESC
            LIMIT ?
        """, (feed, cutoff, limit)) as cursor:
            rows = await cursor.fetchall()
            return [Entry(**dict(row)) for row in rows]
