import os
import re
from pathlib import Path

import yt_dlp

from app.services.ffmpeg_setup import ensure_ffmpeg_in_path

YOUTUBE_URL_PATTERN = re.compile(
    r"(https?://)?(www\.)?"
    r"(youtube\.com/(watch\?v=|embed/|shorts/)|youtu\.be/)"
    r"[\w-]+",
    re.IGNORECASE,
)

VIDEO_ID_PATTERN = re.compile(
    r"(?:v=|/shorts/|/embed/|youtu\.be/)([\w-]{11})",
    re.IGNORECASE,
)

# Clients that usually skip the web "not a bot" check.
PLAYER_CLIENTS = [
    ["android_vr", "tv", "ios"],
    ["tv"],
    ["web_embedded"],
    ["web_safari"],
]


def is_valid_youtube_url(url: str) -> bool:
    return bool(YOUTUBE_URL_PATTERN.search(url.strip()))


def normalize_youtube_url(url: str) -> str:
    match = VIDEO_ID_PATTERN.search(url.strip())
    if match:
        return f"https://www.youtube.com/watch?v={match.group(1)}"
    return url.strip()


def _cookies_path() -> str | None:
    path = os.getenv("YOUTUBE_COOKIES_FILE", "").strip()
    if path and Path(path).exists():
        return path
    default = Path(__file__).resolve().parent.parent.parent / "cookies.txt"
    if default.exists():
        return str(default)
    return None


def download_audio(url: str, output_dir: Path, job_id: str) -> tuple[Path, str]:
    """Download audio from YouTube as WAV for stem separation."""
    ensure_ffmpeg_in_path()
    output_dir.mkdir(parents=True, exist_ok=True)
    url = normalize_youtube_url(url)
    last_error: Exception | None = None
    cookies = _cookies_path()

    for clients in PLAYER_CLIENTS:
        try:
            return _download_with_clients(url, output_dir, job_id, clients, cookies)
        except Exception as exc:
            last_error = exc
            message = str(exc).lower()
            if "not a bot" not in message and "sign in" not in message:
                raise

    raise RuntimeError(
        "YouTube blocked this download from the cloud server (bot check). "
        "Upload an MP3/WAV of the beat instead, or run Musically on your computer."
    ) from last_error


def _download_with_clients(
    url: str,
    output_dir: Path,
    job_id: str,
    clients: list[str],
    cookies: str | None,
) -> tuple[Path, str]:
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
        "nocheckcertificate": True,
        "extractor_args": {
            "youtube": {
                "player_client": clients,
                "player_skip": ["webpage", "configs"],
            }
        },
    }
    if cookies:
        ydl_opts["cookiefile"] = cookies

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get("title", "Unknown") if info else "Unknown"

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
