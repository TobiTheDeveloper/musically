#!/usr/bin/env bash
set -euo pipefail

echo "==> Installing CPU-only PyTorch..."
pip install torch==2.5.1 torchaudio==2.5.1 \
  --index-url https://download.pytorch.org/whl/cpu

echo "==> Installing app dependencies..."
pip install -r requirements.txt

echo "==> Installing Demucs (torch already satisfied)..."
pip install demucs==4.0.1

echo "==> Build complete."
