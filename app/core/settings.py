from dataclasses import dataclass
from sqlalchemy import URL
from dotenv import load_dotenv
import os
from pathlib import Path

path = Path(__file__).parent.parent / ".env"
load_dotenv(path)


@dataclass(frozen=True)
class Settings:
    database_url: URL
    redis_url: str
    cache_ttl_seconds: int
    allow_origins: list[str]


def get_settings() -> Settings:
    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host="postgres",
        port=5432,
        database="postgres",
    )
    return Settings(
        database_url=database_url,
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        cache_ttl_seconds=3600,
        allow_origins=["http://localhost:3000", "http://172.19.0.1:3000"],
    )
