from sqlalchemy.orm import Session
from app.services.user import UsersService
from app.services.order import OrderService
from app.db.sessions import get_db
from fastapi import Depends
from app.cache.redis_cache import RedisCache
from app.core.settings import get_settings

settings = get_settings()

redis_cache = RedisCache(settings.redis_url, settings.cache_ttl_seconds)


def get_cache() -> RedisCache:
    return redis_cache


def get_user_service(db: Session = Depends(get_db)):
    """Функция для инъекции зависимости Task Service"""
    return UsersService(db)


def get_order_service(
    db: Session = Depends(get_db), cache: RedisCache = Depends(get_cache)
):
    return OrderService(db, cache)
