from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import get_connection, init_db

app = FastAPI()

# Run once on startup
@app.on_event("startup")
def startup_event():
    init_db()

class AmountRequest(BaseModel):
    amount: float

class TransferRequest(BaseModel):
    from_id: int
    to_id: int
    amount: float

@app.get("/balance/{account_id}")
def get_balance(account_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM account WHERE id = ?", (account_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Account not found")

    return {"account_id": account_id, "balance": row[0]}

@app.post("/deposit/{account_id}")
def deposit(account_id: int, request: AmountRequest):
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Cannot deposit a negative amount")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE account SET balance = balance + ? WHERE id = ?", (request.amount, account_id))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Account not found")

    conn.commit()
    cursor.execute("SELECT balance FROM account WHERE id = ?", (account_id,))
    new_balance = cursor.fetchone()[0]
    conn.close()

    return {"message": "Deposit successful.", "new_balance": new_balance}

@app.post("/withdraw/{account_id}")
def withdraw(account_id: int, request: AmountRequest):
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid withdrawal amount")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM account WHERE id = ?", (account_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Account not found")

    if row[0] < request.amount:
        conn.close()
        raise HTTPException(status_code=400, detail="Insufficient funds")

    cursor.execute("UPDATE account SET balance = balance - ? WHERE id = ?", (request.amount, account_id))
    conn.commit()
    cursor.execute("SELECT balance FROM account WHERE id = ?", (account_id,))
    new_balance = cursor.fetchone()[0]
    conn.close()

    return {"message": "Withdrawal successful.", "new_balance": new_balance}

@app.post("/transfer/")
def transfer(request: TransferRequest):
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid transfer amount")

    conn = get_connection()
    cursor = conn.cursor()

    # Check from account
    cursor.execute("SELECT balance FROM account WHERE id = ?", (request.from_id,))
    from_acc = cursor.fetchone()
    if not from_acc:
        conn.close()
        raise HTTPException(status_code=404, detail="Account not found")

    # Check to account
    cursor.execute("SELECT balance FROM account WHERE id = ?", (request.to_id,))
    to_acc = cursor.fetchone()
    if not to_acc:
        conn.close()
        raise HTTPException(status_code=404, detail="Account not found")

    if from_acc[0] < request.amount:
        conn.close()
        raise HTTPException(status_code=400, detail="Insufficient funds in the source account")

    # Perform transfer
    cursor.execute("UPDATE account SET balance = balance - ? WHERE id = ?", (request.amount, request.from_id))
    cursor.execute("UPDATE account SET balance = balance + ? WHERE id = ?", (request.amount, request.to_id))
    conn.commit()
    conn.close()

    return {"message": "Transfer successful."}
