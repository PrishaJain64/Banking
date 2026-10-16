
# ----------------------------------------------------------------------
# 3. Withdraw Money
# ----------------------------------------------------------------------
import config
from auth import *
from transactionsOps import *
from loanOps import get_reserved_collateral, get_available_balance
from utils import *

def withdraw_money():
    if not require_login():
        return
    print("\n--- Withdraw Money ---")
    amt = read_amount("Amount to withdraw: ")
    if amt is None:
        return
    available = get_available_balance(config.current)
    if amt > available:
        reserved = get_reserved_collateral(config.current)
        if reserved > 0:
            print(f"Insufficient available balance. {reserved:.2f} of your balance is reserved "
                  f"as loan collateral; you can withdraw up to {available:.2f}.")
        else:
            print("Insufficient balance.")
        return
    tid = next_txn_id()
    add_transaction(tid, "withdraw", amt, account_num=config.current.account_number)
    print(f"Withdrew {amt:.2f}. Transaction ID: {tid}. New balance: {get_balance(config.current):.2f}")
