import sqlite3

connection = sqlite3.connect('bank.db')
cursor = connection.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS account (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               name TEXT NOT NULL,
               balance REAL NOT NULL DEFAULT 0.0
)   
''')
connection.commit()

def create_account(name, initial_balance=0.0):
    cursor.execute('''
    INSERT INTO account(name, balance) VALUES (?, ?)
    ''', (name, initial_balance))
    connection.commit()
    print(f"Account Created!\nUser : {name}\nInitial Balance : {initial_balance}")

def get_account_balance(name):
    cursor.execute('''
    SELECT balance FROM account WHERE name = ?
    ''', (name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        print("Account not found.")
        return None
    
def deposit(name, amount):
    cursor.execute('''
    UPDATE account SET balance = balance + ? WHERE name = ?
    ''', (amount, name))
    connection.commit()
    print(f"Deposited {amount} to {name}'s account.")
    get_account_balance(name)

def withdraw(name, amount):
    cursor.execute('''
    SELECT balance FROM account WHERE name = ?
    ''', (name,))
    result = cursor.fetchone()
    if result and result[0] >= amount:
        cursor.execute('''
        UPDATE account SET balance = balance - ? WHERE name = ?
        ''', (amount, name))
        connection.commit()
        print(f"Withdrew {amount} from {name}'s account.")
    else:
        print("Insufficient fund or account not found.")
    get_account_balance(name)

def transfer(from_user, to_user, amount):
    cursor.execute('''
    SELECT balance FROM account WHERE name = ?
    ''', (from_user,))
    from_result = cursor.fetchone()
    
    if from_result and from_result[0] >= amount:
        cursor.execute('''
        UPDATE account SET balance = balance - ? WHERE name = ?
        ''', (amount, from_user))
        
        cursor.execute('''
        UPDATE account SET balance = balance + ? WHERE name = ?
        ''', (amount, to_user))
        
        connection.commit()
        print(f"Transferred {amount} from {from_user} to {to_user}.")
    else:
        print("Transaction Failed!!!\nInsufficient fund or account not found.")
    
    get_account_balance(from_user)
    get_account_balance(to_user)


if __name__ == "__main__":
    while True:
        print("\n===== BANKING SYSTEM MENU =====")
        print("1. Create Account")
        print("2. Check Balance")
        print("3. Deposit")
        print("4. Withdraw")
        print("5. Transfer")
        print("6. Exit")
        
        choice = input("Enter your choice (1-6): ")

        if choice == '1':
            name = input("Enter account holder name: ")
            initial_balance = float(input("Enter initial balance: "))
            create_account(name, initial_balance)

        elif choice == '2':
            name = input("Enter account holder name: ")
            balance = get_account_balance(name)
            if balance is not None:
                print(f"Current Balance for {name}: ₹{balance}")

        elif choice == '3':
            name = input("Enter account holder name: ")
            amount = float(input("Enter amount to deposit: "))
            deposit(name, amount)

        elif choice == '4':
            name = input("Enter account holder name: ")
            amount = float(input("Enter amount to withdraw: "))
            withdraw(name, amount)

        elif choice == '5':
            from_user = input("Transfer from : ")
            to_user = input("Transfer to : ")
            amount = float(input("Enter amount to transfer: "))
            transfer(from_user, to_user, amount)

        elif choice == '6':
            print("Thank you! Have a good day!")
            break

        else:
            print("Invalid choice. Please try again.")
