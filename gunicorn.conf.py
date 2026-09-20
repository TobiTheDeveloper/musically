import os

bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
worker_class = "uvicorn.workers.UvicornWorker"
workers = 1
timeout = 600
graceful_timeout = 30
keepalive = 5
