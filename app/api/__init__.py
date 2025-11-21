from fastapi import APIRouter
from app.api import feed

api_router = APIRouter()
api_router.include_router(feed.router, tags=["feed"])

__all__ = ["api_router"]

