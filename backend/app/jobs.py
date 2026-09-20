import asyncio
import shutil
import uuid
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from app.services.downloader import download_audio, is_valid_youtube_url
from app.services.separator import separate_stems

BASE_DIR = Path(__file__).resolve().parent.parent
JOBS_DIR = BASE_DIR / "jobs"
JOBS_DIR.mkdir(exist_ok=True)


class JobStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    SEPARATING = "separating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Job:
    id: str
    url: str = ""
    local_file: str = ""
    status: JobStatus = JobStatus.PENDING
    progress: int = 0
    message: str = "Queued..."
    title: str = ""
    stems: dict[str, str] = field(default_factory=dict)
    error: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "url": self.url,
            "status": self.status.value,
            "progress": self.progress,
            "message": self.message,
            "title": self.title,
            "stems": self.stems,
            "error": self.error,
            "created_at": self.created_at,
        }


_jobs: dict[str, Job] = {}


def get_job(job_id: str) -> Job | None:
    return _jobs.get(job_id)


def create_job(url: str = "", local_file: str = "", title: str = "") -> Job:
    job_id = uuid.uuid4().hex[:12]
    job = Job(id=job_id, url=url, local_file=local_file, title=title)
    _jobs[job_id] = job
    return job


async def run_job(job: Job) -> None:
    job_dir = JOBS_DIR / job.id
    job_dir.mkdir(parents=True, exist_ok=True)

    try:
        loop = asyncio.get_event_loop()

        if job.local_file:
            job.status = JobStatus.DOWNLOADING
            job.progress = 20
            job.message = "Using uploaded audio..."
            audio_path = Path(job.local_file)
            if not job.title:
                job.title = audio_path.stem
        else:
            job.status = JobStatus.DOWNLOADING
            job.progress = 10
            job.message = "Downloading audio from YouTube..."
            audio_path, title = await loop.run_in_executor(
                None, download_audio, job.url, job_dir, job.id
            )
            job.title = title

        job.progress = 40
        job.message = f"Ready: {job.title}"

        job.status = JobStatus.SEPARATING
        job.progress = 50
        job.message = "Separating stems (drums, bass, other, vocals)... This may take a few minutes."

        stems_dir = job_dir / "stems"
        stems = await loop.run_in_executor(None, separate_stems, audio_path, stems_dir)

        job.stems = {name: str(path.relative_to(BASE_DIR)) for name, path in stems.items()}
        job.status = JobStatus.COMPLETED
        job.progress = 100
        job.message = "Done! Download your stems below."

    except Exception as exc:
        job.status = JobStatus.FAILED
        job.error = str(exc)
        job.message = f"Failed: {exc}"
        shutil.rmtree(job_dir, ignore_errors=True)


def create_stems_zip(job_id: str) -> Path | None:
    job = get_job(job_id)
    if not job or job.status != JobStatus.COMPLETED:
        return None

    job_dir = JOBS_DIR / job_id / "stems"
    zip_path = JOBS_DIR / job_id / f"{job_id}_stems.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for stem_file in sorted(job_dir.glob("*.wav")):
            zf.write(stem_file, arcname=stem_file.name)

    return zip_path
