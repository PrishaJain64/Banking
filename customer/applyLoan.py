# ----------------------------------------------------------------------
# 8. Apply for Loan
# ----------------------------------------------------------------------
import config
from auth import *
from utils import *
from loanOps import (calculate_loan, create_loan, get_available_balance,
                     get_bank_funds, get_loans_for_account, loan_status)

def apply_for_loan():
    if not require_login():
        return
    acc = config.current
    print("\n--- Apply for Loan ---")
    print("Interest (per year, simple) and collateral depend on the loan period:")
    prev = 0
    for max_months, rate, fraction in config.LOAN_TIERS:
        print(f"  {prev + 1:>2} - {max_months:<2} months : {rate:>4}% interest, "
              f"{int(fraction * 100)}% collateral")
        prev = max_months

    if any(loan_status(l) == "Overdue" for l in get_loans_for_account(acc)):
        print("You have an overdue loan. Clear it before applying for a new one.")
        return

    principal = read_amount("Loan amount: ")
    if principal is None:
        return
    try:
        months = int(input(f"Repayment period in months (1-{config.MAX_LOAN_MONTHS}): "))
    except ValueError:
        print("Invalid number of months.")
        return
    if not 1 <= months <= config.MAX_LOAN_MONTHS:
        print(f"Months must be between 1 and {config.MAX_LOAN_MONTHS}.")
        return

    q = calculate_loan(principal, months)
    available = get_available_balance(acc)
    print("\nLoan offer")
    print(f"  Amount           : {inr(q['principal'])}")
    print(f"  Period           : {q['months']} months")
    print(f"  Interest rate    : {q['rate']}% per year")
    print(f"  Total interest   : {inr(q['interest'])}")
    print(f"  Total to repay   : {inr(q['total_payable'])}  (about {inr(q['monthly'])} / month)")
    print(f"  Collateral needed: {inr(q['collateral'])}  (locked in your account until repaid)")
    print(f"  Your available balance: {inr(available)}")

    if available < q["collateral"]:
        print("\nNot fit for this loan: you do not have enough funds in your account "
              "to reserve as collateral.")
        return
    if q["principal"] > get_bank_funds():
        print("\nThe bank does not have enough funds to give this loan right now.")
        return

    if input("\nAccept this loan? (y/n): ").strip().lower() != "y":
        print("Loan application cancelled.")
        return

    loan, tid = create_loan(acc, q)
    print(f"Loan {loan.loan_id} approved. {inr(loan.principal)} credited to your account "
          f"(Transaction ID: {tid}).")
    print(f"{inr(loan.collateral)} is now reserved as collateral. Due date: {loan.due_date}.")
