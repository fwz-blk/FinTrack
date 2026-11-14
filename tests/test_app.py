from app.extensions import db
from app.models import User


def test_public_pages_render(client):
    for path in ("/", "/features", "/about", "/login", "/register"):
        assert client.get(path).status_code == 200


def test_protected_pages_redirect_when_logged_out(client):
    for path in ("/dashboard", "/transactions", "/budgets", "/goals", "/reports", "/settings"):
        assert client.get(path).status_code == 302


def test_registration_logs_user_in(client, app):
    response = client.post(
        "/register",
        data={
            "name": "Test User",
            "email": "test@example.com",
            "password": "Password1",
            "confirm_password": "Password1",
        },
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
    with app.app_context():
        assert User.query.filter_by(email="test@example.com").one()


def test_user_can_add_transaction(client, app):
    client.post(
        "/register",
        data={
            "name": "Test User",
            "email": "test@example.com",
            "password": "Password1",
            "confirm_password": "Password1",
        },
    )
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
