import pytest

from app import app


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_menu_has_items(client):
    r = client.get("/api/menu")
    assert r.status_code == 200
    assert len(r.get_json()) >= 4


def test_homepage_renders(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"QuickBite" in r.data


def test_place_order_calculates_total(client):
    r = client.post(
        "/api/orders",
        json={"customer": "Vanij", "items": [{"id": 1, "qty": 2}, {"id": 4, "qty": 1}]},
    )
    assert r.status_code == 201
    body = r.get_json()
    assert body["total"] == 249 * 2 + 119
    assert len(body["order_id"]) == 8


def test_order_can_be_fetched(client):
    created = client.post(
        "/api/orders", json={"customer": "Asha", "items": [{"id": 2, "qty": 1}]}
    ).get_json()
    r = client.get(f"/api/orders/{created['order_id']}")
    assert r.status_code == 200
    assert r.get_json()["customer"] == "Asha"


def test_missing_order_returns_404(client):
    assert client.get("/api/orders/doesnotexist").status_code == 404


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"customer": "", "items": [{"id": 1, "qty": 1}]},
        {"customer": "X", "items": []},
        {"customer": "X", "items": [{"id": 99, "qty": 1}]},
        {"customer": "X", "items": [{"id": 1, "qty": 0}]},
        {"customer": "X", "items": [{"id": 1, "qty": 500}]},
        {"customer": "X", "items": [{"id": "abc", "qty": 1}]},
    ],
)
def test_invalid_orders_rejected(client, payload):
    assert client.post("/api/orders", json=payload).status_code == 400
