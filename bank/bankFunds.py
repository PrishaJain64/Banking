# ----------------------------------------------------------------------
# Bank 1. Show current funds
# ----------------------------------------------------------------------
import config
from utils import *
from loanOps import get_bank_funds

def show_bank_funds():
    print("\n=== Bank Funds ===")
    print(f"Initial funds : {inr(config.BANK_INITIAL_FUNDS)}")
    print(f"Current funds : {inr(get_bank_funds())}")
