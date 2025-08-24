import pytest
from fastapi.testclient import TestClient
from main import app, conn, cursor

client = TestClient(app)

# Reset DB before each test
@pytest.fixture(autouse=True)
def reset_database():
    cursor.execute("DROP TABLE IF EXISTS accounts")
    cursor.execute("""
    CREATE TABLE accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        balance REAL DEFAULT 0
    )
    """)
    conn.commit()
    yield


def test_create_account():
    response = client.post("/account", json={"name": "Alice", "balance": 1000})
    assert response.status_code == 200
    assert "Account created" in response.json()["message"]


def test_check_balance():
    client.post("/account", json={"name": "Bob", "balance": 500})
    response = client.get("/account/1")
    assert response.status_code == 200
    assert response.json()["balance"] == 500


def test_deposit():
    client.post("/account", json={"name": "Charlie", "balance": 200})
    response = client.put("/deposit", json={"account_id": 1, "amount": 100})
    assert response.status_code == 200
    assert response.json()["new_balance"] == 300


def test_withdraw():
    client.post("/account", json={"name": "David", "balance": 300})
    response = client.put("/withdraw", json={"account_id": 1, "amount": 100})
    assert response.status_code == 200
    assert response.json()["new_balance"] == 200


def test_withdraw_insufficient_balance():
    client.post("/account", json={"name": "Eve", "balance": 50})
    response = client.put("/withdraw", json={"account_id": 1, "amount": 100})
    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient balance"


def test_transfer():
    client.post("/account", json={"name": "Frank", "balance": 500})
    client.post("/account", json={"name": "Grace", "balance": 200})
    response = client.post("/transfer", json={"from_account": 1, "to_account": 2, "amount": 100})
    assert response.status_code == 200
    assert "Transferred" in response.json()["message"]

    # Check balances
    balance1 = client.get("/account/1").json()["balance"]
    balance2 = client.get("/account/2").json()["balance"]
    assert balance1 == 400
    assert balance2 == 300


def test_delete_account():
    client.post("/account", json={"name": "Hannah", "balance": 400})
    response = client.delete("/account/1")
    assert response.status_code == 200
    assert "deleted" in response.json()["message"]
