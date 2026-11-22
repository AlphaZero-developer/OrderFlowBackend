from dataclasses import dataclass
from sqlalchemy import URL
from dotenv import load_dotenv
import os
from pathlib import Path

path = Path(__file__).parent.parent / ".env"
load_dotenv(path)


@dataclass(frozen=True)
class Settings:
    DATABASE_URL: URL
    allow_origins: list[str]


def get_settings() -> Settings:
    url_to_db = URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host="localhost",
        port=15432,
        database="postgres",
    )
    return Settings(url_to_db, ["http://localhost:3000", "http://172.19.0.1:3000"])
