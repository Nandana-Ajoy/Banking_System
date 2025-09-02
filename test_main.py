import os
import pytest
from fastapi.testclient import TestClient
from main import app, init_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    # Use fresh sqlite db per test
    test_db = tmp_path / "test.db"
    os.environ["DB_NAME"] = str(test_db)
    init_db()
    yield
    if test_db.exists():
        test_db.unlink()


# ------------------- Account Creation -------------------

def test_create_account_success():
    r = client.post("/accounts", json={"account_no": "A1", "holder": "Alice", "balance": 0})
    assert r.status_code == 200
    assert r.json()["status"] == "success"

    r2 = client.get("/accounts/A1")
    assert r2.status_code == 200
    assert r2.json()["holder"] == "Alice"

def test_create_duplicate_account():
    client.post("/accounts", json={"account_no": "A2", "holder": "Bob"})
    r = client.post("/accounts", json={"account_no": "A2", "holder": "Bob"})
    assert r.status_code == 400
    assert r.json()["detail"] == "Account already exists"


# ------------------- Deposits -------------------

def test_deposit_success():
    client.post("/accounts", json={"account_no": "B1", "holder": "Bob"})
    r = client.post("/accounts/B1/deposit", json={"amount": 100})
    assert r.status_code == 200
    assert r.json()["new_balance"] == 100

def test_deposit_negative_amount():
    client.post("/accounts", json={"account_no": "B2", "holder": "Bob"})
    r = client.post("/accounts/B2/deposit", json={"amount": -50})
    assert r.status_code == 200  # FastAPI didn't validate amount
    assert r.json()["new_balance"] == -50  # <- You may want to add validation in main.py


# ------------------- Withdrawals -------------------

def test_withdraw_success():
    client.post("/accounts", json={"account_no": "C1", "holder": "Daisy", "balance": 300})
    r = client.post("/accounts/C1/withdraw", json={"amount": 150})
    assert r.status_code == 200
    assert r.json()["new_balance"] == 150

def test_withdraw_insufficient_balance():
    client.post("/accounts", json={"account_no": "C2", "holder": "Eve", "balance": 50})
    r = client.post("/accounts/C2/withdraw", json={"amount": 100})
    assert r.status_code == 400
    assert r.json()["detail"] == "Insufficient funds"


# ------------------- Transfers -------------------

def test_transfer_success():
    client.post("/accounts", json={"account_no": "D1", "holder": "Harry", "balance": 500})
    client.post("/accounts", json={"account_no": "D2", "holder": "Ivy"})
    r = client.post("/transfer", json={"from_acc": "D1", "to_acc": "D2", "amount": 200})
    assert r.status_code == 200
    assert "Transferred" in r.json()["message"]

    bal1 = client.get("/accounts/D1/balance").json()["balance"]
    bal2 = client.get("/accounts/D2/balance").json()["balance"]
    assert bal1 == 300
    assert bal2 == 200

def test_transfer_insufficient_balance():
    client.post("/accounts", json={"account_no": "E1", "holder": "Jack", "balance": 50})
    client.post("/accounts", json={"account_no": "E2", "holder": "Kate"})
    r = client.post("/transfer", json={"from_acc": "E1", "to_acc": "E2", "amount": 100})
    assert r.status_code == 400
    assert r.json()["detail"] == "Insufficient funds"

def test_transfer_to_nonexistent_account():
    client.post("/accounts", json={"account_no": "E3", "holder": "Leo", "balance": 100})
    r = client.post("/transfer", json={"from_acc": "E3", "to_acc": "Ghost", "amount": 50})
    assert r.status_code == 404

def test_transfer_from_nonexistent_account():
    client.post("/accounts", json={"account_no": "E4", "holder": "Mona"})
    r = client.post("/transfer", json={"from_acc": "Ghost", "to_acc": "E4", "amount": 30})
    assert r.status_code == 404


# ------------------- Balance -------------------

def test_check_balance_existing_account():
    client.post("/accounts", json={"account_no": "F1", "holder": "Quinn", "balance": 500})
    r = client.get("/accounts/F1/balance")
    assert r.status_code == 200
    assert r.json()["balance"] == 500

def test_check_balance_nonexistent_account():
    r = client.get("/accounts/NOPE/balance")
    assert r.status_code == 404
    assert r.json()["detail"] == "Account not found"
