import io

from app.extensions import db
from app.models import Budget, Transaction, User


def register_user(client, name="Test User", email="test@example.com"):
    return client.post(
        "/register",
        data={
            "name": name,
            "email": email,
            "password": "Password1",
            "confirm_password": "Password1",
        },
    )


def test_public_pages_render(client):
    for path in ("/", "/features", "/about", "/login", "/register"):
        assert client.get(path).status_code == 200


def test_protected_pages_redirect_when_logged_out(client):
    for path in ("/dashboard", "/transactions", "/budgets", "/goals", "/reports", "/settings"):
        assert client.get(path).status_code == 302


def test_registration_logs_user_in(client, app):
    response = register_user(client)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
    with app.app_context():
        assert User.query.filter_by(email="test@example.com").one()


def test_user_can_add_transaction(client, app):
    register_user(client)
    response = client.post(
        "/transactions",
        data={
            "transaction_type": "income",
            "amount": "100.00",
            "category": "Salary",
            "account": "Bank",
            "date": "2026-11-14",
        },
    )
    assert response.status_code == 302
    with app.app_context():
        assert db.session.execute(db.select(User)).scalar_one().transactions


def test_transaction_crud_filters_export_and_delete(client, app):
    register_user(client)
    for index in range(11):
        response = client.post(
            "/transactions",
            data={
                "transaction_type": "expense",
                "amount": str(index + 1),
                "category": "Food",
                "account": "Card",
                "date": "2026-11-14",
                "note": f"Groceries {index}",
            },
        )
        assert response.status_code == 302
    response = client.get("/transactions?search=Groceries%2010&min_amount=10")
    assert response.status_code == 200
    assert b"Groceries 10" in response.data
    assert client.get("/transactions?page=2").status_code == 200
    with app.app_context():
        transaction = Transaction.query.order_by(Transaction.id).first()
        transaction_id = transaction.id
    response = client.post(
        f"/transactions/{transaction_id}/edit",
        data={
            "transaction_type": "income",
            "amount": "99.99",
            "category": "Salary",
            "account": "Bank",
            "date": "2026-11-14",
            "note": "Edited",
        },
    )
    assert response.status_code == 302
    response = client.get("/transactions/export")
    assert response.status_code == 200
    assert b"date,type,amount" in response.data
    response = client.post(
        "/transactions/import",
        data={
            "file": (io.BytesIO(b"date,type,amount,category,account,note\n2026-11-13,expense,4.50,Food,Cash,Imported\n"), "transactions.csv")
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 302
    with app.app_context():
        imported = Transaction.query.filter_by(note="Imported").one()
        transaction_ids = [str(imported.id)]
    response = client.post(
        "/transactions/bulk-delete",
        data={"transaction_ids": transaction_ids},
    )
    assert response.status_code == 302
    with app.app_context():
        assert Transaction.query.filter_by(note="Imported").first() is None


def test_transaction_ownership_is_enforced(client, app):
    register_user(client, email="first@example.com")
    client.post(
        "/transactions",
        data={
            "transaction_type": "expense",
            "amount": "10",
            "category": "Food",
            "account": "Cash",
            "date": "2026-11-14",
        },
    )
    with app.app_context():
        transaction_id = Transaction.query.one().id
    client.get("/logout")
    register_user(client, name="Second User", email="second@example.com")
    response = client.post(f"/transactions/{transaction_id}/delete")
    assert response.status_code == 404


def test_budget_spending_is_calculated_and_budget_crud_is_scoped(client, app):
    register_user(client)
    for category, amount in (("Food", "50"), ("Transport", "20")):
        client.post(
            "/transactions",
            data={
                "transaction_type": "expense",
                "amount": amount,
                "category": category,
                "account": "Card",
                "date": "2026-11-14",
            },
        )
    response = client.post(
        "/budgets",
        data={
            "name": "Food budget",
            "amount": "100",
            "category": "Food",
            "period": "monthly",
            "warning_threshold": "75",
            "rollover": "on",
        },
    )
    assert response.status_code == 302
    response = client.get("/budgets")
    assert b"$50.00 / $200.00" in response.data
    assert b"25%" in response.data
    with app.app_context():
        budget = Budget.query.one()
        budget_id = budget.id
    response = client.post(
        f"/budgets/{budget_id}/edit",
        data={
            "name": "Updated food budget",
            "amount": "200",
            "category": "Food",
            "period": "weekly",
            "warning_threshold": "80",
        },
    )
    assert response.status_code == 302
    response = client.post(f"/budgets/{budget_id}/delete")
    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(Budget, budget_id) is None
