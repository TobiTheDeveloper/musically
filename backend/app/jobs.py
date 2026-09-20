import asyncio
import shutil
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from app.services.downloader import download_audio

BASE_DIR = Path(__file__).resolve().parent.parent
JOBS_DIR = BASE_DIR / "jobs"
JOBS_DIR.mkdir(exist_ok=True)


class JobStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
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
    file: str = ""
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
            "file": self.file,
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
            job.progress = 40
            job.message = "Preparing uploaded beat..."
            audio_path = Path(job.local_file)
            if not job.title:
                job.title = audio_path.stem
        else:
            job.status = JobStatus.DOWNLOADING
            job.progress = 15
            job.message = "Downloading beat from YouTube..."
            audio_path, title = await loop.run_in_executor(
                None, download_audio, job.url, job_dir, job.id
            )
            job.title = title

        job.file = str(audio_path.relative_to(BASE_DIR))
        job.status = JobStatus.COMPLETED
        job.progress = 100
        job.message = "Done! Download the WAV and drop it into FL Studio."

    except Exception as exc:
        job.status = JobStatus.FAILED
        job.error = str(exc)
        job.message = f"Failed: {exc}"
        shutil.rmtree(job_dir, ignore_errors=True)
