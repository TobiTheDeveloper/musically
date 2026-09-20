# Render Setup — READ THIS

Render **does not** auto-update your build/start commands from GitHub.
You must edit them manually in the dashboard **once**.

## Go to: Dashboard → musically → Settings

### 1. Build Command
```
bash build.sh
```
*(Or leave default `pip install -r requirements.txt` — both work now.)*

### 2. Start Command — REQUIRED, replace the gunicorn default
```
cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### 3. Environment Variables
| Key | Value |
|-----|--------|
| `PYTHON_VERSION` | `3.11.11` |
| `ALLOWED_ORIGINS` | `https://your-app.vercel.app` |

### 4. Instance Type
Use **Starter ($7/mo)** minimum. Free tier will crash.

### 5. Save Changes → Manual Deploy → Deploy latest commit
