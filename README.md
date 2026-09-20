# Musically — YouTube Beat Downloader

Paste a YouTube beat link and get a WAV file ready to drag into FL Studio.

## What it does

1. Downloads the audio from YouTube
2. Converts it to `.wav`
3. Lets you download the beat for FL Studio

## Requirements

- Python 3.10+

## Setup

```bash
cd musically
python -m venv venv
venv\Scripts\activate        # Windows
cd backend
pip install -r requirements.txt
```

## Run

```bash
cd backend && python run.py
```

Open **http://127.0.0.1:8000** in your browser.

## Using in FL Studio

1. Download the `.wav`
2. Drag it into the FL Studio Playlist, or use **File → Import → Audio file**

WAV is uncompressed and FL Studio's native format, so no conversion needed.

## Notes

- For personal/educational use — respect YouTube terms and copyright
- YouTube may block downloads from cloud servers; if that happens, upload the audio file instead

## Deploy online (Vercel + Render)

This app has two parts:

| Part | Host | Why |
|------|------|-----|
| **Frontend** (UI) | [Vercel](https://vercel.com) | Static site — fast and free |
| **Backend** (API) | [Render](https://render.com) | Python downloader needs a real server |

Vercel cannot run the YouTube download backend.

### 1. Push to GitHub

Already done if you cloned from the repo.

### 2. Deploy backend on Render

1. Go to [render.com](https://render.com) → **New Web Service**
2. Connect repo **TobiTheDeveloper/musically**, branch **main**
3. Use at least the **Starter ($7/mo)** plan — Free tier is too small for PyTorch
4. Fill in these settings exactly:

| Field | Value |
|-------|--------|
| **Root Directory** | *(leave blank)* |
| **Build Command** | `bash build.sh` |
| **Start Command** | `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

5. Add environment variables:

| Key | Value |
|-----|--------|
| `PYTHON_VERSION` | `3.11.11` |
| `ALLOWED_ORIGINS` | your Vercel URL, e.g. `https://musically.vercel.app` |

6. Deploy and copy your Render URL, e.g. `https://musically-api.onrender.com`

> **Do not use** `pip install -r requirements.txt` or `gunicorn` — those are wrong defaults. Python must be **3.11**, not 3.14.

### 3. Deploy frontend on Vercel

See **[VERCEL_SETUP.md](VERCEL_SETUP.md)**. The two settings that matter:

1. **Application Preset → Other** (not FastAPI)
2. **Root Directory → `static`**

Then set `MUSICALLY_API_URL` to your Render URL and deploy.
