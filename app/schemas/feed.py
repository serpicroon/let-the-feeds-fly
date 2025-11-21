from pydantic import BaseModel, Field
from typing import Optional

class Meta(BaseModel):
    """Feed metadata schema"""
    id: Optional[int] = None
    feed: Optional[str] = Field(None, description="Feed URL")
    format: str = Field(..., description="Feed format (rss2/atom/jsonfeed)")
    hash: Optional[str] = Field(None, description="Content hash for deduplication")
    etag: Optional[str] = Field(None, description="HTTP ETag from upstream")
    last_modified: Optional[str] = Field(None, description="HTTP Last-Modified from upstream")
    updated: Optional[str] = Field(None, description="Feed updated time from content")
    serialized: str = Field(..., description="Serialized feed header (XML/JSON)")
    updated_at: Optional[str] = Field(None, description="Last update time")
    created_at: Optional[str] = Field(None, description="Creation time")
    
    class Config:
        from_attributes = True

class Entry(BaseModel):
    """Feed entry schema"""
    id: Optional[int] = None
    feed: Optional[str] = Field(None, description="Feed URL")
    format: str = Field(..., description="Feed format (rss2/atom/jsonfeed)")
    guid: Optional[str] = Field(None, description="GUID/ID")
    hash: Optional[str] = Field(None, description="Content hash for deduplication")
    serialized: str = Field(..., description="Serialized entry content (XML/JSON)")
    published_at: Optional[str] = Field(None, description="Published time")
    discovered_at: Optional[str] = Field(None, description="Discovery time")
    created_at: Optional[str] = Field(None, description="Creation time")
    
    class Config:
        from_attributes = True

