from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_login_success():
    resp = client.post("/login", json={"username": "trader1", "password": "hunter2"})
    assert resp.status_code == 200
    body = resp.json()
    assert "session_id" in body
    assert body["username"] == "trader1"


def test_login_missing_fields():
    resp = client.post("/login", json={"username": "", "password": ""})
    assert resp.status_code == 400


def test_market_data_known_symbol():
    resp = client.get("/market-data/AAPL")
    assert resp.status_code == 200
    assert resp.json()["symbol"] == "AAPL"


def test_market_data_unknown_symbol():
    resp = client.get("/market-data/ZZZZ")
    assert resp.status_code == 404


def test_order_flow_end_to_end():
    # login first
    login_resp = client.post("/login", json={"username": "trader1", "password": "hunter2"})
    session_id = login_resp.json()["session_id"]

    # place an order
    order_resp = client.post(
        "/orders",
        json={"session_id": session_id, "symbol": "TD", "side": "buy", "quantity": 10},
    )
    assert order_resp.status_code == 200
    order = order_resp.json()
    assert order["status"] == "filled"
    assert order["quantity"] == 10

    # fetch it back
    fetch_resp = client.get(f"/orders/{order['order_id']}")
    assert fetch_resp.status_code == 200
    assert fetch_resp.json()["order_id"] == order["order_id"]


def test_order_requires_valid_session():
    resp = client.post(
        "/orders",
        json={"session_id": "not-a-real-session", "symbol": "TD", "side": "buy", "quantity": 1},
    )
    assert resp.status_code == 401


def test_order_bad_quantity():
    login_resp = client.post("/login", json={"username": "trader1", "password": "hunter2"})
    session_id = login_resp.json()["session_id"]

    resp = client.post(
        "/orders",
        json={"session_id": session_id, "symbol": "TD", "side": "buy", "quantity": -5},
    )
    assert resp.status_code == 400
