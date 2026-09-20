#!/usr/bin/env bash
set -euo pipefail

echo "==> Installing app dependencies..."
pip install -r requirements.txt
echo "==> Build complete."
