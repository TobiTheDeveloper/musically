"""Gunicorn entrypoint for Render's default start command.

Render runs `gunicorn your_application.wsgi` unless the dashboard
start command is changed. This module exports the FastAPI app as
`application` so that command works with UvicornWorker.
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.main import app as application  # noqa: E402
