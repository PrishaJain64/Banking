# ----------------------------------------------------------------------
# 4. Check Account Status
# ----------------------------------------------------------------------
import config
from transactionsOps import *
from loanOps import get_reserved_collateral, get_available_balance, display_loans_for_account
from auth import *

def display_account_structure(acc):
    print("\n=== Account Structure ===")
    print(f"Account Number : {acc.account_number}")
    print(f"Account Type   : {acc.acc_type}")
    print(f"Full Name      : {acc.name}")
    print(f"Date of Birth  : {acc.dob.strftime('%d-%m-%Y')}")
    print(f"Aadhar Number  : {'XXXXXXXX' + acc.aadhar[-4:]}")
    print(f"Password       : {'*' * 8}")
    print(f"Current Balance: {get_balance(acc):.2f}")
    print(f"Reserved (loan collateral): {get_reserved_collateral(acc):.2f}")
    print(f"Available to withdraw     : {get_available_balance(acc):.2f}")
    print(f"Txn Chain Head  : {acc.head.txn_id if acc.head else 'None'}")


def check_account_status():
    if not require_login():
        return
    display_account_structure(config.current)
    display_transaction_table(config.current)
    display_loans_for_account(config.current)
