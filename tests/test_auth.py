def test_register_returns_201_without_password(client):
    r = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Alex",
            "email": "alex@example.com",
            "password": "StrongPass123!",
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["role"] == "client"
    assert "password" not in body and "password_hash" not in body


def test_register_duplicate_email_returns_409(client):
    data = {"name": "Alex", "email": "alex@example.com", "password": "StrongPass123!"}
    client.post("/api/v1/auth/register", json=data)
    assert client.post("/api/v1/auth/register", json=data).status_code == 409


def test_login_wrong_password_returns_401(client, client_headers):
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "example@gmail.com", "password": "WrongPass123!"},
    )
    assert r.status_code == 401


def test_me_without_token_returns_401(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_me_with_garbage_token_returns_401(client):
    r = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer abc.def.ghi"})
    assert r.status_code == 401
