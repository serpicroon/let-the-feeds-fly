from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.logger import logger
from app.db import init_db
from app.api import api_router

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    await init_db()
    logger.info("Application started")
    yield
    # Shutdown
    logger.info("Application shutting down")

app = FastAPI(
    title="Let the Feeds Fly",
    description="A delay proxy for RSS feeds, ensuring entries mature before delivery.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Include API routes
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level=settings.log_level.lower()
    )
