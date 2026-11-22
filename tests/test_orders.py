ORDER = {
    "title": "Telegram-бот",
    "description": "Нужен бот для обработки заказов.",
    "budget_rub": 15000,
}


def create_order(client, headers) -> str:
    r = client.post("/api/v1/orders", json=ORDER, headers=headers)
    assert r.status_code == 201
    return r.json()["id"]


def test_client_cannot_see_foreign_order(client, client_headers, other_client_headers):
    order_id = create_order(client, client_headers)
    r = client.get(f"/api/v1/orders/{order_id}", headers=other_client_headers)
    assert r.status_code == 404


def test_manager_sees_all_orders(client, client_headers, manager_headers):
    create_order(client, client_headers)
    assert len(client.get("/api/v1/orders", headers=manager_headers).json()) == 1


def test_client_cannot_change_status(client, client_headers):
    order_id = create_order(client, client_headers)
    r = client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"status": "in_progress"},
        headers=client_headers,
    )
    assert r.status_code == 403


def test_manager_forbidden_transition_returns_409(
    client, client_headers, manager_headers
):
    order_id = create_order(client, client_headers)
    r = client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"status": "completed"},
        headers=manager_headers,
    )
    assert r.status_code == 409


def test_client_can_cancel_only_new_order(client, client_headers, manager_headers):
    order_id = create_order(client, client_headers)
    client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"status": "in_progress"},
        headers=manager_headers,
    )
    r = client.post(f"/api/v1/orders/{order_id}/cancel", headers=client_headers)
    assert r.status_code == 409


def test_client_sees_new_status_after_manager_change(
    client, client_headers, manager_headers
):
    order_id = create_order(client, client_headers)
    client.get("/api/v1/orders", headers=client_headers)
    client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"status": "in_progress"},
        headers=manager_headers,
    )
    orders = client.get("/api/v1/orders", headers=client_headers).json()
    assert orders[0]["status"] == "in_progress"
