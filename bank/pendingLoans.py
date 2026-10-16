# ----------------------------------------------------------------------
# Bank 2. Show pending loans
# ----------------------------------------------------------------------
import config
from utils import *
from loanOps import (loan_remaining, loan_status, collateral_text, process_overdue_loans)

def show_pending_loans():
    process_overdue_loans()          # seize collateral of loans whose date has crossed
    pending = [l for l in config.loans.values() if loan_remaining(l) > 0]
    print("\n=== Pending Loans (amounts in Rs.) ===")
    if not pending:
        print("No pending loans.")
        return
    print(f"{'Loan ID':<8}{'Account':<9}{'To be paid':>14}{'Remaining':>14}"
          f"  {'Due date':<13}{'Collateral':<24}Status")
    print("-" * 100)
    total = 0.0
    for l in pending:
        rem = loan_remaining(l)
        total += rem
        print(f"{l.loan_id:<8}{l.account_number:<9}{fmt_inr(l.total_payable):>14}{fmt_inr(rem):>14}"
              f"  {str(l.due_date):<13}{collateral_text(l):<24}{loan_status(l)}")
    print("-" * 100)
    print(f"Total outstanding: {inr(total)}")
