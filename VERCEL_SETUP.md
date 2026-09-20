# Vercel Setup (frontend only)

Vercel **cannot** run this as FastAPI. The Python/AI backend lives on Render.
Vercel only hosts the website UI.

## Create the project

On **New Project**, change these two fields:

| Field | Must be |
|-------|---------|
| **Application Preset** | **Other** — not FastAPI |
| **Root Directory** | Click **Edit** → choose **`static`** |

Keep:

| Field | Value |
|-------|--------|
| Project Name | `musically` |
| `MUSICALLY_API_URL` | your Render URL, e.g. `https://musically-xxxx.onrender.com` (no trailing slash) |

Then click Deploy.

## If you already imported it as FastAPI

1. Cancel / delete that failed project, **or**
2. Open **Project Settings → General**
   - Framework Preset → **Other**
   - Root Directory → **`static`**
3. Redeploy

If the preset stays FastAPI, Vercel will run `uv pip install` and the deploy will fail.
