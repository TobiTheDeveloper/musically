# Render Setup

The latest commit makes Render's **default** start command work:

`gunicorn your_application.wsgi`

You do **not** have to change the Start Command anymore. Just redeploy.

## Still recommended in Settings

| Field | Value |
|-------|--------|
| **Instance type** | Starter ($7/mo) or higher — not Free |
| `PYTHON_VERSION` | `3.11.11` |
| `ALLOWED_ORIGINS` | your Vercel URL |

## Optional (cleaner, same result)

If you want to set commands yourself:

- **Build:** `pip install -r requirements.txt`
- **Start:** `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
