import sqlite3
from pathlib import Path

DB_FILE = Path("bank.db")

def get_connection():
    return sqlite3.connect(DB_FILE)

def init_db():
    # If db exists, delete it so we reset every time
    if DB_FILE.exists():
        DB_FILE.unlink()

    conn = get_connection()
    cursor = conn.cursor()

    # Create table
    cursor.execute('''
    CREATE TABLE account (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        balance REAL NOT NULL DEFAULT 0.0
    )
    ''')

    # Insert sample accounts
    cursor.execute("INSERT INTO account (name, balance) VALUES (?, ?)", ("Alice", 1000.0))
    cursor.execute("INSERT INTO account (name, balance) VALUES (?, ?)", ("Bob", 1000.0))

    conn.commit()
    conn.close()
