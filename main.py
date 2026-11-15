import database as db
from datetime import date, datetime


def get_amount():
    while True:
        try:
            amount = float(input("Amount: "))
            if amount <= 0:
                print("Amount must be positive.")
                continue
            return amount
        except ValueError:
            print("Enter a valid number.")


def get_date():
    raw = input("Date (YYYY-MM-DD, Enter for today): ").strip()
    if not raw:
        return date.today().isoformat()
    try:
        datetime.strptime(raw, "%Y-%m-%d")
        return raw
    except ValueError:
        print("Invalid date, using today.")
        return date.today().isoformat()


def add():
    amount = get_amount()
    category = input("Category (food, travel, etc.): ").strip() or "Other"
    description = input("Description: ").strip()
    db.add_expense(amount, category, description, get_date())
    print("Expense added.")


def view():
    rows = db.get_all_expenses()
    if not rows:
        print("No expenses yet.")
        return
    print(f"\n{'#':<4}{'Date':<12}{'Category':<12}{'Amount':<10}Description")
    print("-" * 55)
    for n, (id_, amount, cat, desc, d) in enumerate(rows, start=1):
        print(f"{n:<4}{d:<12}{cat:<12}{amount:<10.2f}{desc}")


def delete():
    rows = db.get_all_expenses()
    try:
        n = int(input("Row # to delete: "))
        if not 1 <= n <= len(rows):
            raise ValueError
    except ValueError:
        print("Invalid row number.")
        return
    db.delete_expense(rows[n - 1][0])
    print("Deleted.")


def summary():
    print("\nTotal by category:")
    for cat, total in db.total_by_category():
        print(f"  {cat:<12}{total:.2f}")
    month = date.today().strftime("%Y-%m")
    print(f"\nThis month ({month}): {db.monthly_total(month):.2f}")


def main():
    db.init_db()
    actions = {"1": add, "2": view, "3": delete, "4": summary}
    while True:
        print("\n--- Expense Tracker ---")
        print("1. Add expense\n2. View all\n3. Delete expense\n4. Summary\n5. Exit")
        choice = input("Choose: ").strip()
        if choice == "5":
            print("Bye!")
            break
        action = actions.get(choice)
        action() if action else print("Invalid choice.")


if __name__ == "__main__":
    main()
