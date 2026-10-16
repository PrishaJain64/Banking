import config
from models import *
from utils import *
from hashtables import *
from transactionsOps import *
from loanOps import process_overdue_loans
from auth import *
from customer.openAccount import *
from customer.deposit import *
from customer.withdraw import *
from customer.accountStatus import *
from customer.transferMoney import *
from customer.applyLoan import *
from customer.repayLoan import *
from bank.bankFunds import *
from bank.pendingLoans import *

# ----------------------------------------------------------------------
# Customer menu
# ----------------------------------------------------------------------
def show_customer_menu():
    cur = config.current
    status = f"Signed in: {cur.account_number} ({cur.name})" if cur else "Not signed in"
    print("\n" + "=" * 40)
    print("          CUSTOMER MENU")
    print(f"   [{status}]")
    print("=" * 40)
    print("1. Open Account")
    print("2. Deposit Money")
    print("3. Withdraw Money")
    print("4. Check Account Status")
    print("5. Transfer Money")
    print("6. Logout")
    print("7. Sign In")
    print("8. Apply for Loan")
    print("9. Repay Loan")
    print("0. Back")


def customer_menu():
    actions = {
        "1": open_account,
        "2": deposit_money,
        "3": withdraw_money,
        "4": check_account_status,
        "5": transfer_money,
        "6": logout,
        "7": sign_in,
        "8": apply_for_loan,
        "9": repay_loan,
    }
    while True:
        process_overdue_loans()
        show_customer_menu()
        choice = input("Enter choice: ").strip()
        if choice == "0":
            if config.current is not None:
                logout()
            return
        action = actions.get(choice)
        if action:
            action()
        else:
            print("Invalid choice. Try again.")


# ----------------------------------------------------------------------
# Bank menu
# ----------------------------------------------------------------------
def bank_menu():
    actions = {
        "1": show_bank_funds,
        "2": show_pending_loans,
    }
    while True:
        process_overdue_loans()
        print("\n" + "=" * 40)
        print("            BANK MENU")
        print("=" * 40)
        print("1. Show current funds in bank")
        print("2. Show pending loans")
        print("0. Back")
        choice = input("Enter choice: ").strip()
        if choice == "0":
            return
        action = actions.get(choice)
        if action:
            action()
        else:
            print("Invalid choice. Try again.")


# ----------------------------------------------------------------------
# Role selection
# ----------------------------------------------------------------------
def main():
    while True:
        print("\n" + "=" * 40)
        print("          BANKING SYSTEM")
        print("=" * 40)
        print("Are you a bank or a customer?")
        print("1. Bank")
        print("2. Customer")
        print("0. Exit")
        choice = input("Enter choice: ").strip()
        if choice == "1":
            bank_menu()
        elif choice == "2":
            customer_menu()
        elif choice == "0":
            print("Thank you for banking with us. Goodbye!")
            break
        else:
            print("Invalid choice. Try again.")


if __name__ == "__main__":
    main()
