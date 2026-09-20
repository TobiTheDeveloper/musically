import json
import os
import re
import subprocess
import urllib.request
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

RETRYABLE = (
    "not a bot",
    "sign in",
    "unavailable",
    "error code: 15",
    "error code: 152",
    "watch video on youtube",
    "http error 403",
    "http error 429",
    "requested format is not available",
    "no video formats",
    "please sign in",
)

FATAL = (
    "private video",
    "video has been removed",
    "this video is no longer available",
    "account associated with this video has been terminated",
)

# Default first — forcing android_vr/tv caused error 152 on many beats.
YTDLP_STRATEGIES = [
    {},
    {"extractor_args": {"youtube": {"player_client": ["tv", "web_safari"]}}},
    {"extractor_args": {"youtube": {"player_client": ["ios"]}}},
    {"extractor_args": {"youtube": {"player_client": ["mweb"]}}},
    {"extractor_args": {"youtube": {"player_client": ["android"]}}},
    {"extractor_args": {"youtube": {"player_client": ["web"]}}},
]

INVIDIOUS_INSTANCES = [
    "https://inv.nadeko.net",
    "https://yewtu.be",
    "https://invidious.nerdvpn.de",
    "https://iv.ggtyler.dev",
    "https://invidious.fdn.fr",
]


def is_valid_youtube_url(url: str) -> bool:
    return bool(YOUTUBE_URL_PATTERN.search(url.strip()))


def video_id_from_url(url: str) -> str | None:
    match = VIDEO_ID_PATTERN.search(url.strip())
    return match.group(1) if match else None


def normalize_youtube_url(url: str) -> str:
    video_id = video_id_from_url(url)
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"
    return url.strip()


def _cookies_path() -> str | None:
    path = os.getenv("YOUTUBE_COOKIES_FILE", "").strip()
    if path and Path(path).exists():
        return path
    default = Path(__file__).resolve().parent.parent.parent / "cookies.txt"
    if default.exists():
        return str(default)
    return None


def _is_retryable(exc: Exception) -> bool:
    message = str(exc).lower()
    if any(part in message for part in FATAL):
        return False
    return True


def download_audio(url: str, output_dir: Path, job_id: str) -> tuple[Path, str]:
    """Download audio from YouTube as WAV."""
    ensure_ffmpeg_in_path()
    output_dir.mkdir(parents=True, exist_ok=True)
    video_id = video_id_from_url(url)
    cookies = _cookies_path()
    last_error: Exception | None = None

    source_urls = [normalize_youtube_url(url)]
    if video_id:
        source_urls.extend(f"{base}/watch?v={video_id}" for base in INVIDIOUS_INSTANCES)

    for source in source_urls:
        strategies = YTDLP_STRATEGIES if "youtube.com" in source else [{}]
        for extra in strategies:
            try:
                return _download_with_ytdlp(source, output_dir, job_id, cookies, extra)
            except Exception as exc:
                last_error = exc
                message = str(exc).lower()
                if any(part in message for part in FATAL):
                    raise

    if video_id:
        try:
            return _download_via_invidious_api(video_id, output_dir, job_id)
        except Exception as exc:
            last_error = exc

    raise RuntimeError(
        "Could not download this YouTube beat from the cloud. "
        "Upload an MP3/WAV instead, or run Musically on your computer."
    ) from last_error


def _ydl_base_opts(output_dir: Path, job_id: str, cookies: str | None) -> dict:
    opts = {
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
        "retries": 3,
        "fragment_retries": 3,
    }
    if cookies:
        opts["cookiefile"] = cookies
    return opts


def _download_with_ytdlp(
    url: str,
    output_dir: Path,
    job_id: str,
    cookies: str | None,
    extra_opts: dict,
) -> tuple[Path, str]:
    ydl_opts = _ydl_base_opts(output_dir, job_id, cookies)
    ydl_opts.update(extra_opts)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get("title", "Unknown") if info else "Unknown"
    return _find_output(output_dir, job_id), title


def _find_output(output_dir: Path, job_id: str) -> Path:
    wav = output_dir / f"{job_id}.wav"
    if wav.exists():
        return wav
    candidates = list(output_dir.glob(f"{job_id}.*"))
    wav_files = [f for f in candidates if f.suffix.lower() == ".wav"]
    if wav_files:
        return wav_files[0]
    if candidates:
        return candidates[0]
    raise FileNotFoundError("Download completed but audio file was not found.")


def _http_json(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 Musically/1.0"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _http_download(url: str, dest: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 Musically/1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response, dest.open("wb") as out:
        while True:
            chunk = response.read(1024 * 256)
            if not chunk:
                break
            out.write(chunk)


def _to_wav(src: Path, dest: Path) -> None:
    ffmpeg = ensure_ffmpeg_in_path()
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to convert the beat to WAV.")
    result = subprocess.run(
        [ffmpeg, "-y", "-i", str(src), "-vn", "-acodec", "pcm_s16le", str(dest)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not dest.exists():
        raise RuntimeError(result.stderr[-400:] if result.stderr else "WAV conversion failed.")


def _download_via_invidious_api(video_id: str, output_dir: Path, job_id: str) -> tuple[Path, str]:
    last_error: Exception | None = None
    for base in INVIDIOUS_INSTANCES:
        try:
            data = _http_json(f"{base}/api/v1/videos/{video_id}")
            title = data.get("title") or video_id
            formats = list(data.get("adaptiveFormats") or []) + list(data.get("formatStreams") or [])
            audio = next(
                (
                    item
                    for item in formats
                    if str(item.get("type", "")).startswith("audio/") and item.get("url")
                ),
                None,
            )
            if not audio:
                continue
            raw = output_dir / f"{job_id}.audio"
            wav = output_dir / f"{job_id}.wav"
            _http_download(audio["url"], raw)
            _to_wav(raw, wav)
            raw.unlink(missing_ok=True)
            return wav, title
        except Exception as exc:
            last_error = exc
            continue
    raise RuntimeError("All YouTube frontends failed.") from last_error
