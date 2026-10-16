import calendar
from datetime import date

import config
import utils
from models import LoanNode
from transactionsOps import add_transaction, get_balance, get_transactions_for_account

# Everything about a loan that is a money figure (paid, remaining, reserved collateral,
# bank funds) is calculated from the transaction store, never kept as a second copy.

# ----------------------------------------------------------------------
# Terms
# ----------------------------------------------------------------------
def add_months(d, n):
    month_index = d.month - 1 + n
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def calculate_loan(principal, months):
    """Interest rate and collateral depend on the number of months (see config.LOAN_TIERS).
    Simple interest: principal * rate% * months / 12."""
    for max_months, rate, fraction in config.LOAN_TIERS:
        if months <= max_months:
            interest = round(principal * rate / 100 * months / 12, 2)
            return {
                "principal": principal,
                "months": months,
                "rate": rate,
                "interest": interest,
                "total_payable": round(principal + interest, 2),
                "collateral": round(principal * fraction, 2),
                "monthly": round((principal + interest) / months, 2),
            }
    return None


# ----------------------------------------------------------------------
# Loan lookups
# ----------------------------------------------------------------------
def get_loans_for_account(acc):
    result = []
    cur = acc.loan_head
    while cur:
        result.append(config.loans[cur.loan_id])
        cur = cur.next
    return result


def loan_paid(loan):
    """Repayments + seized collateral, summed from the account's transactions."""
    acc = config.accounts.search(loan.account_number)
    total = 0.0
    for t in get_transactions_for_account(acc):
        if t.loan_id == loan.loan_id and t.txn_type in ("loan_repay", "collateral_seized"):
            total += t.amount
    return round(total, 2)


def loan_remaining(loan):
    return max(0.0, round(loan.total_payable - loan_paid(loan), 2))


def is_overdue(loan):
    return loan_remaining(loan) > 0 and utils.get_today() > loan.due_date


def loan_status(loan):
    if loan_remaining(loan) <= 0:
        return "Closed"
    if is_overdue(loan) or loan.collateral_state == "seized":
        return "Overdue"
    return "Active"


def get_reserved_collateral(acc):
    return round(sum(l.collateral for l in get_loans_for_account(acc)
                     if l.collateral_state == "reserved"), 2)


def get_available_balance(acc):
    """Balance the customer may actually withdraw / transfer / repay with:
    the balance minus collateral reserved for active loans."""
    return round(get_balance(acc) - get_reserved_collateral(acc), 2)


def get_bank_funds():
    """Initial funds - loans paid out + repayments + seized collateral."""
    funds = config.BANK_INITIAL_FUNDS
    for t in config.transactions.values():
        if t.txn_type == "loan_credit":
            funds -= t.amount
        elif t.txn_type in ("loan_repay", "collateral_seized"):
            funds += t.amount
    return round(funds, 2)


# ----------------------------------------------------------------------
# Actions
# ----------------------------------------------------------------------
def create_loan(acc, quote):
    """Create the loan (collateral becomes reserved) and credit the money to the account."""
    start = utils.get_today()
    loan = LoanNode(utils.next_loan_id(), acc.account_number, quote["principal"],
                    quote["months"], quote["rate"], quote["interest"],
                    quote["total_payable"], quote["collateral"],
                    start, add_months(start, quote["months"]))
    config.loans[loan.loan_id] = loan
    acc.add_loan_id(loan.loan_id)
    tid = utils.next_txn_id()
    add_transaction(tid, "loan_credit", loan.principal,
                    account_num=acc.account_number, loan_id=loan.loan_id)
    return loan, tid


def repay_loan_amount(acc, loan, amt):
    """Deduct the repayment from the account (as a transaction); release the
    collateral once the loan is fully repaid."""
    tid = utils.next_txn_id()
    add_transaction(tid, "loan_repay", amt,
                    account_num=acc.account_number, loan_id=loan.loan_id)
    if loan_remaining(loan) <= 0 and loan.collateral_state == "reserved":
        loan.collateral_state = "released"
    return tid


def process_overdue_loans():
    """If a loan's due date has passed and it is not fully repaid, the reserved
    collateral is seized from the customer's account and counted against the debt."""
    for loan in list(config.loans.values()):
        if loan.collateral_state == "reserved" and is_overdue(loan):
            acc = config.accounts.search(loan.account_number)
            amt = min(loan.collateral, loan_remaining(loan))
            tid = utils.next_txn_id()
            add_transaction(tid, "collateral_seized", amt,
                            account_num=acc.account_number, loan_id=loan.loan_id)
            loan.collateral_state = "seized"
            print(f"[Notice] Loan {loan.loan_id} (account {acc.account_number}) passed its due "
                  f"date {loan.due_date}: collateral {utils.inr(amt)} seized.")


# ----------------------------------------------------------------------
# Display
# ----------------------------------------------------------------------
def collateral_text(loan):
    state = "SEIZED" if loan.collateral_state == "seized" else loan.collateral_state
    return f"{utils.fmt_inr(loan.collateral)} ({state})"


def display_loans_for_account(acc):
    loans = get_loans_for_account(acc)
    print(f"\n=== Loans for Account {acc.account_number} (amounts in Rs.) ===")
    if not loans:
        print("No loans.")
        return
    print(f"{'Loan ID':<8}{'Principal':>13}{'To be paid':>14}{'Remaining':>13}"
          f"  {'Due date':<13}{'Collateral':<24}Status")
    print("-" * 102)
    for l in loans:
        print(f"{l.loan_id:<8}{utils.fmt_inr(l.principal):>13}{utils.fmt_inr(l.total_payable):>14}"
              f"{utils.fmt_inr(loan_remaining(l)):>13}  {str(l.due_date):<13}"
              f"{collateral_text(l):<24}{loan_status(l)}")
