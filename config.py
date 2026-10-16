from hashtables import *

# NOTE: shared *objects* (accounts, transactions, loans) can be star-imported because
# they are never re-assigned. The scalars that DO change (current, account_counter,
# txn_counter, loan_counter) must always be used as config.<name>; a star-import would
# only copy their value. __all__ below deliberately leaves them out.
__all__ = ["ACCOUNT_TYPES", "BANK_INITIAL_FUNDS", "MAX_LOAN_MONTHS", "LOAN_TIERS",
           "accounts", "transactions", "loans"]

ACCOUNT_TYPES = {1: "Savings", 2: "Salary", 3: "Current"}

# ----------------------------------------------------------------------
# Bank / loan settings
# ----------------------------------------------------------------------
BANK_INITIAL_FUNDS = 1000000.0     # Rs. 10,00,000

# (up to N months, annual simple interest %, collateral as a fraction of the loan)
# Longer loans are riskier for the bank -> higher interest and higher collateral.
LOAN_TIERS = [
    (6,  8.0, 0.20),
    (12, 10.0, 0.25),
    (24, 12.0, 0.30),
    (36, 14.0, 0.35),
]
MAX_LOAN_MONTHS = LOAN_TIERS[-1][0]

# ----------------------------------------------------------------------
# Global state
# ----------------------------------------------------------------------
accounts = AccountHashTable()
transactions = {}          # central store: transaction id -> TransactionNode (O(1))
loans = {}                 # central store: loan id -> LoanNode (O(1))
current = None             # signed-in account node (None = logged out)
account_counter = 1000     # auto-generated account numbers: 1001, 1002, ...
txn_counter = 0            # transaction ids: T_1, T_2, ...
loan_counter = 0           # loan ids: L_1, L_2, ...
