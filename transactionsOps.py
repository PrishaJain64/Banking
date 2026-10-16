from config import *
from models import *
import config

# money-in / money-out transaction types (transfer is handled by sender/receiver)
CREDIT_TYPES = ("deposit", "loan_credit")
DEBIT_TYPES = ("withdraw", "loan_repay", "collateral_seized")


def add_transaction(txn_id, txn_type, amount, account_num=None,
                    sender=None, receiver=None, loan_id=None):
    """Store ONE transaction node in the central key/value store (key = txn id),
    then add only the id to the chain of every account involved.
    deposit/withdraw/loan_*  -> only account_num is set -> id added to that account.
    transfer                 -> only sender/receiver set -> same id added to both accounts."""
    node = TransactionNode(txn_id, account_num, txn_type, amount, sender, receiver, loan_id)
    transactions[txn_id] = node
    for num in {account_num, sender, receiver} - {None}:
        acc = config.accounts.search(num)
        if acc:
            acc.add_txn_id(txn_id)
    return node


def get_transactions_for_account(acc):
    """Walk the account's chain of ids and fetch each node from the store in O(1)."""
    result = []
    cur = acc.head
    while cur:
        result.append(transactions[cur.txn_id])
        cur = cur.next
    return result


def get_balance(acc):
    """Balance is never stored: it is calculated from the account's transaction
    chain every time it is needed."""
    total = 0.0
    cur = acc.head
    while cur:
        t = transactions[cur.txn_id]
        if t.txn_type in CREDIT_TYPES:
            total += t.amount
        elif t.txn_type in DEBIT_TYPES:
            total -= t.amount
        elif t.txn_type == "transfer":
            if t.sender_acc == acc.account_number:
                total -= t.amount
            elif t.receiver_acc == acc.account_number:
                total += t.amount
        cur = cur.next
    return round(total, 2)


def display_transaction_table(acc):
    acc_num = acc.account_number
    print(f"\n=== Transaction History for Account {acc_num} ===")
    txns = get_transactions_for_account(acc)
    if not txns:
        print("No transactions found.")
        return
    print(f"{'Txn ID':<8}{'Type':<18}{'Account':<9}{'Sender':<8}"
          f"{'Receiver':<10}{'Amount':>12}  {'Role':<10}{'Loan':<6}Time")
    print("-" * 104)
    for t in txns:
        if t.txn_type == "transfer":
            role = "Sender" if t.sender_acc == acc_num else "Receiver"
            sign = "-" if role == "Sender" else "+"
        else:
            role = "Self"
            sign = "+" if t.txn_type in CREDIT_TYPES else "-"
        acct = "-" if t.account_num is None else t.account_num
        sender = "-" if t.sender_acc is None else t.sender_acc
        receiver = "-" if t.receiver_acc is None else t.receiver_acc
        loan = t.loan_id or "-"
        print(f"{t.txn_id:<8}{t.txn_type:<18}{str(acct):<9}{str(sender):<8}"
              f"{str(receiver):<10}{sign + format(t.amount, '.2f'):>12}  {role:<10}{loan:<6}{t.timestamp}")
