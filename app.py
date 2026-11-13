import sqlite3
from datetime import date as current_date
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

def get_db_connection():
    connection = sqlite3.connect("expenses.db")
    connection.row_factory = sqlite3.Row
    return connection

def create_table():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL
        )
    """)
    columns = connection.execute("PRAGMA table_info(expenses)").fetchall()
    columns = connection.execute("PRAGMA table_info(expenses)").fetchall()
    if "date" not in [column["name"] for column in columns]:
        connection.execute(
            "ALTER TABLE expenses ADD COLUMN date TEXT NOT NULL DEFAULT 'Unknown'"
        )
    if "category" not in [column["name"] for column in columns]:
        connection.execute(
            "ALTER TABLE expenses ADD COLUMN category TEXT NOT NULL DEFAULT 'Other'"
        )

    connection.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            income REAL NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS starting_balance (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            amount REAL NOT NULL
        )
    """)

    connection.execute(
        "INSERT OR IGNORE INTO settings (id, income) VALUES (1, 5000.00)"
    )
    connection.execute(
        "INSERT OR IGNORE INTO starting_balance (id, amount) VALUES (1, 0.00)"
    )

    connection.commit()
    connection.close()

create_table()

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        amount = request.form.get("amount", "").strip()
        category = request.form.get("category", "Other")
        expense_date = request.form.get("date", "Unknown")

        if name and amount:
            connection = get_db_connection()
            connection.execute(
                "INSERT INTO expenses (name, amount, category, date) "
                "VALUES (?, ?, ?, ?)",
                (name, float(amount), category, expense_date)
            )
            connection.commit()
            connection.close()

        return redirect("/")

    selected_month = request.args.get("month")
    if not selected_month:
        selected_month = current_date.today().strftime("%Y-%m")

    connection = get_db_connection()
    expenses = connection.execute(
        "SELECT id, name, amount, category, date FROM expenses "
        "WHERE substr(date, 1, 7) = ? ORDER BY date DESC, id DESC",
        (selected_month,)
    ).fetchall()

    income = connection.execute(
        "SELECT income FROM settings WHERE id = 1"
    ).fetchone()["income"]

    starting_balance = connection.execute(
        "SELECT amount FROM starting_balance WHERE id = 1"
    ).fetchone()["amount"]

    total_expenses = connection.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses"
    ).fetchone()["total"]

    connection.close()

    monthly_expenses = sum(expense["amount"] for expense in expenses)
    balance = starting_balance + income - total_expenses

    return render_template(
        "index.html",
        expenses=expenses,
        income=income,
        starting_balance=starting_balance,
        total_expenses=total_expenses,
        balance=balance,
        selected_month=selected_month,
        monthly_expenses=monthly_expenses
    )

@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    connection = get_db_connection()
    connection.execute(
        "DELETE FROM expenses WHERE id = ?",
        (expense_id,)
    )
    connection.commit()
    connection.close()
    return redirect("/")

@app.route("/income", methods=["POST"])
def update_income():
    amount = request.form.get("income", "").strip()

    try:
        income = float(amount)
    except ValueError:
        return redirect("/")

    if income >= 0:
        connection = get_db_connection()
        connection.execute(
            "UPDATE settings SET income = ? WHERE id = 1",
            (income,)
        )
        connection.commit()
        connection.close()

        return redirect("/")


@app.route("/starting-balance", methods=["POST"])
def update_starting_balance():
    amount = request.form.get("starting_balance", "").strip()

    try:
        starting_balance = float(amount)
    except ValueError:
        return redirect("/")

    if starting_balance >= 0:
        connection = get_db_connection()
        connection.execute(
            "UPDATE starting_balance SET amount = ? WHERE id = 1",
            (starting_balance,)
        )
        connection.commit()
        connection.close()

    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)