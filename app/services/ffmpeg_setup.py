import os
import shutil
from pathlib import Path


def ensure_ffmpeg_in_path() -> str | None:
    """Ensure ffmpeg is available. Returns the ffmpeg path if found."""
    if shutil.which("ffmpeg"):
        return shutil.which("ffmpeg")

    try:
        import imageio_ffmpeg

        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        ffmpeg_dir = str(Path(ffmpeg_path).parent)
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
        return ffmpeg_path
    except Exception:
        return None
