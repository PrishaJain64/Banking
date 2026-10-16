import config
from utils import *

def require_login():
    if config.current is None:
        print("No account signed in. Please sign in first (option 7).")
        return False
    return True

# ----------------------------------------------------------------------
# 6. Logout
# ----------------------------------------------------------------------
def logout():
    if config.current is None:
        print("No account is signed in.")
        return
    print(f"Account {config.current.account_number} logged out.")
    config.current = None


# ----------------------------------------------------------------------
# 7. Sign in
# ----------------------------------------------------------------------
def sign_in():
    if config.current is not None:
        print(f"Already signed in as {config.current.account_number}. Logout first.")
        return
    print("\n--- Sign In ---")
    try:
        acc_num = int(input("Account number: "))
    except ValueError:
        print("Invalid account number.")
        return
    password = input("Password: ")
    acc = config.accounts.search(acc_num)
    if acc is None or acc.password != hash_password(password):
        print("Invalid account number or password.")
        return
    config.current = acc
    print(f"Welcome, {acc.name}!")
