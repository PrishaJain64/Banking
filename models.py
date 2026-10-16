from datetime import date, datetime

class TransactionNode:
    """Transaction structure (also usable as a linked-list / bucket node)."""

    def __init__(self, txn_id, account_num, txn_type, amount,
                 sender_acc=None, receiver_acc=None, loan_id=None):
        self.txn_id = txn_id                # T_<counter>
        self.account_num = account_num      # used for everything except transfer (None for transfer)
        # "deposit" / "withdraw" / "transfer" /
        # "loan_credit" / "loan_repay" / "collateral_seized"
        self.txn_type = txn_type
        self.amount = amount
        self.sender_acc = sender_acc        # transfer only (None otherwise)
        self.receiver_acc = receiver_acc    # transfer only (None otherwise)
        self.loan_id = loan_id              # set only for the loan_* / collateral_seized types
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class TxnIdNode:
    """Link in an account's chain of transaction ids (stores the id only)."""

    def __init__(self, txn_id):
        self.txn_id = txn_id
        self.next = None


class LoanIdNode:
    """Link in an account's chain of loan ids (stores the id only)."""

    def __init__(self, loan_id):
        self.loan_id = loan_id
        self.next = None


class LoanNode:
    """Loan structure. Paid / remaining amounts are NOT stored: they are calculated
    from the repayment transactions (see loanOps.loan_paid)."""

    def __init__(self, loan_id, account_number, principal, months, rate, interest,
                 total_payable, collateral, start_date, due_date):
        self.loan_id = loan_id              # L_<counter>
        self.account_number = account_number
        self.principal = principal          # money credited to the customer
        self.months = months
        self.rate = rate                    # annual simple interest %
        self.interest = interest            # total interest for the whole period
        self.total_payable = total_payable  # principal + interest
        self.collateral = collateral        # amount locked in the customer's account
        self.start_date = start_date
        self.due_date = due_date
        self.collateral_state = "reserved"  # "reserved" -> "released" (repaid) or "seized" (overdue)


class AccountNode:
    """Account structure."""

    def __init__(self, acc_num, password, name, dob, aadhar, acc_type):
        self.head = None                    # head of transaction-id chain (linked list)
        self.tail = None                    # tail pointer for O(1) append
        self.loan_head = None               # head of loan-id chain (linked list)
        self.loan_tail = None
        self.account_number = acc_num       # auto generated
        self.password = password            # stored as SHA-256 hash
        self.name = name
        self.dob = dob
        self.aadhar = aadhar
        self.acc_type = acc_type
        self.next = None                    # next in hash bucket chain

    def add_txn_id(self, txn_id):
        """Append a transaction id to this account's chain (oldest first)."""
        node = TxnIdNode(txn_id)
        if self.head is None:
            self.head = self.tail = node
        else:
            self.tail.next = node
            self.tail = node

    def add_loan_id(self, loan_id):
        """Append a loan id to this account's loan chain (oldest first)."""
        node = LoanIdNode(loan_id)
        if self.loan_head is None:
            self.loan_head = self.loan_tail = node
        else:
            self.loan_tail.next = node
            self.loan_tail = node
