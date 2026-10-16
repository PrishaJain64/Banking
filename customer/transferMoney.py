# ----------------------------------------------------------------------
# 5. Transfer Money
# ----------------------------------------------------------------------
import config
from auth import *
from transactionsOps import *
from loanOps import get_reserved_collateral, get_available_balance
from utils import *

def transfer_money():
    if not require_login():
        return
    print("\n--- Transfer Money ---")
    try:
        target_num = int(input("Receiver account number: "))
    except ValueError:
        print("Invalid account number.")
        return
    if target_num == config.current.account_number:
        print("Cannot transfer to your own account.")
        return
    receiver = config.accounts.search(target_num)
    if receiver is None:
        print("Receiver account not found.")
        return
    amt = read_amount("Amount to transfer: ")
    if amt is None:
        return
    available = get_available_balance(config.current)
    if amt > available:
        reserved = get_reserved_collateral(config.current)
        if reserved > 0:
            print(f"Insufficient available balance. {reserved:.2f} of your balance is reserved "
                  f"as loan collateral; you can transfer up to {available:.2f}.")
        else:
            print("Insufficient balance.")
        return

    tid = next_txn_id()
    # one transaction node; its id goes into both accounts' chains,
    # which is what updates both balances (they are calculated, not stored)
    add_transaction(tid, "transfer", amt,
                    sender=config.current.account_number, receiver=receiver.account_number)
    print(f"Transferred {amt:.2f} to account {target_num}. Transaction ID: {tid}. "
          f"New balance: {get_balance(config.current):.2f}")
