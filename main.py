from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import uvicorn
from datetime import datetime

DB_NAME = "banking.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            account_no TEXT PRIMARY KEY,
            holder TEXT NOT NULL,
            balance REAL NOT NULL DEFAULT 0,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            txn_type TEXT NOT NULL,
            amount REAL NOT NULL,
            from_acc TEXT,
            to_acc TEXT,
            note TEXT,
            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

app = FastAPI(title="Simple Banking API")

class AccountCreate(BaseModel):
    account_no: str
    holder: str
    balance: float = 0

class MoneyAction(BaseModel):
    amount: float
    note: Optional[str] = None

class Transfer(BaseModel):
    from_acc: str
    to_acc: str
    amount: float
    note: Optional[str] = None


def get_account(acc_no: str):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT account_no, holder, balance, created FROM accounts WHERE account_no=?", (acc_no,))
    acc = cur.fetchone()
    conn.close()
    return acc

def record_transaction(txn_type, amount, from_acc=None, to_acc=None, note=None):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO transactions (txn_type, amount, from_acc, to_acc, note) VALUES (?, ?, ?, ?, ?)",
        (txn_type, amount, from_acc, to_acc, note)
    )
    conn.commit()
    conn.close()

@app.post("/accounts")
def create_account(data: AccountCreate):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO accounts (account_no, holder, balance) VALUES (?, ?, ?)",
                    (data.account_no, data.holder, data.balance))
        conn.commit()
        return {"message": f"Account {data.account_no} created", "status": "success"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Account already exists")
    finally:
        conn.close()


@app.get("/accounts/{acc_no}")
def account_info(acc_no: str):
    acc = get_account(acc_no)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"account_no": acc[0], "holder": acc[1], "balance": acc[2], "created": acc[3]}


@app.get("/accounts/{acc_no}/balance")
def balance(acc_no: str):
    acc = get_account(acc_no)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"account_no": acc[0], "balance": acc[2]}


@app.post("/accounts/{acc_no}/deposit")
def deposit(acc_no: str, data: MoneyAction):
    acc = get_account(acc_no)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")

    new_bal = acc[2] + data.amount
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE accounts SET balance=? WHERE account_no=?", (new_bal, acc_no))
    conn.commit()
    conn.close()

    record_transaction("DEPOSIT", data.amount, to_acc=acc_no, note=data.note)
    return {"message": f"Deposited {data.amount}", "new_balance": new_bal}


@app.post("/accounts/{acc_no}/withdraw")
def withdraw(acc_no: str, data: MoneyAction):
    acc = get_account(acc_no)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")

    if acc[2] < data.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    new_bal = acc[2] - data.amount
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE accounts SET balance=? WHERE account_no=?", (new_bal, acc_no))
    conn.commit()
    conn.close()

    record_transaction("WITHDRAW", data.amount, from_acc=acc_no, note=data.note)
    return {"message": f"Withdrew {data.amount}", "new_balance": new_bal}


@app.post("/transfer")
def transfer(data: Transfer):
    if data.from_acc == data.to_acc:
        raise HTTPException(status_code=400, detail="Cannot transfer to the same account")

    src = get_account(data.from_acc)
    dest = get_account(data.to_acc)
    if not src or not dest:
        raise HTTPException(status_code=404, detail="One or both accounts not found")

    if src[2] < data.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE accounts SET balance=balance-? WHERE account_no=?", (data.amount, data.from_acc))
    cur.execute("UPDATE accounts SET balance=balance+? WHERE account_no=?", (data.amount, data.to_acc))
    conn.commit()
    conn.close()

    record_transaction("TRANSFER", data.amount, from_acc=data.from_acc, to_acc=data.to_acc, note=data.note)
    return {"message": f"Transferred {data.amount} from {data.from_acc} to {data.to_acc}"}


@app.get("/accounts/{acc_no}/transactions")
def transactions(acc_no: str, limit: int = 10):
    acc = get_account(acc_no)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT txn_type, amount, from_acc, to_acc, note, time 
        FROM transactions 
        WHERE from_acc=? OR to_acc=?
        ORDER BY time DESC
        LIMIT ?
    """, (acc_no, acc_no, limit))
    rows = cur.fetchall()
    conn.close()

    return [
        {"txn_type": r[0], "amount": r[1], "from": r[2], "to": r[3], "note": r[4], "time": r[5]}
        for r in rows
    ]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
