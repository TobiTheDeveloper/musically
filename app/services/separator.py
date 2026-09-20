import shutil
import subprocess
import sys
from pathlib import Path

from app.services.ffmpeg_setup import ensure_ffmpeg_in_path

STEM_NAMES = ["drums", "bass", "other", "vocals"]


def separate_stems(audio_path: Path, output_dir: Path) -> dict[str, Path]:
    """Separate audio into stems using Demucs (htdemucs model)."""
    ensure_ffmpeg_in_path()
    output_dir.mkdir(parents=True, exist_ok=True)
    demucs_out = output_dir / "demucs_raw"

    cmd = [
        sys.executable,
        "-m",
        "demucs",
        "-n",
        "htdemucs",
        "-o",
        str(demucs_out),
        str(audio_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Stem separation failed: {result.stderr or result.stdout}")

    model_dir = demucs_out / "htdemucs" / audio_path.stem
    if not model_dir.exists():
        found = list(demucs_out.rglob("*.wav"))
        if not found:
            raise FileNotFoundError("Demucs finished but no stem files were produced.")
        model_dir = found[0].parent

    stems: dict[str, Path] = {}
    for stem_name in STEM_NAMES:
        src = model_dir / f"{stem_name}.wav"
        if src.exists():
            dest = output_dir / f"{stem_name}.wav"
            shutil.copy2(src, dest)
            stems[stem_name] = dest

    if demucs_out.exists():
        shutil.rmtree(demucs_out, ignore_errors=True)

    if not stems:
        raise FileNotFoundError("No stems were extracted from the audio.")

    return stems
