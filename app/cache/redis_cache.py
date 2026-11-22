from typing import Any

from redis import Redis, RedisError
import json
import logging

logger = logging.getLogger(__name__)


class RedisCache:
    def __init__(self, redis_url: str, cache_ttl_seconds: int | None = None) -> None:
        self.redis = Redis.from_url(redis_url, decode_responses=True, socket_timeout=1)
        self.cache_ttl_seconds = cache_ttl_seconds

    def get(self, key: str) -> Any | None:
        try:
            value = self.redis.get(key)
        except RedisError:
            logger.warning("Redis недоступен: set %s", key)
            return None

        return json.loads(value) if value is not None else None

    def set(self, key: str, value: dict) -> None:
        try:
            self.redis.set(key, json.dumps(value), ex=self.cache_ttl_seconds)
        except RedisError:
            logger.warning("Redis недоступен: set %s", key)

    def delete(self, *keys: str) -> None:
        try:
            self.redis.delete(*keys)
        except RedisError:
            logger.warning("Redis недоступен: set %s", *keys)
