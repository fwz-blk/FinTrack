# FinTrack

FinTrack is a multi-user personal finance manager built with Flask, Jinja templates, vanilla CSS/JavaScript, and SQLite or PostgreSQL. It provides authenticated account management, user-scoped financial data, a responsive Metallic Chic interface, and a versioned JSON API.

## Features

- Dashboard with balances, income, expenses, savings rate, trends, budget alerts, goals, and upcoming bills
- Transaction CRUD, filtering, pagination, CSV import/export, recurring flags, attachments, and ownership protection
- Budgets with category spending, periods, warning thresholds, and rollover support
- Savings goals with contributions, progress tracking, target dates, archive/restore, and completion state
- Recurring bills with due dates, paid state, generated transactions, and duplicate prevention
- Reports with date filters, category/account breakdowns, CSV/PDF export, and print view
- Settings for profile, password, preferences, data export, anonymization, and account deletion
- CSRF protection, secure sessions, password hashing, rate limits, audit logging, ownership checks, and friendly error pages
- REST endpoints under `/api/v1` with consistent `{data, errors, meta}` responses

## Technology

- **Backend:** Flask, SQLAlchemy, Flask-Migrate, Flask-WTF
- **Frontend:** Jinja, vanilla JavaScript, custom CSS, selective Bootstrap utilities
- **Database:** SQLite for local/demo use; PostgreSQL recommended for production
- **Production server:** Gunicorn
- **Exports:** ReportLab PDF and CSV
- **Testing:** pytest

## Local setup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask --app app db upgrade
flask --app app run --debug
```

Open `http://127.0.0.1:5000`.

Run the test suite:

```bash
python -m pytest -q
```

## Demo data

Create or refresh the local demo account and representative transactions, budgets, goals, and bills:

```bash
flask --app app seed-demo
```

The demo credentials are maintained for the presentation environment and should not be reused in production.

## REST API

Authenticated JSON endpoints are available at:

```text
/api/v1/transactions
/api/v1/budgets
/api/v1/goals
/api/v1/bills
/api/v1/dashboard
/api/v1/reports
/api/v1/settings
```

Interactive documentation is available at `/api/docs`; the OpenAPI contract is in `openapi.yaml`. API authentication uses the existing Flask session cookie. Write requests require the CSRF token header.

## Deployment

Configure production environment variables:

```text
SECRET_KEY=<long-random-production-secret>
DATABASE_URL=<persistent-database-url>
FLASK_ENV=production
FLASK_DEBUG=0
SESSION_COOKIE_SECURE=1
RATELIMIT_STORAGE_URI=<shared-redis-url>
```

Apply migrations during the release and start Gunicorn:

```bash
flask --app app db upgrade
gunicorn --workers 2 --bind 0.0.0.0:$PORT wsgi:application
```

The repository includes a `Procfile` and a `/health` endpoint for platform health checks. Use persistent PostgreSQL storage for public deployments. SQLite is suitable for local development or a single-instance university demo only. Configure persistent object storage for uploaded attachments if the hosting platform has ephemeral disks.

## Current limitations

- Google sign-in is not implemented.
- Password-reset and email-verification links use development flash messages because no email provider is configured.
- Flask-Limiter defaults to in-memory storage; use Redis for multiple production instances.
- The frontend is server-rendered; the API migration is incremental and preserves server-rendered fallbacks.
