import re
from pathlib import Path

import yt_dlp

from app.services.ffmpeg_setup import ensure_ffmpeg_in_path

YOUTUBE_URL_PATTERN = re.compile(
    r"(https?://)?(www\.)?"
    r"(youtube\.com/(watch\?v=|embed/|shorts/)|youtu\.be/)"
    r"[\w-]+"
)


def is_valid_youtube_url(url: str) -> bool:
    return bool(YOUTUBE_URL_PATTERN.match(url.strip()))


def download_audio(url: str, output_dir: Path, job_id: str) -> tuple[Path, str]:
    """Download audio from YouTube as WAV for stem separation."""
    ensure_ffmpeg_in_path()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{job_id}.wav"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(output_dir / f"{job_id}.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "0",
            }
        ],
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get("title", "Unknown")

    if not output_path.exists():
        candidates = list(output_dir.glob(f"{job_id}.*"))
        wav_files = [f for f in candidates if f.suffix.lower() == ".wav"]
        if wav_files:
            output_path = wav_files[0]
        elif candidates:
            output_path = candidates[0]
        else:
            raise FileNotFoundError("Download completed but audio file was not found.")

    return output_path, title
