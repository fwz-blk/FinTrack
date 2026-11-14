# FinTrack

FinTrack is a Flask personal-finance application with server-rendered pages and a versioned JSON API at `/api/v1`.

## Local setup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask --app app db upgrade
flask --app app run --debug
```

Run tests with:

```bash
python -m pytest -q
```

## Deployment

Configure a strong `SECRET_KEY`, a persistent `DATABASE_URL`, `FLASK_ENV=production`, `FLASK_DEBUG=0`, and `SESSION_COOKIE_SECURE=1` when HTTPS is enabled. Apply migrations during release:

```bash
flask --app app db upgrade
gunicorn --workers 2 --bind 0.0.0.0:$PORT wsgi:application
```

The repository includes a `Procfile` with the Gunicorn command and `/health` for service checks. The default SQLite database is suitable for the university demo; use a managed database if the deployment platform provides one. For multiple application instances, configure `RATELIMIT_STORAGE_URI` to a shared Redis storage.

## API

The API uses the logged-in Flask session and returns `{data, errors, meta}` JSON responses. Documentation is available at `/api/docs`, with the contract in `openapi.yaml`.
