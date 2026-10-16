# ----------------------------------------------------------------------
# 2. Deposit Money
# ----------------------------------------------------------------------
import config
from auth import *
from transactionsOps import *
from utils import *

def deposit_money():
    if not require_login():
        return
    print("\n--- Deposit Money ---")
    amt = read_amount("Amount to deposit: ")
    if amt is None:
        return
    tid = next_txn_id()
    add_transaction(tid, "deposit", amt, account_num=config.current.account_number)
    print(f"Deposited {amt:.2f}. Transaction ID: {tid}. New balance: {get_balance(config.current):.2f}")
