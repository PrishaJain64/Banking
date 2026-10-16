import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer,SimpleHTTPRequestHandler

import config
import utils
from models import AccountNode
from transactionsOps import (add_transaction, get_balance, get_transactions_for_account,
                             CREDIT_TYPES)
from loanOps import (calculate_loan, create_loan, get_available_balance, get_bank_funds,
                     get_loans_for_account, get_reserved_collateral, loan_remaining,
                     loan_status, collateral_text, process_overdue_loans, repay_loan_amount)

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
PORT = 8000


class ApiError(Exception):
    pass


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------
def need_login():
    if config.current is None:
        raise ApiError("No account signed in. Please use 'Sign In' first.")
    return config.current


def amount_of(body, key="amount"):
    try:
        amt = round(float(body.get(key, "")), 2)
    except (TypeError, ValueError):
        raise ApiError("Invalid amount.")
    if amt <= 0:
        raise ApiError("Amount must be greater than zero.")
    return amt


def whoami():
    c = config.current
    return {"account_number": c.account_number, "name": c.name} if c else None


def loan_row(l):
    return {
        "loan_id": l.loan_id, "account": l.account_number,
        "principal": utils.fmt_inr(l.principal),
        "total_payable": utils.fmt_inr(l.total_payable),
        "remaining": utils.fmt_inr(loan_remaining(l)),
        "remaining_raw": loan_remaining(l),
        "due_date": str(l.due_date),
        "collateral": collateral_text(l),
        "status": loan_status(l),
    }


# ----------------------------------------------------------------------
# customer actions
# ----------------------------------------------------------------------
def open_account(b):
    name = str(b.get("name", "")).strip()
    if not name:
        raise ApiError("Name cannot be empty.")
    try:
        dob = datetime.strptime(str(b.get("dob", "")), "%Y-%m-%d").date()
    except ValueError:
        raise ApiError("Invalid date of birth.")
    if utils.calculate_age(dob) < 18:
        raise ApiError("You must be 18 or older to open an account.")
    aadhar = str(b.get("aadhar", "")).strip().replace(" ", "")
    if not (aadhar.isdigit() and len(aadhar) == 12):
        raise ApiError("Invalid Aadhar number (12 digits needed).")
    try:
        acc_type = config.ACCOUNT_TYPES[int(b.get("type"))]
    except (TypeError, ValueError, KeyError):
        raise ApiError("Invalid account type.")
    password = str(b.get("password", ""))
    if len(password) < 4:
        raise ApiError("Password must be at least 4 characters.")
    num = utils.next_account_number()
    config.accounts.insert(AccountNode(num, utils.hash_password(password), name, dob, aadhar, acc_type))
    return {"message": f"Account created successfully! Your account number is {num}."}


def sign_in(b):
    if config.current is not None:
        raise ApiError(f"Already signed in as {config.current.account_number}. Log out first.")
    try:
        num = int(b.get("account_number"))
    except (TypeError, ValueError):
        raise ApiError("Invalid account number.")
    acc = config.accounts.search(num)
    if acc is None or acc.password != utils.hash_password(str(b.get("password", ""))):
        raise ApiError("Invalid account number or password.")
    config.current = acc
    return {"message": f"Welcome, {acc.name}!"}


def logout(b):
    if config.current is None:
        raise ApiError("No account is signed in.")
    num = config.current.account_number
    config.current = None
    return {"message": f"Account {num} logged out."}


def deposit(b):
    acc = need_login()
    amt = amount_of(b)
    tid = utils.next_txn_id()
    add_transaction(tid, "deposit", amt, account_num=acc.account_number)
    return {"message": f"Deposited {utils.inr(amt)}. Transaction ID: {tid}. "
                       f"New balance: {utils.inr(get_balance(acc))}"}


def withdraw(b):
    acc = need_login()
    amt = amount_of(b)
    available = get_available_balance(acc)
    if amt > available:
        reserved = get_reserved_collateral(acc)
        if reserved > 0:
            raise ApiError(f"Insufficient available balance. {utils.inr(reserved)} is reserved as "
                           f"loan collateral; you can withdraw up to {utils.inr(available)}.")
        raise ApiError("Insufficient balance.")
    tid = utils.next_txn_id()
    add_transaction(tid, "withdraw", amt, account_num=acc.account_number)
    return {"message": f"Withdrew {utils.inr(amt)}. Transaction ID: {tid}. "
                       f"New balance: {utils.inr(get_balance(acc))}"}


def transfer(b):
    acc = need_login()
    try:
        target = int(b.get("receiver"))
    except (TypeError, ValueError):
        raise ApiError("Invalid account number.")
    if target == acc.account_number:
        raise ApiError("Cannot transfer to your own account.")
    receiver = config.accounts.search(target)
    if receiver is None:
        raise ApiError("Receiver account not found.")
    amt = amount_of(b)
    available = get_available_balance(acc)
    if amt > available:
        reserved = get_reserved_collateral(acc)
        if reserved > 0:
            raise ApiError(f"Insufficient available balance. {utils.inr(reserved)} is reserved as "
                           f"loan collateral; you can transfer up to {utils.inr(available)}.")
        raise ApiError("Insufficient balance.")
    tid = utils.next_txn_id()
    add_transaction(tid, "transfer", amt, sender=acc.account_number, receiver=receiver.account_number)
    return {"message": f"Transferred {utils.inr(amt)} to account {target}. Transaction ID: {tid}. "
                       f"New balance: {utils.inr(get_balance(acc))}"}


def status(b):
    acc = need_login()
    txns = []
    for t in get_transactions_for_account(acc):
        if t.txn_type == "transfer":
            role = "Sender" if t.sender_acc == acc.account_number else "Receiver"
            sign = "-" if role == "Sender" else "+"
        else:
            role = "Self"
            sign = "+" if t.txn_type in CREDIT_TYPES else "-"
        txns.append({"id": t.txn_id, "type": t.txn_type, "sender": t.sender_acc or "-",
                     "receiver": t.receiver_acc or "-", "amount": sign + f"{t.amount:.2f}",
                     "role": role, "loan": t.loan_id or "-", "time": t.timestamp})
    return {"account": {
        "Account Number": acc.account_number, "Account Type": acc.acc_type,
        "Full Name": acc.name, "Date of Birth": acc.dob.strftime("%d-%m-%Y"),
        "Aadhar Number": "XXXXXXXX" + acc.aadhar[-4:],
        "Current Balance": utils.inr(get_balance(acc)),
        "Reserved (loan collateral)": utils.inr(get_reserved_collateral(acc)),
        "Available to withdraw": utils.inr(get_available_balance(acc)),
    }, "transactions": txns, "loans": [loan_row(l) for l in get_loans_for_account(acc)]}


def loan_info(b):
    need_login()
    return {"tiers": [{"max_months": m, "rate": r, "collateral": int(f * 100)}
                      for m, r, f in config.LOAN_TIERS],
            "max_months": config.MAX_LOAN_MONTHS}


def _quote(acc, b):
    if any(loan_status(l) == "Overdue" for l in get_loans_for_account(acc)):
        raise ApiError("You have an overdue loan. Clear it before applying for a new one.")
    principal = amount_of(b)
    try:
        months = int(b.get("months"))
    except (TypeError, ValueError):
        raise ApiError("Invalid number of months.")
    if not 1 <= months <= config.MAX_LOAN_MONTHS:
        raise ApiError(f"Months must be between 1 and {config.MAX_LOAN_MONTHS}.")
    return calculate_loan(principal, months)


def loan_quote(b):
    acc = need_login()
    q = _quote(acc, b)
    available = get_available_balance(acc)
    return {"quote": {
        "Amount": utils.inr(q["principal"]), "Period": f"{q['months']} months",
        "Interest rate": f"{q['rate']}% per year", "Total interest": utils.inr(q["interest"]),
        "Total to repay": f"{utils.inr(q['total_payable'])} (about {utils.inr(q['monthly'])} / month)",
        "Collateral needed": utils.inr(q["collateral"]),
        "Your available balance": utils.inr(available)},
        "eligible": available >= q["collateral"] and q["principal"] <= get_bank_funds(),
        "reason": ("Not fit for this loan: not enough funds in your account to reserve as collateral."
                   if available < q["collateral"] else
                   "The bank does not have enough funds to give this loan right now."
                   if q["principal"] > get_bank_funds() else "")}


def apply_loan(b):
    acc = need_login()
    q = _quote(acc, b)
    if get_available_balance(acc) < q["collateral"]:
        raise ApiError("Not fit for this loan: not enough funds to reserve as collateral.")
    if q["principal"] > get_bank_funds():
        raise ApiError("The bank does not have enough funds to give this loan right now.")
    loan, tid = create_loan(acc, q)
    return {"message": f"Loan {loan.loan_id} approved. {utils.inr(loan.principal)} credited "
                       f"(Transaction ID: {tid}). {utils.inr(loan.collateral)} is reserved as "
                       f"collateral. Due date: {loan.due_date}."}


def my_pending_loans(b):
    acc = need_login()
    return {"loans": [loan_row(l) for l in get_loans_for_account(acc) if loan_remaining(l) > 0],
            "available": utils.inr(get_available_balance(acc))}


def repay_loan(b):
    acc = need_login()
    loan = config.loans.get(str(b.get("loan_id", "")).upper())
    if loan is None or loan.account_number != acc.account_number or loan_remaining(loan) <= 0:
        raise ApiError("Invalid loan ID.")
    amt = amount_of(b)
    remaining = loan_remaining(loan)
    if amt > remaining:
        raise ApiError(f"You only owe {utils.inr(remaining)} on this loan.")
    available = get_available_balance(acc)
    pays_off = amt >= remaining
    limit = available + (loan.collateral if pays_off and loan.collateral_state == "reserved" else 0)
    if amt > limit:
        raise ApiError(f"Insufficient available balance (you can repay up to "
                       f"{utils.inr(max(limit, 0))}). Collateral reserved for your loans cannot "
                       "be used for part-payments.")
    tid = repay_loan_amount(acc, loan, amt)
    msg = f"Repaid {utils.inr(amt)}. Transaction ID: {tid}. New balance: {utils.inr(get_balance(acc))}. "
    left = loan_remaining(loan)
    if left <= 0:
        msg += f"Loan {loan.loan_id} fully repaid."
        if loan.collateral_state == "released":
            msg += f" Collateral {utils.inr(loan.collateral)} released."
    else:
        msg += f"Remaining on {loan.loan_id}: {utils.inr(left)}"
    return {"message": msg}


# ----------------------------------------------------------------------
# bank actions
# ----------------------------------------------------------------------
def bank_funds(b):
    return {"info": {"Initial funds": utils.inr(config.BANK_INITIAL_FUNDS),
                     "Current funds": utils.inr(get_bank_funds())}}


def bank_pending(b):
    pending = [l for l in config.loans.values() if loan_remaining(l) > 0]
    return {"loans": [loan_row(l) for l in pending],
            "total": utils.inr(sum(loan_remaining(l) for l in pending))}


ACTIONS = {
    "open_account": open_account, "sign_in": sign_in, "logout": logout,
    "deposit": deposit, "withdraw": withdraw, "transfer": transfer, "status": status,
    "loan_info": loan_info, "loan_quote": loan_quote, "apply_loan": apply_loan,
    "my_pending_loans": my_pending_loans, "repay_loan": repay_loan,
    "bank_funds": bank_funds, "bank_pending": bank_pending,
    "whoami": lambda b: {},
}

MIME = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
        ".js": "application/javascript; charset=utf-8", ".png": "image/png", ".svg": "image/svg+xml"}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, payload, ctype="application/json; charset=utf-8"):
        data = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
            path = "/index.html"
        full = os.path.normpath(os.path.join(WEB_DIR, path.lstrip("/")))
        if not full.startswith(WEB_DIR) or not os.path.isfile(full):
            return self._send(404, {"ok": False, "error": "Not found"})
        with open(full, "rb") as f:
            self._send(200, f.read(), MIME.get(os.path.splitext(full)[1], "application/octet-stream"))

    def do_POST(self):
        name = self.path.split("?")[0].replace("/api/", "", 1)
        fn = ACTIONS.get(name)
        if fn is None:
            return self._send(404, {"ok": False, "error": "Unknown action"})
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
            process_overdue_loans()
            result = fn(body)
            result.update(ok=True, user=whoami())
            self._send(200, result)
        except ApiError as e:
            self._send(200, {"ok": False, "error": str(e), "user": whoami()})
        except Exception as e:  # keep the server alive on unexpected errors
            self._send(500, {"ok": False, "error": f"Server error: {e}", "user": whoami()})

    def log_message(self, *args):
        pass



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Banking server running on port {port}")
    server.serve_forever()

