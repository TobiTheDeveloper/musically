import asyncio
import os
import shutil
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.jobs import JOBS_DIR, JobStatus, create_job, get_job, run_job
from app.services.downloader import is_valid_youtube_url

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
STATIC_DIR = REPO_ROOT / "static"
BASE_DIR = BACKEND_DIR

app = FastAPI(title="Musically", description="YouTube beat downloader for FL Studio")

raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class ProcessRequest(BaseModel):
    url: str


def _safe_filename(title: str, suffix: str) -> str:
    clean = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)[:60].strip()
    return f"{clean or 'beat'}{suffix}"


@app.get("/")
async def index():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Musically API is running."}


@app.get("/style.css")
async def style_css():
    return FileResponse(STATIC_DIR / "style.css", media_type="text/css")


@app.get("/app.js")
async def app_js():
    return FileResponse(STATIC_DIR / "app.js", media_type="application/javascript")


@app.get("/config.js")
async def config_js():
    return FileResponse(STATIC_DIR / "config.js", media_type="application/javascript")


@app.get("/api/health")
async def health():
    return {"ok": True, "service": "musically-api"}


@app.post("/api/process")
async def process_youtube(request: ProcessRequest):
    url = request.url.strip()
    if not is_valid_youtube_url(url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL.")

    job = create_job(url)
    asyncio.create_task(run_job(job))
    return {"job_id": job.id, "status": job.status.value}


ALLOWED_AUDIO = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac", ".webm"}


@app.post("/api/process-file")
async def process_file(file: UploadFile = File(...)):
    suffix = Path(file.filename or "beat.wav").suffix.lower()
    if suffix not in ALLOWED_AUDIO:
        raise HTTPException(
            status_code=400,
            detail="Upload a WAV, MP3, M4A, FLAC, OGG, AAC, or WEBM file.",
        )

    job = create_job(title=Path(file.filename or "uploaded-beat").stem)
    job_dir = JOBS_DIR / job.id
    job_dir.mkdir(parents=True, exist_ok=True)
    dest = job_dir / f"{job.id}{suffix}"

    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    job.local_file = str(dest)
    asyncio.create_task(run_job(job))
    return {"job_id": job.id, "status": job.status.value}


@app.get("/api/jobs/{job_id}")
async def job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job.to_dict()


@app.get("/api/jobs/{job_id}/download")
async def download_beat(job_id: str):
    job = get_job(job_id)
    if not job or job.status != JobStatus.COMPLETED or not job.file:
        raise HTTPException(status_code=404, detail="Beat not ready.")

    file_path = BASE_DIR / job.file
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Beat file missing on disk.")

    suffix = file_path.suffix.lower() or ".wav"
    media = "audio/wav" if suffix == ".wav" else "application/octet-stream"
    return FileResponse(
        path=file_path,
        media_type=media,
        filename=_safe_filename(job.title, suffix),
    )
