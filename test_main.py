import os
import pytest
from fastapi.testclient import TestClient
from main import app, init_db, DB_NAME

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_database():
    # Reset DB before each test
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    init_db()
    yield


def test_create_account():
    response = client.post("/accounts", json={"account_no": "A1", "holder": "Alice", "balance": 1000})
    assert response.status_code == 200
    assert "created" in response.json()["message"]


def test_check_balance():
    client.post("/accounts", json={"account_no": "A2", "holder": "Bob", "balance": 500})
    response = client.get("/accounts/A2/balance")
    assert response.status_code == 200
    assert response.json()["balance"] == 500


def test_deposit():
    client.post("/accounts", json={"account_no": "A3", "holder": "Charlie", "balance": 200})
    response = client.post("/accounts/A3/deposit", json={"amount": 100})
    assert response.status_code == 200
    assert response.json()["new_balance"] == 300


def test_withdraw():
    client.post("/accounts", json={"account_no": "A4", "holder": "David", "balance": 300})
    response = client.post("/accounts/A4/withdraw", json={"amount": 100})
    assert response.status_code == 200
    assert response.json()["new_balance"] == 200


def test_withdraw_insufficient_balance():
    client.post("/accounts", json={"account_no": "A5", "holder": "Eve", "balance": 50})
    response = client.post("/accounts/A5/withdraw", json={"amount": 100})
    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient funds"


def test_transfer():
    client.post("/accounts", json={"account_no": "A6", "holder": "Frank", "balance": 500})
    client.post("/accounts", json={"account_no": "A7", "holder": "Grace", "balance": 200})
    response = client.post("/transfer", json={"from_acc": "A6", "to_acc": "A7", "amount": 100})
    assert response.status_code == 200
    assert "Transferred" in response.json()["message"]

    balance1 = client.get("/accounts/A6/balance").json()["balance"]
    balance2 = client.get("/accounts/A7/balance").json()["balance"]
    assert balance1 == 400
    assert balance2 == 300


def test_delete_account():
    client.post("/accounts", json={"account_no": "A8", "holder": "Hannah", "balance": 400})
    response = client.delete("/accounts/A8")
    assert response.status_code == 200
    assert "deleted" in response.json()["message"]
