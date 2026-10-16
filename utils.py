import hashlib
from datetime import date, datetime

import config


def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


def next_account_number():
    config.account_counter += 1
    return config.account_counter


def next_txn_id():
    config.txn_counter += 1
    return f"T_{config.txn_counter}"


def next_loan_id():
    config.loan_counter += 1
    return f"L_{config.loan_counter}"


def get_today():
    """Single place the program asks "what is today's date?" (handy for testing
    overdue loans: temporarily make this return a later date)."""
    return date.today()


def calculate_age(dob):
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def read_amount(prompt):
    try:
        amt = round(float(input(prompt)), 2)
    except ValueError:
        print("Invalid amount.")
        return None
    if amt <= 0:
        print("Amount must be greater than zero.")
        return None
    return amt


def fmt_inr(amount):
    """Indian digit grouping: 1000000 -> '10,00,000.00'."""
    sign = "-" if amount < 0 else ""
    whole, frac = f"{abs(amount):.2f}".split(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        whole = ",".join(parts + [tail])
    return f"{sign}{whole}.{frac}"


def inr(amount):
    return "Rs. " + fmt_inr(amount)
