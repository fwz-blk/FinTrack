from flask import Flask, render_template

app = Flask(__name__)

TRANSACTIONS = [
    {"type": "↑", "date": "12 Oct", "category": "Food", "account": "Cash", "note": "Lunch with friends", "amount": "-$18.50", "kind": "expense"},
    {"type": "↓", "date": "10 Oct", "category": "Salary", "account": "Bank", "note": "October salary", "amount": "+$4,800.00", "kind": "income"},
    {"type": "↑", "date": "09 Oct", "category": "Rent", "account": "Bank", "note": "Monthly rent", "amount": "-$900.00", "kind": "expense"},
    {"type": "↑", "date": "08 Oct", "category": "Transport", "account": "Card", "note": "Metro pass", "amount": "-$35.00", "kind": "expense"},
    {"type": "↑", "date": "06 Oct", "category": "Shopping", "account": "Card", "note": "Headphones", "amount": "-$79.99", "kind": "expense"},
    {"type": "↓", "date": "05 Oct", "category": "Freelance", "account": "Bank", "note": "Website project", "amount": "+$350.00", "kind": "income"},
    {"type": "↑", "date": "04 Oct", "category": "Bills", "account": "Bank", "note": "Electricity", "amount": "-$62.00", "kind": "expense"},
    {"type": "↑", "date": "02 Oct", "category": "Food", "account": "Cash", "note": "Groceries", "amount": "-$48.20", "kind": "expense"},
    {"type": "↑", "date": "01 Oct", "category": "Fun", "account": "Card", "note": "Movie night", "amount": "-$14.00", "kind": "expense"},
]

BUDGETS = [
    {"name": "Food", "spent": "$280 / $400", "percent": 70, "tone": "green"},
    {"name": "Transport", "spent": "$220 / $250", "percent": 88, "tone": "orange"},
    {"name": "Rent", "spent": "$900 / $900", "percent": 100, "tone": "green"},
    {"name": "Shopping", "spent": "$224 / $200", "percent": 112, "tone": "red"},
    {"name": "Entertainment", "spent": "$45 / $100", "percent": 45, "tone": "green"},
    {"name": "Utilities", "spent": "$96 / $150", "percent": 64, "tone": "green"},
]

GOALS = [
    {"name": "Emergency Fund", "deadline": "Due Dec 2026", "percent": "50%", "amount": "$500 / $1,000", "tone": ""},
    {"name": "New Laptop", "deadline": "Due Mar 2027", "percent": "50%", "amount": "$400 / $800", "tone": "blue"},
    {"name": "Holiday Trip", "deadline": "Completed", "percent": "100%", "amount": "$1,200 / $1,200", "tone": "green"},
]


@app.context_processor
def shared_context():
    return {
        "implemented_pages": {"dashboard", "transactions", "budgets", "goals", "reports", "settings"},
        "nav_items": [
            ("dashboard", "◉", "Dashboard"),
            ("transactions", "⇄", "Transactions"),
            ("categories", "◈", "Categories"),
            ("accounts", "♜", "Accounts"),
            ("budgets", "◔", "Budgets"),
            ("goals", "◎", "Goals"),
            ("bills", "⟳", "Bills"),
            ("reports", "⌁", "Reports"),
        ]
    }


@app.get("/")
def landing():
    return render_template("landing.html")


@app.get("/login")
def login():
    return render_template("login.html")


@app.get("/register")
def register():
    return render_template("register.html")


@app.get("/dashboard")
def dashboard():
    return render_template("dashboard.html", transactions=TRANSACTIONS)


@app.get("/transactions")
def transactions():
    return render_template("transactions.html", transactions=TRANSACTIONS)


@app.get("/budgets")
def budgets():
    return render_template("budgets.html", budgets=BUDGETS)


@app.get("/goals")
def goals():
    return render_template("goals.html", goals=GOALS)


@app.get("/reports")
def reports():
    return render_template("reports.html")


@app.get("/settings")
def settings():
    return render_template("settings.html")


if __name__ == "__main__":
    app.run(debug=True)
