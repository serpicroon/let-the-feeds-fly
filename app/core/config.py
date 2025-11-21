from pydantic_settings import BaseSettings
from functools import lru_cache

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

