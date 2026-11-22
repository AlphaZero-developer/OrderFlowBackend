import json
import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only-1234567890")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.sessions import get_db
from app.main import app
from app.models.base import Base
from app.models.user import UserORM
from app.api.dependencies import get_cache

engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)

TestingSession = sessionmaker(bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(engine)
    session = TestingSession()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def client(db):
    def overrride_get_db():
        yield db

    fake_cache = FakeCache()
    app.dependency_overrides[get_cache] = lambda: fake_cache
    app.dependency_overrides[get_db] = overrride_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def register_and_login(
    client, email: str, password: str = "StrongPassword123!"
) -> dict:
    """Регистрирует клиента, и возвращает заголовок авторизации"""
    client.post(
        "/api/v1/auth/register",
        json={"name": "Test", "email": email, "password": password},
    )
    token = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client_headers(client):
    return register_and_login(client, "client@example.com")


@pytest.fixture
def other_client_headers(client):
    return register_and_login(client, "other@example.com")


@pytest.fixture
def manager_headers(client, db):
    """Менеджер создается напрямую в БД, как это делает seed-скрипт"""
    db.add(
        UserORM(
            name="Manager",
            email="manager@example.com",
            password_hash=hash_password("ManagerPass123!"),
            role="manager",
        )
    )

    db.commit()
    token = client.post(
        "/api/v1/auth/login",
        json={"email": "manager@example.com", "password": "ManagerPass123!"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class FakeCache:
    def __init__(self) -> None:
        self.data: dict[str, str] = {}

    def get(self, key):
        return json.loads(self.data[key]) if key in self.data else None

    def set(self, key, value):
        self.data[key] = json.dumps(value)

    def delete(self, *keys):
        for key in keys:
            self.data.pop(key, None)
