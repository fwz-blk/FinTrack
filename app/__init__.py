import os
from pathlib import Path

from datetime import date, timedelta

from flask import Flask, render_template, session
from .extensions import csrf, db, migrate


def create_app(test_config=None):
    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder="../static",
        template_folder="templates",
    )
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL",
            "sqlite:///" + str(Path(app.instance_path) / "finance.db"),
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        ENV=os.environ.get("FLASK_ENV", "development"),
        DEBUG=os.environ.get("FLASK_DEBUG", "0") == "1",
        PERMANENT_SESSION_LIFETIME=timedelta(days=30),
        SESSION_REFRESH_EACH_REQUEST=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "0") == "1",
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,
    )
    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    from .cli import register_commands

    register_commands(app)

    from .auth.routes import register as register_auth
    from .budgets.routes import register as register_budgets
    from .dashboard.routes import register as register_dashboard
    from .goals.routes import register as register_goals
    from .public.routes import register as register_public
    from .reports.routes import register as register_reports
    from .settings.routes import register as register_settings
    from .transactions.routes import register as register_transactions

    register_public(app)
    register_auth(app)
    register_dashboard(app)
    register_transactions(app)
    register_budgets(app)
    register_goals(app)
    register_reports(app)
    register_settings(app)

    @app.before_request
    def refresh_current_user():
        if "user_id" in session:
            session.permanent = True

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    @app.context_processor
    def shared_context():
        return {
            "today": date.today(),
            "implemented_pages": {
                "dashboard",
                "transactions",
                "budgets",
                "goals",
                "reports",
                "settings",
                "bills",
            },
            "nav_items": [
                ("dashboard", "◉", "Dashboard"),
                ("transactions", "⇄", "Transactions"),
                ("budgets", "◔", "Budgets"),
                ("goals", "◎", "Goals"),
                ("bills", "⟳", "Bills"),
                ("reports", "⌁", "Reports"),
            ],
        }

    return app


app = create_app()
