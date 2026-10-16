from datetime import date, datetime
from utils import *
from config import *
from models import *

def open_account():
    print("\n--- Open Account ---")
    name = input("Full legal name: ").strip()
    if not name:
        print("Name cannot be empty.")
        return

    dob_str = input("Date of birth (DD-MM-YYYY): ").strip()
    try:
        dob = datetime.strptime(dob_str, "%d-%m-%Y").date()
    except ValueError:
        print("Invalid date format.")
        return
    if calculate_age(dob) < 18:
        print("You must be 18 or older to open an account.")
        return

    aadhar = input("Aadhar card number (12 digits): ").strip().replace(" ", "")
    if not (aadhar.isdigit() and len(aadhar) == 12):
        print("Invalid Aadhar number.")
        return

    print("Account type:  1. Savings   2. Salary   3. Current")
    try:
        t = int(input("Choose type: "))
        acc_type = ACCOUNT_TYPES[t]
    except (ValueError, KeyError):
        print("Invalid account type.")
        return

    password = input("Set a password: ")
    if len(password) < 4:
        print("Password must be at least 4 characters.")
        return

    acc_num = next_account_number()
    node = AccountNode(acc_num, hash_password(password), name, dob, aadhar, acc_type)
    accounts.insert(node)
    print(f"Account created successfully! Your account number is {acc_num}.")
