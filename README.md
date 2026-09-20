# Musically — YouTube Beat Stem Extractor

Paste a YouTube beat link and get separated WAV stems (drums, bass, other, vocals) ready to drag into FL Studio.

## What it does

1. Downloads audio from YouTube
2. Runs AI stem separation (Meta Demucs)
3. Gives you individual `.wav` files or a ZIP of all stems

## Requirements

- Python 3.10+
- ~2 GB free disk space (PyTorch + Demucs model on first run)
- GPU optional (CPU works, but separation is slower)

## Setup

```bash
cd musically
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Run

```bash
python run.py
```

Open **http://127.0.0.1:8000** in your browser.

## Using stems in FL Studio

1. Download the stems (individual WAV or ZIP)
2. In FL Studio: **File → Import → Audio file** (or drag WAV files into the Playlist)
3. Each stem loads as its own track — drums, bass, instruments, vocals

WAV is uncompressed and FL Studio's native format, so no conversion needed.

## Stems explained

| Stem | What's in it |
|------|-------------|
| **drums** | Kick, snare, hi-hats, percussion |
| **bass** | Bass line and low-end |
| **other** | Melody, synths, keys, guitars |
| **vocals** | Any vocals or vocal samples |

## Notes

- First run downloads the Demucs model (~80 MB) — one-time setup
- Longer beats take more time to separate (especially on CPU)
- For personal/educational use — respect YouTube terms and copyright

## Deploy online (Vercel + Render)

This app has two parts:

| Part | Host | Why |
|------|------|-----|
| **Frontend** (UI) | [Vercel](https://vercel.com) | Static site — fast and free |
| **Backend** (API + AI) | [Render](https://render.com) | Python + PyTorch + Demucs need a real server |

Vercel cannot run the stem separation backend (PyTorch is ~200 MB, jobs take minutes).

### 1. Push to GitHub

Already done if you cloned from the repo.

### 2. Deploy backend on Render

1. Go to [render.com](https://render.com) → **New → Blueprint**
2. Connect your GitHub repo — Render reads `render.yaml`
3. Use at least the **Starter** plan (free tier is too small for PyTorch)
4. Set env var `ALLOWED_ORIGINS` to your Vercel URL, e.g. `https://musically.vercel.app`
5. Copy your Render URL, e.g. `https://musically-api.onrender.com`

### 3. Deploy frontend on Vercel

1. Go to [vercel.com](https://vercel.com) → **Add New Project**
2. Import the same GitHub repo
3. Vercel auto-detects `vercel.json`
4. Add environment variable:
   - `MUSICALLY_API_URL` = your Render backend URL (no trailing slash)
5. Deploy

Your app will be live at `https://your-project.vercel.app`.
