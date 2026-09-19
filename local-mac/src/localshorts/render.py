from __future__ import annotations

import subprocess
from pathlib import Path


def _run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-4000:] or "FFmpeg failed")


def render_vertical_clip(
    source: Path,
    output: Path,
    start: float,
    end: float,
    prefer_videotoolbox: bool = True,
) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    duration = max(0.1, end - start)
    video_filter = (
        "scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920"
    )

    encoder = "h264_videotoolbox" if prefer_videotoolbox else "libx264"
    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{start:.3f}",
        "-i", str(source),
        "-t", f"{duration:.3f}",
        "-vf", video_filter,
        "-c:v", encoder,
    ]
    if encoder == "h264_videotoolbox":
        cmd += ["-b:v", "8M", "-allow_sw", "1"]
    else:
        cmd += ["-preset", "fast", "-crf", "20"]
    cmd += ["-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(output)]

    try:
        _run(cmd)
    except RuntimeError:
        if encoder != "h264_videotoolbox":
            raise
        # A Mac/FFmpeg build may expose VideoToolbox differently. Fall back cleanly.
        return render_vertical_clip(source, output, start, end, prefer_videotoolbox=False)

    return output
