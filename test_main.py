import os
import pytest
import main

# Use in-memory DB for testing
os.environ["DB_NAME"] = ":memory:"
main.init_db()

@pytest.fixture(autouse=True)
def setup_db():
    # Reset DB before each test
    conn = main.sqlite3.connect(main.DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM accounts")
    cur.execute("DELETE FROM transactions")
    conn.commit()
    conn.close()
    yield

# Wrappers
def create_account(holder):
    try:
        return main.create_account(main.AccountCreate(account_no=holder, holder=holder))
    except Exception as e:
        return str(e.detail if hasattr(e, "detail") else e)

def deposit(holder, amount):
    try:
        main.deposit(holder, main.MoneyAction(amount=amount))
        return f"Deposited {amount} to {holder}'s account."
    except Exception as e:
        return str(e.detail if hasattr(e, "detail") else e)

def withdraw(holder, amount):
    try:
        main.withdraw(holder, main.MoneyAction(amount=amount))
        return f"Withdrew {amount} from {holder}'s account."
    except Exception as e:
        return str(e.detail if hasattr(e, "detail") else e)

def transfer(from_holder, to_holder, amount):
    try:
        main.transfer(main.Transfer(from_acc=from_holder, to_acc=to_holder, amount=amount))
        return f"Transferred {amount} from {from_holder} to {to_holder}."
    except Exception as e:
        return str(e.detail if hasattr(e, "detail") else e)

def check_balance(holder):
    try:
        return main.balance(holder)["balance"]
    except Exception as e:
        return str(e.detail if hasattr(e, "detail") else e)


# ------------------- Tests -------------------

def test_create_account_success(setup_db):
    result = create_account("Alice")
    assert "success" in str(result).lower()

def test_create_duplicate_account(setup_db):
    create_account("Alice")
    result = create_account("Alice")
    assert "already exists" in str(result)

def test_deposit_success(setup_db):
    create_account("Bob")
    assert deposit("Bob", 100) == "Deposited 100 to Bob's account."
    assert check_balance("Bob") == 100

def test_deposit_negative_amount(setup_db):
    create_account("Bob")
    result = deposit("Bob", -50)
    assert "must be positive" in str(result).lower()
    assert check_balance("Bob") == 0

def test_deposit_to_nonexistent_account(setup_db):
    result = deposit("Charlie", 200)
    assert "not found" in str(result).lower()

def test_withdraw_success(setup_db):
    create_account("Daisy")
    deposit("Daisy", 300)
    assert withdraw("Daisy", 150) == "Withdrew 150 from Daisy's account."
    assert check_balance("Daisy") == 150

def test_withdraw_insufficient_balance(setup_accounts):
    create_account("Eve")
    deposit("Eve", 50)
    assert withdraw("Eve", 100) == "Insufficient balance."

def test_withdraw_negative_amount(setup_accounts):
    create_account("Frank")
    deposit("Frank", 100)
    assert withdraw("Frank", -20) == "Withdrawal amount must be positive."

def test_withdraw_nonexistent_account(setup_accounts):
    assert withdraw("Ghost", 50) == "Account does not exist."

# ------------------- Transfers -------------------
def test_transfer_success(setup_accounts):
    create_account("Harry")
    create_account("Ivy")
    deposit("Harry", 500)
    assert transfer("Harry", "Ivy", 200) == "Transferred 200 from Harry to Ivy."
    assert check_balance("Harry") == 300
    assert check_balance("Ivy") == 200

def test_transfer_insufficient_balance(setup_accounts):
    create_account("Jack")
    create_account("Kate")
    deposit("Jack", 50)
    assert transfer("Jack", "Kate", 100) == "Insufficient balance."

def test_transfer_to_nonexistent_account(setup_accounts):
    create_account("Leo")
    deposit("Leo", 100)
    assert transfer("Leo", "NonExistent", 50) == "One or both accounts do not exist."

def test_transfer_from_nonexistent_account(setup_accounts):
    create_account("Mona")
    assert transfer("Ghost", "Mona", 30) == "One or both accounts do not exist."

def test_transfer_negative_amount(setup_accounts):
    create_account("Oscar")
    create_account("Pam")
    deposit("Oscar", 100)
    assert transfer("Oscar", "Pam", -20) == "Transfer amount must be positive."

# ------------------- Balance Checks -------------------
def test_check_balance_existing_account(setup_accounts):
    create_account("Quinn")
    deposit("Quinn", 500)
    assert check_balance("Quinn") == 500

def test_check_balance_nonexistent_account(setup_accounts):
    assert check_balance("Ruth") == "Account does not exist."

# ------------------- Edge Cases -------------------
def test_multiple_operations_sequence(setup_accounts):
    create_account("Sam")
    deposit("Sam", 1000)
    withdraw("Sam", 200)
    deposit("Sam", 300)
    withdraw("Sam", 100)
    assert check_balance("Sam") == 1000  # 1000 - 200 + 300 - 100 = 1000

def test_transfer_entire_balance(setup_accounts):
    create_account("Tom")
    create_account("Uma")
    deposit("Tom", 400)
    assert transfer("Tom", "Uma", 400) == "Transferred 400 from Tom to Uma."
    assert check_balance("Tom") == 0
    assert check_balance("Uma") == 400

def test_zero_deposit(setup_accounts):
    create_account("Victor")
    assert deposit("Victor", 0) == "Deposit amount must be positive."

def test_zero_withdraw(setup_accounts):
    create_account("Wendy")
    deposit("Wendy", 100)
    assert withdraw("Wendy", 0) == "Withdrawal amount must be positive."

def test_zero_transfer(setup_accounts):
    create_account("Xavier")
    create_account("Yara")
    deposit("Xavier", 100)
    assert transfer("Xavier", "Yara", 0) == "Transfer amount must be positive."
