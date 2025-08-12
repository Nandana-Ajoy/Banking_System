import pytest
from fastapi.testclient import TestClient
from app import app
from database import init_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_database():
    init_db()
    yield

def test_initial_balance():
    response = client.get("/balance/1")
    assert response.status_code == 200
    assert response.json() == {"account_id": 1, "balance": 1000.0}

def test_deposit_successful():
    response = client.post("/deposit/1", json={"amount": 500.0})
    assert response.status_code == 200
    assert response.json()["message"] == "Deposit successful."
    assert response.json()["new_balance"] == 1500.0

def test_deposit_negative_amount():
    response = client.post("/deposit/1", json={"amount": -100.0})
    assert response.status_code == 400
    assert "Cannot deposit a negative amount" in response.json()["detail"]

def test_withdraw_successful():
    response = client.post("/withdraw/1", json={"amount": 200.0})
    assert response.status_code == 200
    assert response.json()["message"] == "Withdrawal successful."
    assert response.json()["new_balance"] == 800.0

def test_withdraw_insufficient_funds():
    response = client.post("/withdraw/1", json={"amount": 2000.0})
    assert response.status_code == 400
    assert "Insufficient funds" in response.json()["detail"]

def test_transfer_successful():
    response = client.post("/transfer/", json={"from_id": 1, "to_id": 2, "amount": 300.0})
    assert response.status_code == 200
    assert response.json()["message"] == "Transfer successful."

    sender_balance = client.get("/balance/1")
    assert sender_balance.json()["balance"] == 700.0

    receiver_balance = client.get("/balance/2")
    assert receiver_balance.json()["balance"] == 1300.0

def test_transfer_insufficient_funds():
    response = client.post("/transfer/", json={"from_id": 1, "to_id": 2, "amount": 5000.0})
    assert response.status_code == 400
    assert "Insufficient funds in the source account" in response.json()["detail"]

def test_transfer_non_existent_account():
    response = client.post("/transfer/", json={"from_id": 1, "to_id": 99, "amount": 100.0})
    assert response.status_code == 404
    assert "Account not found" in response.json()["detail"]
