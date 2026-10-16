# ----------------------------------------------------------------------
# 9. Repay Loan
# ----------------------------------------------------------------------
import config
from auth import *
from utils import *
from transactionsOps import get_balance
from loanOps import (get_loans_for_account, loan_remaining, loan_status, collateral_text,
                     get_available_balance, repay_loan_amount)

def repay_loan():
    if not require_login():
        return
    acc = config.current
    print("\n--- Repay Loan ---")
    pending = [l for l in get_loans_for_account(acc) if loan_remaining(l) > 0]
    if not pending:
        print("You have no pending loans.")
        return

    print(f"{'Loan ID':<8}{'Remaining':>14}  {'Due date':<11}Status")
    for l in pending:
        print(f"{l.loan_id:<8}{fmt_inr(loan_remaining(l)):>14}  {str(l.due_date):<11}{loan_status(l)}")

    choice = input("Loan ID to repay: ").strip().upper()
    if choice.isdigit():
        choice = "L_" + choice
    loan = next((l for l in pending if l.loan_id == choice), None)
    if loan is None:
        print("Invalid loan ID.")
        return

    remaining = loan_remaining(loan)
    available = get_available_balance(acc)
    print(f"Remaining on {loan.loan_id}: {inr(remaining)}   Available balance: {inr(available)}")
    amt = read_amount("Amount to repay: ")
    if amt is None:
        return
    if amt > remaining:
        print(f"You only owe {inr(remaining)} on this loan.")
        return

    # Paying the loan off completely frees its own collateral, so it may be used for that.
    pays_off = amt >= remaining
    limit = available + (loan.collateral if pays_off and loan.collateral_state == "reserved" else 0)
    if amt > limit:
        print(f"Insufficient available balance (you can repay up to {inr(max(limit, 0))}). "
              "Collateral reserved for your loans cannot be used for part-payments.")
        return

    tid = repay_loan_amount(acc, loan, amt)
    print(f"Repaid {inr(amt)}. Transaction ID: {tid}. New balance: {inr(get_balance(acc))}")
    left = loan_remaining(loan)
    if left <= 0:
        print(f"Loan {loan.loan_id} fully repaid.", end=" ")
        if loan.collateral_state == "released":
            print(f"Collateral {inr(loan.collateral)} released.")
        else:
            print()
    else:
        print(f"Remaining on {loan.loan_id}: {inr(left)}")
