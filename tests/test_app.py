import io
from datetime import date, timedelta

from app.extensions import db
from app.models import Bill, Budget, Goal, GoalContribution, Transaction, User


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
    for path in ("/", "/features", "/about", "/help", "/terms", "/privacy", "/login", "/register"):
        assert client.get(path).status_code == 200


def test_protected_pages_redirect_when_logged_out(client):
    for path in ("/dashboard", "/transactions", "/budgets", "/goals", "/reports", "/settings", "/bills"):
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


def test_goal_progress_contributions_history_and_crud(client, app):
    register_user(client)
    response = client.post(
        "/goals",
        data={
            "name": "Emergency fund",
            "target_amount": "100",
            "saved_amount": "20",
            "deadline": "2027-11-14",
        },
    )
    assert response.status_code == 302
    with app.app_context():
        goal_id = db.session.execute(db.select(Goal)).scalar_one().id
    response = client.post(
        f"/goals/{goal_id}/contributions",
        data={"amount": "30", "date": "2026-11-14", "note": "First deposit"},
    )
    assert response.status_code == 302
    response = client.get("/goals")
    assert b"$50.00 / $100.00" in response.data
    assert b"50%" in response.data
    assert b"First deposit" in response.data
    with app.app_context():
        assert db.session.execute(db.select(GoalContribution)).scalar_one()
    response = client.post(
        f"/goals/{goal_id}/edit",
        data={
            "name": "Updated fund",
            "target_amount": "200",
            "saved_amount": "20",
            "deadline": "2028-11-14",
        },
    )
    assert response.status_code == 302
    response = client.post(f"/goals/{goal_id}/archive")
    assert response.status_code == 302
    assert b"Archived" in client.get("/goals?show_archived=1").data
    response = client.post(f"/goals/{goal_id}/delete")
    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(Goal, goal_id) is None


def test_dashboard_uses_real_period_data_and_empty_states(client, app):
    register_user(client)
    client.post(
        "/transactions",
        data={
            "transaction_type": "income",
            "amount": "1000",
            "category": "Salary",
            "account": "Bank",
            "date": "2026-11-14",
        },
    )
    client.post(
        "/transactions",
        data={
            "transaction_type": "expense",
            "amount": "250",
            "category": "Food",
            "account": "Card",
            "date": "2026-11-14",
        },
    )
    response = client.get("/dashboard?period=this_month")
    assert response.status_code == 200
    assert b"$750.00" in response.data
    assert b"$1,000.00" in response.data
    assert b"Food 100%" in response.data
    assert b"75.0%" in response.data

    response = client.get("/dashboard?start=2026-11-01&end=2026-11-10")
    assert response.status_code == 200
    assert b"No transactions in this period" in response.data
    assert b"No expense data for this period" in response.data


def test_reports_are_filtered_exportable_printable_and_user_scoped(client, app):
    register_user(client, email="reports@example.com")
    client.post(
        "/transactions",
        data={
            "transaction_type": "income",
            "amount": "500",
            "category": "Salary",
            "account": "Bank",
            "date": "2026-11-14",
        },
    )
    client.post(
        "/transactions",
        data={
            "transaction_type": "expense",
            "amount": "125",
            "category": "Food",
            "account": "Card",
            "date": "2026-11-14",
        },
    )
    response = client.get("/reports?filter=current_month")
    assert response.status_code == 200
    assert b"Food" in response.data
    assert b"Salary" not in response.data
    assert b"Income $500.00" in response.data
    response = client.get("/reports/export.csv?filter=current_month")
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert b"Food,125.00" in response.data
    response = client.get("/reports/export.pdf?filter=current_month")
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF")
    response = client.get("/reports/print?filter=current_month")
    assert response.status_code == 200
    assert b"FinTrack Report" in response.data
    client.get("/logout")
    register_user(client, name="Other User", email="other-reports@example.com")
    response = client.get("/reports?filter=current_month")
    assert response.status_code == 200
    assert b"Food" not in response.data
    assert b"Salary" not in response.data


def test_settings_persist_security_export_and_data_controls(client, app):
    register_user(client, email="settings@example.com")
    response = client.post(
        "/settings",
        data={
            "action": "profile",
            "name": "Updated Name",
            "email": "settings-new@example.com",
            "currency": "EUR",
            "timezone": "Europe/London",
        },
    )
    assert response.status_code == 302
    response = client.post(
        "/settings",
        data={"action": "preferences", "notifications": "on"},
    )
    assert response.status_code == 302
    response = client.post(
        "/settings",
        data={
            "action": "password",
            "current_password": "Password1",
            "new_password": "NewPassword2",
            "confirm_password": "NewPassword2",
        },
    )
    assert response.status_code == 302
    client.get("/logout")
    response = client.post(
        "/login",
        data={"email": "settings-new@example.com", "password": "NewPassword2"},
    )
    assert response.status_code == 302
    response = client.get("/settings")
    assert b"Updated Name" in response.data
    assert b"Europe/London" in response.data
    response = client.get("/settings/export")
    assert response.status_code == 200
    assert response.mimetype == "application/json"
    assert b"settings-new@example.com" in response.data

    response = client.post(
        "/settings",
        data={"action": "anonymize", "confirmation": "ANONYMIZE"},
    )
    assert response.status_code == 302
    with app.app_context():
        user = User.query.one()
        assert user.name == "Deleted User"
        assert user.email.endswith("@example.invalid")
        assert user.transactions == []


def test_settings_can_permanently_delete_account(client, app):
    register_user(client, email="delete-settings@example.com")
    with app.app_context():
        user_id = User.query.one().id
    response = client.post(
        "/settings",
        data={"action": "delete", "confirmation": "DELETE"},
    )
    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(User, user_id) is None
    assert client.get("/settings").status_code == 302


def test_bills_persist_show_overdue_and_generate_recurring_transactions(client, app):
    register_user(client, email="bills@example.com")
    response = client.post(
        "/bills",
        data={
            "name": "Rent",
            "amount": "800",
            "due_date": (date.today() - timedelta(days=1)).isoformat(),
            "recurrence": "monthly",
            "category": "Housing",
            "account": "Bank",
        },
    )
    assert response.status_code == 302
    response = client.get("/bills")
    assert response.status_code == 200
    assert b"Overdue" in response.data
    response = client.get("/dashboard")
    assert response.status_code == 200
    response = client.get("/dashboard")
    assert response.status_code == 200
    with app.app_context():
        bill = Bill.query.one()
        assert bill.paid is True
        assert Transaction.query.filter_by(bill_id=bill.id).count() == 1
        assert bill.due_date > date.today()


def test_v1_api_is_json_authenticated_and_user_scoped(client, app):
    register_user(client, email="api-one@example.com")
    response = client.post(
        "/api/v1/transactions",
        json={
            "type": "expense",
            "amount": "12.50",
            "category": "Food",
            "account": "Card",
            "date": "2026-11-14",
        },
    )
    assert response.status_code == 201
    assert response.json["data"]["amount"] == "12.50"
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 200
    assert response.json["errors"] == {}
    client.get("/logout")
    register_user(client, email="api-two@example.com")
    response = client.get("/api/v1/transactions")
    assert response.status_code == 200
    assert response.json["data"] == []
    response = client.get("/api/v1/transactions/1")
    assert response.status_code == 404
    client.get("/logout")
    response = client.get("/api/v1/transactions")
    assert response.status_code == 401
