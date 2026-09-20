import asyncio
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.jobs import JobStatus, create_job, create_stems_zip, get_job, run_job
from app.services.downloader import is_valid_youtube_url

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
STATIC_DIR = REPO_ROOT / "static"
BASE_DIR = BACKEND_DIR

app = FastAPI(title="Musically", description="YouTube beat stem extractor for FL Studio")

allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class ProcessRequest(BaseModel):
    url: str


@app.get("/")
async def index():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Musically API is running. Place static files in /static."}


@app.get("/style.css")
async def style_css():
    return FileResponse(STATIC_DIR / "style.css", media_type="text/css")


@app.get("/app.js")
async def app_js():
    return FileResponse(STATIC_DIR / "app.js", media_type="application/javascript")


@app.get("/config.js")
async def config_js():
    return FileResponse(STATIC_DIR / "config.js", media_type="application/javascript")


@app.post("/api/process")
async def process_youtube(request: ProcessRequest):
    url = request.url.strip()
    if not is_valid_youtube_url(url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL.")

    job = create_job(url)
    asyncio.create_task(run_job(job))

    return {"job_id": job.id, "status": job.status.value}


@app.get("/api/jobs/{job_id}")
async def job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job.to_dict()


@app.get("/api/jobs/{job_id}/download/{stem_name}")
async def download_stem(job_id: str, stem_name: str):
    job = get_job(job_id)
    if not job or job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=404, detail="Job not found or not completed.")

    if stem_name not in job.stems:
        raise HTTPException(status_code=404, detail=f"Stem '{stem_name}' not found.")

    file_path = BASE_DIR / job.stems[stem_name]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Stem file missing on disk.")

    safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in job.title)[:60]
    filename = f"{safe_title}_{stem_name}.wav"

    return FileResponse(
        path=file_path,
        media_type="audio/wav",
        filename=filename,
    )


@app.get("/api/jobs/{job_id}/download-all")
async def download_all_stems(job_id: str):
    job = get_job(job_id)
    if not job or job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=404, detail="Job not found or not completed.")

    zip_path = create_stems_zip(job_id)
    if not zip_path or not zip_path.exists():
        raise HTTPException(status_code=500, detail="Could not create ZIP archive.")

    safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in job.title)[:60]
    filename = f"{safe_title}_stems.zip"

    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=filename,
    )
